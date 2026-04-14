"""
services/database.py — PostgreSQL persistence layer (SQLAlchemy).

Provides:
  - engine / SessionLocal setup
  - get_db()    — FastAPI dependency for session injection
  - init_db()   — Create tables on startup
  - insert_email() — Persist a structured email record
  - get_emails()   — Retrieve paginated email records
"""

import logging
from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError

from config import settings
from .models import Base, Email

logger = logging.getLogger(__name__)

# ─── Engine & Session Factory ──────────────────────────────────────────────────

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,   # Automatically reconnect on stale connections
    pool_size=5,
    max_overflow=10,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """
    FastAPI dependency: yield a database session and ensure it is
    closed after the request completes (even on exceptions).
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ─── Lifecycle ─────────────────────────────────────────────────────────────────

def init_db() -> None:
    """
    Create all ORM-mapped tables in the PostgreSQL database if they
    do not already exist. Called once on application startup.

    Raises:
        SQLAlchemyError: If the database is unreachable or DDL fails.
    """
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("PostgreSQL tables verified/created successfully.")
    except SQLAlchemyError as e:
        logger.error(f"Database initialization failed: {e}")
        raise


# ─── CRUD ──────────────────────────────────────────────────────────────────────

def insert_email(db: Session, email_data: dict[str, Any]) -> int:
    """
    Insert a structured email record into the `emails` table.

    Args:
        db:         Active SQLAlchemy session (injected via Depends).
        email_data: Dict containing email fields. Expected keys:
                    gmail_message_id, gmail_thread_id, sender, subject,
                    summary, category, priority, action.

    Returns:
        The auto-generated `id` of the newly inserted row.

    Raises:
        SQLAlchemyError: On insertion failure (rolled back automatically).
    """
    record = Email(
        gmail_message_id = email_data.get("id") or email_data.get("gmail_message_id"),
        gmail_thread_id  = email_data.get("thread_id") or email_data.get("gmail_thread_id"),
        sender           = email_data.get("sender",   "Unknown"),
        subject          = email_data.get("subject",  "(No Subject)"),
        summary          = email_data.get("summary",  ""),
        category         = email_data.get("category", "References"),
        priority         = email_data.get("priority", "Low"),
        action           = email_data.get("action",   "Review"),
    )
    try:
        db.add(record)
        db.commit()
        db.refresh(record)
        logger.info(
            f"Inserted email id={record.id}: '{record.subject}' "
            f"[{record.category} | {record.action}]"
        )
        return record.id
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Failed to insert email: {e}")
        raise


def get_emails(
    db: Session,
    limit: int = 100,
    offset: int = 0,
) -> list[dict[str, Any]]:
    """
    Retrieve stored emails from the database, newest first (by id DESC).

    Args:
        db:     Active SQLAlchemy session.
        limit:  Maximum number of records to return.
        offset: Number of records to skip (for pagination).

    Returns:
        List of email dicts with all schema fields including `action`.

    Raises:
        SQLAlchemyError: On query failure.
    """
    try:
        emails = (
            db.query(Email)
            .order_by(Email.id.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        return [
            {
                "id":               email.id,
                "gmail_message_id": email.gmail_message_id,
                "gmail_thread_id":  email.gmail_thread_id,
                "sender":           email.sender,
                "subject":          email.subject,
                "summary":          email.summary,
                "category":         email.category,
                "priority":         email.priority,
                "action":           email.action,
            }
            for email in emails
        ]
    except SQLAlchemyError as e:
        logger.error(f"Failed to read emails: {e}")
        raise
