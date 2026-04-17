"""
services/calendar_service.py — Google Calendar API integration.

Uses a separate OAuth token file (calendar_token.json) so that adding
the Calendar scope does not invalidate the existing Gmail token.

Supports:
  - Creating Google Calendar events from structured data
  - AI-assisted event extraction from raw email body (via Gemini)

Scope: https://www.googleapis.com/auth/calendar.events
"""

import json
import logging
import os
import re
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from config import settings
from services.gemini_service import generate_response

logger = logging.getLogger(__name__)

# ── Calendar-specific OAuth scope ─────────────────────────────────────────────
# Using a dedicated scope + token file keeps it independent from Gmail tokens.
CALENDAR_SCOPES = ["https://www.googleapis.com/auth/calendar.events"]


class CalendarService:
    """
    Wrapper around the Google Calendar API.

    Handles OAuth 2.0 authentication with its own token file and provides
    event creation from structured inputs or AI-extracted email details.
    """

    def __init__(self):
        self._service = self._authenticate()

    # ── Authentication ────────────────────────────────────────────────────

    def _authenticate(self):
        """
        Authenticate with Google Calendar using OAuth 2.0.

        Priority:
          1. CALENDAR_TOKEN_JSON env var  → production / Cloud Run / Render
          2. calendar_token.json file     → local development only

        Browser-based OAuth (run_local_server) is intentionally DISABLED.
        Pre-generate calendar_token.json locally and set CALENDAR_TOKEN_JSON in production.

        Returns:
            Google API service object for Calendar v3.

        Raises:
            RuntimeError: If no valid token is available.
        """
        creds = None

        # ── 1. ENV-VAR based loading — Production (Cloud Run / Render / Docker) ──
        calendar_token_json = os.getenv("CALENDAR_TOKEN_JSON")

        if calendar_token_json:
            try:
                token_data = json.loads(calendar_token_json)
                creds = Credentials.from_authorized_user_info(token_data, CALENDAR_SCOPES)
                logger.info("[Auth] Using Calendar token from CALENDAR_TOKEN_JSON environment variable.")
            except Exception as e:
                logger.error(f"[Auth] Failed to parse CALENDAR_TOKEN_JSON: {e}")
                raise RuntimeError(f"Invalid CALENDAR_TOKEN_JSON env var: {e}") from e

        # ── 2. FILE-BASED fallback — Local development only ───────────────────────
        if not creds:
            if os.path.exists(settings.CALENDAR_TOKEN_PATH):
                try:
                    creds = Credentials.from_authorized_user_file(
                        settings.CALENDAR_TOKEN_PATH, CALENDAR_SCOPES
                    )
                    logger.info("[Auth] Using Calendar token from calendar_token.json file (local dev).")
                except Exception as e:
                    logger.warning(f"[Auth] Could not load calendar_token.json: {e}.")

        # ── 3. No token available — raise immediately, do NOT open browser ────────
        if not creds:
            raise RuntimeError(
                "No Calendar credentials available. "
                "Set CALENDAR_TOKEN_JSON env var in production, "
                "or ensure calendar_token.json exists for local development. "
                "Browser-based OAuth is disabled in this deployment."
            )

        # ── 4. Refresh if expired ─────────────────────────────────────────────────
        if not creds.valid:
            if creds.expired and creds.refresh_token:
                logger.info("[Auth] Refreshing expired Calendar token...")
                creds.refresh(Request())
                logger.info("[Auth] Calendar token refreshed successfully.")

                # Persist refreshed token to file in local dev only
                if not calendar_token_json:
                    try:
                        with open(settings.CALENDAR_TOKEN_PATH, "w") as f:
                            f.write(creds.to_json())
                        logger.info(f"[Auth] Refreshed calendar token saved to '{settings.CALENDAR_TOKEN_PATH}'.")
                    except OSError as e:
                        logger.warning(f"[Auth] Could not persist refreshed calendar token (read-only FS?): {e}")
            else:
                raise RuntimeError(
                    "Calendar token is invalid and cannot be refreshed. "
                    "Re-generate calendar_token.json locally and update CALENDAR_TOKEN_JSON env var."
                )

        # ── OAuth browser flow is intentionally removed for production safety ──────
        # flow = InstalledAppFlow.from_client_secrets_file(settings.GMAIL_CREDENTIALS_PATH, CALENDAR_SCOPES)
        # creds = flow.run_local_server(port=0)

        return build("calendar", "v3", credentials=creds)

    # ── Event Creation ────────────────────────────────────────────────────

    def create_event(
        self,
        title: str,
        start_datetime: str,
        end_datetime: str,
        description: str = "",
        location: str = "",
        attendees: list[str] | None = None,
        timezone: str = "UTC",
    ) -> dict[str, Any]:
        """
        Create a Google Calendar event.

        Args:
            title:          Event title / summary.
            start_datetime: ISO 8601 datetime string (e.g. "2024-04-20T10:00:00").
            end_datetime:   ISO 8601 datetime string for the event end.
            description:    Optional event description / agenda.
            location:       Optional event location (room, URL, etc.).
            attendees:      Optional list of attendee email addresses.
                            Calendar will send invitations automatically.
            timezone:       IANA timezone string (e.g. "Asia/Kolkata"). Default UTC.

        Returns:
            Google Calendar API event resource dict.
            Important keys: id, htmlLink, summary, start, end, status.

        Raises:
            HttpError:   On Calendar API failure.
            RuntimeError: On unexpected errors.
        """
        event_body: dict[str, Any] = {
            "summary":     title,
            "description": description,
            "location":    location,
            "start": {
                "dateTime": start_datetime,
                "timeZone": timezone,
            },
            "end": {
                "dateTime": end_datetime,
                "timeZone": timezone,
            },
        }

        if attendees:
            event_body["attendees"] = [{"email": addr} for addr in attendees]

        try:
            event = (
                self._service.events()
                .insert(
                    calendarId="primary",
                    body=event_body,
                    sendUpdates="all",  # Sends invite emails to attendees
                )
                .execute()
            )
            logger.info(
                f"Calendar event created: '{title}' "
                f"(id={event.get('id')}, link={event.get('htmlLink')})"
            )
            return event
        except HttpError as e:
            logger.error(f"Calendar API error creating event '{title}': {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating calendar event: {e}")
            raise RuntimeError(f"Calendar event error: {e}") from e


# ── AI-Assisted Event Extraction ──────────────────────────────────────────────

def extract_event_details_from_email(email_body: str) -> dict[str, Any]:
    """
    Use Gemini to extract structured event details from a raw email body.

    Attempts to parse the LLM's JSON response. Falls back to an empty
    structure if parsing fails so the caller can still use manual fields.

    Args:
        email_body: Raw plain-text email content.

    Returns:
        Dict with keys: title, start_datetime, end_datetime, location,
                        description, attendees (list[str]).
        Fields default to empty string / empty list if not found.

    Raises:
        RuntimeError: If Gemini API fails.
    """
    prompt = f"""\
You are an AI assistant that extracts calendar event details from emails.

EMAIL:
{email_body}

Extract any meeting/event details from the email above and return a JSON object
with EXACTLY this structure (use empty string "" for missing fields):

{{
  "title":          "<event title or meeting topic>",
  "start_datetime": "<ISO 8601 datetime, e.g. 2024-04-20T10:00:00 or empty string>",
  "end_datetime":   "<ISO 8601 datetime or empty string>",
  "location":       "<room, address, or meeting URL or empty string>",
  "description":    "<brief agenda or context>",
  "attendees":      ["<email1>", "<email2>"]
}}

Return ONLY the JSON object. Do NOT include any explanation or markdown code fences."""

    raw = generate_response(prompt)

    # Strip markdown code fences if the model included them
    cleaned = re.sub(r"```(?:json)?", "", raw, flags=re.IGNORECASE).strip().rstrip("```").strip()

    try:
        data = json.loads(cleaned)
        return {
            "title":          data.get("title", ""),
            "start_datetime": data.get("start_datetime", ""),
            "end_datetime":   data.get("end_datetime", ""),
            "location":       data.get("location", ""),
            "description":    data.get("description", ""),
            "attendees":      data.get("attendees", []),
        }
    except (json.JSONDecodeError, ValueError) as e:
        logger.warning(f"Could not parse event extraction JSON: {e}. Raw: {cleaned[:200]}")
        return {
            "title": "", "start_datetime": "", "end_datetime": "",
            "location": "", "description": "", "attendees": [],
        }
