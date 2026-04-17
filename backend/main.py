"""
AI-Powered Email Intelligence System
Main FastAPI Application Entry Point

Exposes endpoints to:
  - Process Gmail emails through CrewAI agents (intent-based classification)
  - Retrieve stored, classified emails with action labels
  - Send / reply to emails directly from the dashboard (POST /reply-email)
  - Forward emails to new recipients               (POST /forward-email)
  - Send brand-new emails                          (POST /send-email)
  - Modify email labels (star/archive/delete)      (POST /modify-email)
  - Create Google Calendar events from email data  (POST /create-event)
  - Generate AI reply suggestions                  (POST /generate-reply)
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import Optional, List
import logging
import time

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from agents.crew import EmailIntelligenceCrew
from gmail_service import GmailService
from services.database import init_db, insert_email, get_emails, get_db
from services.reply_service import generate_reply
from services.calendar_service import CalendarService, extract_event_details_from_email
from config import settings

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

# ─── Logging Setup ─────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


# ─── Pydantic Request / Response Models ───────────────────────────────────────

class ReplyRequest(BaseModel):
    """Request body for POST /reply-email."""
    to: str = Field(..., description="Recipient email address")
    subject: str = Field(..., description="Email subject line")
    body: str = Field(..., description="Plain-text message body")
    thread_id: Optional[str] = Field(
        default=None,
        description="Gmail thread ID to reply within an existing thread. "
                    "Omit to start a new conversation."
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "to": "colleague@example.com",
                "subject": "Re: Project Update",
                "body": "Thanks for the update! I'll review and get back to you by EOD.",
                "thread_id": "18f3a2b9c4d5e6f7"
            }
        }
    }


class SendEmailRequest(BaseModel):
    """Request body for POST /send-email (new outbound emails, no thread context)."""
    to: str = Field(..., description="Recipient email address")
    subject: str = Field(..., description="Email subject line")
    body: str = Field(..., description="Plain-text message body")

    model_config = {
        "json_schema_extra": {
            "example": {
                "to": "client@example.com",
                "subject": "Following up on our meeting",
                "body": "Hi, I wanted to follow up on the discussion from yesterday..."
            }
        }
    }


class ForwardEmailRequest(BaseModel):
    """Request body for POST /forward-email."""
    message_id: str = Field(
        ...,
        description="Gmail message ID of the email to forward "
                    "(returned as gmail_message_id in GET /emails)"
    )
    to: str = Field(..., description="Recipient email address to forward to")
    note: Optional[str] = Field(
        default="",
        description="Optional personal note to prepend above the forwarded content"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "message_id": "18f3a2b9c4d5e6f7",
                "to": "manager@example.com",
                "note": "FYI — please review the request below."
            }
        }
    }


class ModifyEmailRequest(BaseModel):
    """Request body for POST /modify-email."""
    message_id: str = Field(
        ...,
        description="Gmail message ID to act on "
                    "(returned as gmail_message_id in GET /emails)"
    )
    action: str = Field(
        ...,
        description=(
            "Label action to apply. One of: "
            "star | unstar | archive | unarchive | delete | restore | "
            "mark_read | mark_unread"
        )
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "message_id": "18f3a2b9c4d5e6f7",
                "action": "star"
            }
        }
    }


class CreateEventRequest(BaseModel):
    """Request body for POST /create-event."""
    # Manual fields — used when the caller supplies structured data directly
    title: Optional[str] = Field(default=None, description="Event title / meeting topic")
    start_datetime: Optional[str] = Field(
        default=None,
        description="Start date-time in ISO 8601 format: 2024-04-20T10:00:00"
    )
    end_datetime: Optional[str] = Field(
        default=None,
        description="End date-time in ISO 8601 format: 2024-04-20T11:00:00"
    )
    description: Optional[str] = Field(default="", description="Event description / agenda")
    location: Optional[str] = Field(default="", description="Room, address, or meeting URL")
    attendees: Optional[List[str]] = Field(
        default=None,
        description="List of attendee email addresses (Calendar invites will be sent)"
    )
    timezone: Optional[str] = Field(
        default="UTC",
        description="IANA timezone (e.g. Asia/Kolkata, America/New_York)"
    )
    # AI extraction — when supplied, Ollama parses meeting details from the email body
    email_body: Optional[str] = Field(
        default=None,
        description=(
            "Raw email body to extract event details from using AI. "
            "Any manually supplied fields will override AI-extracted values."
        )
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "email_body": "Hi team, let's do a sync on Monday April 20th at 10am IST to review Q2 milestones.",
                "location": "Google Meet",
                "attendees": ["alice@example.com", "bob@example.com"],
                "timezone": "Asia/Kolkata"
            }
        }
    }


class GenerateReplyRequest(BaseModel):
    """Request body for POST /generate-reply."""
    email_body: str = Field(..., description="The original email text to reply to")
    category: str = Field(
        default="References",
        description="Intent-based category of the email. One of: "
                    "Meetings | Events | Tasks | Follow-ups | "
                    "Reports | References | Finance | Promotions"
    )
    variations: int = Field(
        default=2,
        ge=1, le=3,
        description="Number of reply variations to generate (1–3)"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "email_body": "Hi, can we schedule a call this week to discuss the project milestones?",
                "category": "Meetings",
                "variations": 2
            }
        }
    }


# ─── Lifespan ──────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize resources on startup and clean up on shutdown."""
    logger.info("Initializing PostgreSQL database...")
    init_db()
    logger.info("Database ready.")
    yield
    logger.info("Shutting down AI Email Intelligence System.")


# ─── App Initialization ────────────────────────────────────────────────────────
app = FastAPI(
    title="AI Email Intelligence System",
    description=(
        "Agentic AI backend for Gmail processing using CrewAI + Gemini API.\n\n"
        "Features intent-based email classification (Meetings, Events, Tasks, "
        "Follow-ups, Reports, References, Finance, Promotions, Other) and full dashboard "
        "action support: Reply, Send, Forward, Star, Archive, Delete, Calendar.\n\n"
        "**Scopes required:** `gmail.modify`, `gmail.send`, `calendar.events`"
    ),
    version="3.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict to your frontend origin in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Helper: Gmail client with standard error handling ─────────────────────────

def _get_gmail() -> GmailService:
    """Instantiate GmailService and raise appropriate HTTP errors on failure."""
    try:
        return GmailService()
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Gmail authentication failed: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Gmail authentication error: {str(e)}"
        )


# ─── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/", summary="Health Check", tags=["System"])
def root():
    """Root health check endpoint."""
    return {
        "status": "running",
        "service": "AI Email Intelligence System",
        "version": "3.0.0",
    }


@app.get(
    "/process-emails",
    summary="Fetch, Analyze, and Store Emails",
    tags=["Email Processing"],
)
def process_emails(db: Session = Depends(get_db)):
    """
    Full pipeline:
    1. Fetch latest emails from Gmail API
    2. Run each email through the CrewAI agent pipeline
       (Reader → Analyzer → Structurer)
    3. Classify into intent-based category + derive action label
    4. Persist structured output to PostgreSQL (including gmail_message_id)
    5. Return summary of processed emails
    """
    logger.info("Fetching emails from Gmail...")
    try:
        gmail = _get_gmail()
        raw_emails = gmail.fetch_emails(limit=settings.EMAIL_FETCH_LIMIT)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Gmail fetch failed: {e}")
        raise HTTPException(status_code=503, detail=f"Gmail API error: {str(e)}")

    if not raw_emails:
        logger.warning("No emails returned from Gmail.")
        return {"message": "No emails found to process.", "processed": 0}

    crew = EmailIntelligenceCrew()
    processed_count = 0
    errors = []

    for raw_email in raw_emails:
        try:
            logger.info(f"Processing email: {raw_email.get('subject', 'No Subject')}")
            structured = crew.run(raw_email)
            # Carry Gmail IDs into the structured result for DB storage
            structured.setdefault("id",        raw_email.get("id"))
            structured.setdefault("thread_id", raw_email.get("thread_id"))
            structured.setdefault("received_at", raw_email.get("date"))
            insert_email(db, structured)
            processed_count += 1
        except Exception as e:
            logger.error(f"Failed to process email '{raw_email.get('subject')}': {e}")
            errors.append({
                "subject": raw_email.get("subject", "Unknown"),
                "error": str(e),
            })
        
        # Rate limit to avoid Gemini API quota errors
        time.sleep(10)

    response = {
        "message": "Email processing complete.",
        "processed": processed_count,
        "total_fetched": len(raw_emails),
    }
    if errors:
        response["errors"] = errors

    return response


@app.get(
    "/emails",
    summary="Retrieve All Processed Emails",
    tags=["Email Processing"],
)
def list_emails(db: Session = Depends(get_db)):
    """
    Returns all processed emails from PostgreSQL as a structured JSON list.

    Each record includes:
      gmail_message_id, gmail_thread_id, sender, subject,
      summary, category, priority, action
    """
    try:
        emails = get_emails(db)
    except Exception as e:
        logger.error(f"Database read failed: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    return {
        "total": len(emails),
        "emails": emails,
    }


@app.get(
    "/dashboard-stats",
    summary="Retrieve Dashboard Statistics and AI Insights",
    tags=["Dashboard"],
)
def get_dashboard_stats(db: Session = Depends(get_db)):
    """
    Computes summary metrics for the dashboard from the database.
    """
    from services.models import Email
    try:
        total_emails = db.query(Email).count()
        high_priority = db.query(Email).filter(Email.priority.ilike("High")).count()
        meetings = db.query(Email).filter(Email.category.ilike("Meetings")).count()
        # Mocking unread emails count using "Needs Reply" action label
        unread_emails = db.query(Email).filter(Email.action.ilike("Needs Reply")).count()

        insights = []
        if high_priority > 0:
            insights.append({
                "type": "urgent",
                "title": f"{high_priority} urgent emails",
                "description": "Require your attention today"
            })
        if meetings > 0:
            insights.append({
                "type": "info",
                "title": f"{meetings} meeting invites",
                "description": "Pending your response"
            })
        
        insights.append({
            "type": "trend",
            "title": "Data logging active",
            "description": "System is processing new emails"
        })

        return {
            "stats": {
                "total_emails": total_emails,
                "high_priority": high_priority,
                "meetings_detected": meetings,
                "unread_emails": unread_emails
            },
            "insights": insights
        }
    except Exception as e:
        logger.error(f"Failed to generate dashboard stats: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


# ─── Action Endpoints ──────────────────────────────────────────────────────────

@app.post(
    "/reply-email",
    summary="Reply to an Email (in-thread) via Gmail",
    tags=["Actions"],
)
def reply_email(request: ReplyRequest):
    """
    Send a reply within an existing Gmail thread, or start a new conversation.

    - Provide `thread_id` (from GET /emails → gmail_thread_id) to reply in-thread.
    - Omit `thread_id` to start a new email conversation.
    """
    gmail = _get_gmail()
    try:
        sent = gmail.send_email(
            to=request.to,
            subject=request.subject,
            body=request.body,
            thread_id=request.thread_id,
        )
    except Exception as e:
        logger.error(f"Failed to send reply: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send reply: {str(e)}")

    return {
        "message": "Reply sent successfully.",
        "gmail_message_id": sent.get("id"),
        "thread_id": sent.get("threadId"),
        "to": request.to,
        "subject": request.subject,
    }


@app.post(
    "/send-email",
    summary="Send a New Email via Gmail",
    tags=["Actions"],
)
def send_email(request: SendEmailRequest):
    """
    Send a brand-new outbound email (no threading).

    Use this endpoint for composing fresh emails from the dashboard.
    Use `/reply-email` (with `thread_id`) to reply within an existing conversation.
    """
    gmail = _get_gmail()
    try:
        sent = gmail.send_email(
            to=request.to,
            subject=request.subject,
            body=request.body,
            thread_id=None,
        )
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")

    return {
        "message": "Email sent successfully.",
        "gmail_message_id": sent.get("id"),
        "thread_id": sent.get("threadId"),
        "to": request.to,
        "subject": request.subject,
    }


@app.post(
    "/forward-email",
    summary="Forward an Existing Email to a New Recipient",
    tags=["Actions"],
)
def forward_email(request: ForwardEmailRequest):
    """
    Forward an existing Gmail message to a new recipient.

    The endpoint:
    1. Fetches the original message from Gmail by `message_id`
    2. Prepends an optional personal `note`
    3. Appends a standard forwarded-message block with the original content
    4. Sends as a new outbound email (separate thread)

    `message_id` is the `gmail_message_id` field returned by GET /emails.
    """
    if not request.message_id.strip():
        raise HTTPException(status_code=422, detail="message_id cannot be empty.")

    gmail = _get_gmail()
    try:
        sent = gmail.forward_email(
            message_id=request.message_id,
            to=request.to,
            note=request.note or "",
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to forward email: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to forward email: {str(e)}")

    return {
        "message": "Email forwarded successfully.",
        "gmail_message_id": sent.get("id"),
        "thread_id": sent.get("threadId"),
        "to": request.to,
        "original_message_id": request.message_id,
    }


@app.post(
    "/modify-email",
    summary="Modify Email Labels (Star, Archive, Delete, etc.)",
    tags=["Actions"],
)
def modify_email(request: ModifyEmailRequest):
    """
    Apply a label-based action to a Gmail message.

    | action       | Effect                            |
    |--------------|-----------------------------------|
    | star         | Add STARRED label                 |
    | unstar       | Remove STARRED label              |
    | archive      | Remove INBOX label (archives it)  |
    | unarchive    | Re-add INBOX label                |
    | delete       | Add TRASH, remove INBOX           |
    | restore      | Remove TRASH, add INBOX           |
    | mark_read    | Remove UNREAD label               |
    | mark_unread  | Add UNREAD label                  |

    `message_id` is the `gmail_message_id` field returned by GET /emails.

    **Requires `gmail.modify` scope** — re-authenticate if you had gmail.readonly.
    """
    if not request.message_id.strip():
        raise HTTPException(status_code=422, detail="message_id cannot be empty.")

    valid_actions = {
        "star", "unstar", "archive", "unarchive",
        "delete", "restore", "mark_read", "mark_unread",
    }
    if request.action not in valid_actions:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid action '{request.action}'. "
                   f"Must be one of: {', '.join(sorted(valid_actions))}"
        )

    gmail = _get_gmail()
    try:
        gmail.modify_email(
            message_id=request.message_id,
            action=request.action,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to modify email: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to modify email: {str(e)}")

    return {
        "message": f"Email action '{request.action}' applied successfully.",
        "message_id": request.message_id,
        "action": request.action,
    }


@app.post(
    "/create-event",
    summary="Create a Google Calendar Event",
    tags=["Actions"],
)
def create_event(request: CreateEventRequest):
    """
    Create a Google Calendar event — optionally using AI to extract details
    from a raw email body.

    **Two modes:**

    **1. AI-assisted (recommended for dashboard):**
    Provide `email_body` and Gemini will extract title, start/end times,
    location, and attendees automatically. Any manually supplied fields
    override the AI-extracted values.

    **2. Manual:**
    Provide `title`, `start_datetime`, `end_datetime` directly.

    **Note:** First call will open a browser OAuth window for Calendar access.
    Token is saved to `calendar_token.json` and reused on subsequent calls.
    """
    # ── Step 1: AI extraction (if email_body provided) ────────────────────
    extracted: dict = {}
    if request.email_body and request.email_body.strip():
        try:
            logger.info("Extracting event details from email body via Gemini...")
            extracted = extract_event_details_from_email(request.email_body)
            logger.info(f"AI extracted event: {extracted}")
        except Exception as e:
            logger.warning(f"AI extraction failed, continuing with manual fields: {e}")

    # ── Step 2: Merge — manual fields take priority over AI-extracted ─────
    title          = request.title          or extracted.get("title", "")
    start_datetime = request.start_datetime or extracted.get("start_datetime", "")
    end_datetime   = request.end_datetime   or extracted.get("end_datetime", "")
    description    = request.description   or extracted.get("description", "")
    location       = request.location      or extracted.get("location", "")
    attendees      = request.attendees      or extracted.get("attendees", [])
    timezone       = request.timezone       or "UTC"

    # ── Step 3: Validate required fields ──────────────────────────────────
    if not title.strip():
        raise HTTPException(
            status_code=422,
            detail="Event title is required. Provide 'title' or a parseable 'email_body'."
        )
    if not start_datetime.strip():
        raise HTTPException(
            status_code=422,
            detail=(
                "start_datetime is required (ISO 8601, e.g. 2024-04-20T10:00:00). "
                "Provide it manually or via a parseable 'email_body'."
            )
        )
    if not end_datetime.strip():
        # Default: 1 hour after start if AI couldn't extract
        from datetime import datetime, timedelta
        try:
            start_dt = datetime.fromisoformat(start_datetime)
            end_datetime = (start_dt + timedelta(hours=1)).isoformat()
            logger.info(f"end_datetime defaulted to 1 hour after start: {end_datetime}")
        except ValueError:
            raise HTTPException(
                status_code=422,
                detail="end_datetime is required and could not be inferred from start_datetime."
            )

    # ── Step 4: Create the calendar event ─────────────────────────────────
    try:
        calendar = CalendarService()
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Calendar authentication failed: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Calendar authentication error: {str(e)}"
        )

    try:
        event = calendar.create_event(
            title=title,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            description=description,
            location=location,
            attendees=attendees or None,
            timezone=timezone,
        )
    except Exception as e:
        logger.error(f"Calendar event creation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Calendar API error: {str(e)}"
        )

    return {
        "message": "Calendar event created successfully.",
        "event_id":    event.get("id"),
        "event_link":  event.get("htmlLink"),
        "title":       event.get("summary"),
        "start":       event.get("start", {}).get("dateTime"),
        "end":         event.get("end",   {}).get("dateTime"),
        "attendees":   attendees,
        "timezone":    timezone,
        "ai_extracted": bool(extracted),
    }


@app.post(
    "/generate-reply",
    summary="AI-Generate Reply Drafts for an Email",
    tags=["Actions"],
)
def generate_reply_endpoint(request: GenerateReplyRequest):
    """
    Use Gemini to generate professional reply drafts for an email.

    Returns 1–3 variations (Short / Medium / Detailed) based on the
    email's intent category, giving the user ready-to-send options.

    **Example request:**
    ```json
    {
      "email_body": "Hi, can we schedule a call this week to discuss milestones?",
      "category": "Meetings",
      "variations": 2
    }
    ```

    **Example response:**
    ```json
    {
      "category": "Meetings",
      "variations": [
        {"variation": 1, "label": "Short",  "reply": "Hi, I'd be happy to connect..."},
        {"variation": 2, "label": "Medium", "reply": "Thank you for reaching out..."}
      ]
    }
    ```
    """
    if not request.email_body.strip():
        raise HTTPException(status_code=422, detail="email_body cannot be empty.")

    try:
        replies = generate_reply(
            email_body=request.email_body,
            category=request.category,
            variations=request.variations,
        )
    except Exception as e:
        logger.error(f"Reply generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Reply generation error: {str(e)}")

    return {
        "category": request.category,
        "variations": replies,
    }
