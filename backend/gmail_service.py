"""
gmail_service.py — Gmail API integration using OAuth 2.0.

Handles authentication via credentials.json / token.json.
Supports:
  - Fetching inbox emails (with thread_id capture)
  - Sending new emails
  - Replying within an existing thread
  - Forwarding emails with quoted body
  - Modifying email labels (star, archive, delete, restore)

SCOPES:
  - gmail.modify  — read + label write (superset of readonly)
  - gmail.send    — outbound message sending

⚠️  SCOPE CHANGE: If token.json exists from a previous run, delete it
    and re-run the OAuth flow once to grant the new scopes.
"""

import base64
import logging
import os
from email.mime.text import MIMEText
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from config import settings

logger = logging.getLogger(__name__)

# ── OAuth Scopes ──────────────────────────────────────────────────────────────
# gmail.modify  → superset of gmail.readonly; also allows label writes
#                 (star, archive, move to trash) via users.messages.modify
# gmail.send    → required to send / reply to emails
#
# ⚠️  Scope change: delete token.json and re-run OAuth flow once.
SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.send",
]


class GmailService:
    """
    Wrapper around the Gmail API.

    Handles OAuth token refresh, email listing, parsing, and sending.
    """

    def __init__(self):
        self._service = self._authenticate()

    # ── Authentication ────────────────────────────────────────────────────

    def _authenticate(self):
        """
        Authenticate with Gmail using OAuth 2.0.

        - Loads existing token from token.json if available.
        - Refreshes token automatically when expired.
        - Initiates browser-based OAuth flow on first run or scope change.

        Returns:
            Google API service object for Gmail.

        Raises:
            FileNotFoundError: If credentials.json is missing.
            Exception: On authentication failure.
        """
        creds = None

        if not os.path.exists(settings.GMAIL_CREDENTIALS_PATH):
            raise FileNotFoundError(
                f"credentials.json not found at '{settings.GMAIL_CREDENTIALS_PATH}'. "
                "Download it from Google Cloud Console > APIs & Services > Credentials."
            )

        # Load saved token
        if os.path.exists(settings.GMAIL_TOKEN_PATH):
            try:
                creds = Credentials.from_authorized_user_file(
                    settings.GMAIL_TOKEN_PATH, SCOPES
                )
                logger.info("Loaded existing Gmail token.")
            except Exception as e:
                logger.warning(f"Could not load token.json: {e}. Re-authenticating.")

        # Refresh or re-authenticate
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                logger.info("Refreshing expired Gmail token...")
                creds.refresh(Request())
            else:
                logger.info("Starting Gmail OAuth flow (browser will open)...")
                flow = InstalledAppFlow.from_client_secrets_file(
                    settings.GMAIL_CREDENTIALS_PATH, SCOPES
                )
                creds = flow.run_local_server(port=0)

            # Persist the new / refreshed token
            with open(settings.GMAIL_TOKEN_PATH, "w") as token_file:
                token_file.write(creds.to_json())
            logger.info(f"Token saved to '{settings.GMAIL_TOKEN_PATH}'.")

        return build("gmail", "v1", credentials=creds)

    # ── Email Fetching ────────────────────────────────────────────────────

    def fetch_emails(self, limit: int = 10) -> list[dict[str, Any]]:
        """
        Fetch the latest `limit` emails from the Gmail inbox.

        Args:
            limit: Maximum number of emails to retrieve.

        Returns:
            List of dicts with keys: id, thread_id, sender, subject, body.

        Raises:
            HttpError: On Gmail API failure.
        """
        try:
            logger.info(f"Fetching up to {limit} emails from Gmail...")
            result = (
                self._service.users()
                .messages()
                .list(userId="me", maxResults=limit, labelIds=["INBOX"])
                .execute()
            )
        except HttpError as e:
            logger.error(f"Gmail API list error: {e}")
            raise

        messages = result.get("messages", [])
        if not messages:
            logger.info("Inbox is empty or no messages returned.")
            return []

        emails = []
        for msg_ref in messages:
            try:
                email_data = self._fetch_single_email(msg_ref["id"])
                if email_data:
                    emails.append(email_data)
            except Exception as e:
                logger.warning(f"Skipping message {msg_ref['id']}: {e}")

        logger.info(f"Successfully fetched {len(emails)} emails.")
        return emails

    def _fetch_single_email(self, message_id: str) -> dict[str, Any] | None:
        """
        Retrieve and parse a single Gmail message.

        Args:
            message_id: The Gmail message ID.

        Returns:
            Dict with id, thread_id, sender, subject, body; or None on failure.
        """
        try:
            msg = (
                self._service.users()
                .messages()
                .get(userId="me", id=message_id, format="full")
                .execute()
            )
        except HttpError as e:
            logger.error(f"Failed to fetch message {message_id}: {e}")
            return None

        headers = {
            h["name"].lower(): h["value"]
            for h in msg.get("payload", {}).get("headers", [])
        }

        sender    = headers.get("from", "Unknown Sender")
        subject   = headers.get("subject", "(No Subject)")
        thread_id = msg.get("threadId", "")       # Required for threaded replies
        date      = headers.get("date", "")
        body      = self._extract_body(msg)

        return {
            "id":        message_id,
            "thread_id": thread_id,
            "sender":    sender,
            "subject":   subject,
            "date":      date,
            "body":      body or msg.get("snippet", ""),
        }

    @staticmethod
    def _extract_body(msg: dict) -> str:
        """
        Recursively extract plain-text body from a Gmail message payload.

        Tries text/plain first; falls back to text/html snippet.

        Args:
            msg: Full Gmail message dict.

        Returns:
            Decoded body string, or empty string if not found.
        """
        payload = msg.get("payload", {})

        def decode_part(part: dict) -> str:
            data = part.get("body", {}).get("data", "")
            if data:
                try:
                    return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
                except Exception:
                    return ""
            return ""

        # Single-part message
        if payload.get("mimeType") == "text/plain":
            return decode_part(payload)

        # Multi-part: prefer text/plain
        parts = payload.get("parts", [])
        for part in parts:
            if part.get("mimeType") == "text/plain":
                text = decode_part(part)
                if text:
                    return text

        # Second pass: any text type
        for part in parts:
            mime = part.get("mimeType", "")
            if mime.startswith("text/"):
                text = decode_part(part)
                if text:
                    return text

        # Last resort: use snippet
        return msg.get("snippet", "")

    # ── Single Message Details ─────────────────────────────────────────────

    def get_message_details(self, message_id: str) -> dict[str, Any] | None:
        """
        Fetch the full details of a single Gmail message by its ID.

        Returns a dict with: id, thread_id, sender, subject, date, body.
        Returns None if the message cannot be retrieved.
        """
        return self._fetch_single_email(message_id)

    # ── Email Sending ─────────────────────────────────────────────────────

    def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        thread_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Send an email (or a threaded reply) via the Gmail API.

        Args:
            to:        Recipient email address.
            subject:   Email subject line.
            body:      Plain-text message body.
            thread_id: Optional Gmail thread ID to reply within a thread.
                       Pass None to start a new conversation.

        Returns:
            Gmail API response dict (contains 'id' and 'threadId').

        Raises:
            HttpError: On Gmail API failure.
            RuntimeError: On unexpected errors.
        """
        # Build the MIME message
        mime_message = MIMEText(body, "plain")
        mime_message["to"] = to
        mime_message["subject"] = subject

        # Encode to base64url (required by Gmail API)
        raw_message = base64.urlsafe_b64encode(
            mime_message.as_bytes()
        ).decode("utf-8")

        message_body: dict[str, Any] = {"raw": raw_message}

        # Threading: set threadId to keep reply in the same thread
        if thread_id:
            message_body["threadId"] = thread_id

        try:
            sent = (
                self._service.users()
                .messages()
                .send(userId="me", body=message_body)
                .execute()
            )
            logger.info(
                f"Email sent to '{to}' (message_id={sent.get('id')} "
                f"thread={sent.get('threadId')})"
            )
            return sent
        except HttpError as e:
            logger.error(f"Gmail send failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error sending email: {e}")
            raise RuntimeError(f"Email send error: {e}") from e

    # ── Email Forwarding ──────────────────────────────────────────────────

    def forward_email(
        self,
        message_id: str,
        to: str,
        note: str = "",
    ) -> dict[str, Any]:
        """
        Forward an existing Gmail message to a new recipient.

        Fetches the original message, prepends an optional personal note,
        and appends a standard forwarded-message block (RFC 2822 style).

        Args:
            message_id: Original Gmail message ID to forward.
            to:         Recipient email address.
            note:       Optional text to prepend above the forwarded body.

        Returns:
            Gmail API response dict (contains 'id' and 'threadId').

        Raises:
            ValueError:  If the original message cannot be fetched.
            HttpError:   On Gmail API failure.
        """
        original = self._fetch_single_email(message_id)
        if not original:
            raise ValueError(
                f"Cannot forward: message '{message_id}' could not be retrieved."
            )

        subject  = original.get("subject", "(No Subject)")
        sender   = original.get("sender",  "Unknown Sender")
        body     = original.get("body",    "")

        # Remove any existing 'Fwd:' prefix before re-adding it
        clean_subject = subject.lstrip()
        if not clean_subject.lower().startswith("fwd:"):
            forward_subject = f"Fwd: {clean_subject}"
        else:
            forward_subject = clean_subject

        # Build the forwarded body
        divider = "-" * 60
        forwarded_block = (
            f"\n\n{divider}\n"
            f"---------- Forwarded message ----------\n"
            f"From: {sender}\n"
            f"Subject: {subject}\n"
            f"{divider}\n\n"
            f"{body}"
        )
        full_body = (f"{note.strip()}\n" if note.strip() else "") + forwarded_block

        # Send as a new thread (not threaded with the original)
        return self.send_email(to=to, subject=forward_subject, body=full_body)

    # ── Label / Modify Operations ─────────────────────────────────────────

    def modify_email(
        self,
        message_id: str,
        action: str,
    ) -> dict[str, Any]:
        """
        Apply a label-based action to a Gmail message.

        Supported actions:
            star      → addLabelIds=["STARRED"]
            unstar    → removeLabelIds=["STARRED"]
            archive   → removeLabelIds=["INBOX"]
            unarchive → addLabelIds=["INBOX"]
            delete    → addLabelIds=["TRASH"], removeLabelIds=["INBOX"]
            restore   → removeLabelIds=["TRASH"], addLabelIds=["INBOX"]
            mark_read → removeLabelIds=["UNREAD"]
            mark_unread → addLabelIds=["UNREAD"]

        Args:
            message_id: Gmail message ID.
            action:     One of the action strings listed above.

        Returns:
            Gmail API modify response dict.

        Raises:
            ValueError:  If action is not recognised.
            HttpError:   On Gmail API failure.
        """
        action_map: dict[str, dict[str, list[str]]] = {
            "star":        {"addLabelIds": ["STARRED"],          "removeLabelIds": []},
            "unstar":      {"addLabelIds": [],                    "removeLabelIds": ["STARRED"]},
            "archive":     {"addLabelIds": [],                    "removeLabelIds": ["INBOX"]},
            "unarchive":   {"addLabelIds": ["INBOX"],            "removeLabelIds": []},
            "delete":      {"addLabelIds": ["TRASH"],            "removeLabelIds": ["INBOX"]},
            "restore":     {"addLabelIds": ["INBOX"],            "removeLabelIds": ["TRASH"]},
            "mark_read":   {"addLabelIds": [],                    "removeLabelIds": ["UNREAD"]},
            "mark_unread": {"addLabelIds": ["UNREAD"],           "removeLabelIds": []},
        }

        if action not in action_map:
            raise ValueError(
                f"Unknown action '{action}'. "
                f"Valid actions: {', '.join(action_map.keys())}"
            )

        body = action_map[action]
        try:
            result = (
                self._service.users()
                .messages()
                .modify(userId="me", id=message_id, body=body)
                .execute()
            )
            logger.info(
                f"Email '{message_id}' modified with action '{action}' "
                f"(add={body['addLabelIds']} remove={body['removeLabelIds']})"
            )
            return result
        except HttpError as e:
            logger.error(f"Gmail modify failed for '{message_id}' action '{action}': {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error modifying email: {e}")
            raise RuntimeError(f"Email modify error: {e}") from e
