"""
services/models.py — SQLAlchemy database models.

Defines the ORM-mapped Email table used by PostgreSQL.
"""

from sqlalchemy import Column, Integer, Text
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Email(Base):
    """
    ORM model for the `emails` table.

    Columns:
        id               — Auto-incremented primary key (SERIAL)
        gmail_message_id — Original Gmail message ID (for reply/forward/modify)
        gmail_thread_id  — Gmail thread ID (for threaded replies)
        sender           — Email sender address / display name
        subject          — Email subject line
        summary          — AI-generated one-sentence summary
        category         — Intent-based classification (e.g. Tasks, Meetings)
        priority         — Secondary metadata: Low | Medium | High
        action           — Derived action label (e.g. Action Required, Needs Reply)
    """
    __tablename__ = "emails"

    id               = Column(Integer, primary_key=True, index=True)
    gmail_message_id = Column(Text, nullable=True, index=True)  # Gmail API message ID
    gmail_thread_id  = Column(Text, nullable=True)              # Gmail thread ID
    sender           = Column(Text, nullable=False)
    subject          = Column(Text, nullable=False)
    summary          = Column(Text, nullable=True)
    category         = Column(Text, nullable=True)
    priority         = Column(Text, nullable=True)
    action           = Column(Text, nullable=True)
