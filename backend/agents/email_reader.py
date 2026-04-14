"""
agents/email_reader.py — Email Reader Agent.

Responsibility: Accept a raw Gmail email dict and return
a cleaned, normalized text representation suitable for LLM input.
"""

import logging
import re
from typing import Any

from crewai import Agent, Task, LLM
from config import settings

logger = logging.getLogger(__name__)

# Maximum characters to send to the LLM (avoid context overflow)
MAX_BODY_LENGTH = 1500


class EmailReaderAgent:
    """
    Agent 1: Email Reader

    Cleans and normalizes raw email data.
    Strips HTML tags, excess whitespace, and truncates oversized bodies.
    """

    def __init__(self):
        self.agent = Agent(
            role="Email Reader",
            llm=LLM(
                model="gemini/gemini-2.5-flash",
                api_key=settings.GEMINI_API_KEY,
            ),
            goal=(
                "Parse and clean raw email content, removing noise such as "
                "HTML tags and excessive whitespace, producing readable plain text."
            ),
            backstory=(
                "You are a precision data-cleaning specialist. You preprocess "
                "raw email payloads to make them ready for analysis by downstream AI agents."
            ),
            verbose=True,
            allow_delegation=False,
        )

    def create_task(self, raw_email: dict[str, Any]) -> Task:
        """
        Build a CrewAI Task for cleaning the provided raw email.

        Args:
            raw_email: Dict with sender, subject, body fields.

        Returns:
            A CrewAI Task object.
        """
        cleaned_body = self._clean_text(raw_email.get("body", ""))

        description = (
            f"Clean and normalize the following email:\n\n"
            f"Sender:  {raw_email.get('sender', 'Unknown')}\n"
            f"Subject: {raw_email.get('subject', '(No Subject)')}\n"
            f"Body:\n{cleaned_body}\n\n"
            "Return the cleaned email as plain readable text with "
            "sender, subject, and body clearly labeled."
        )

        return Task(
            description=description,
            expected_output=(
                "A clean, structured plain-text representation of the email "
                "with Sender, Subject, and Body sections."
            ),
            agent=self.agent,
        )

    # ── Helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _clean_text(text: str) -> str:
        """
        Strip HTML tags, normalize whitespace, and truncate long bodies.

        Args:
            text: Raw email body string.

        Returns:
            Cleaned plain-text string.
        """
        if not text:
            return ""

        # Remove HTML tags
        text = re.sub(r"<[^>]+>", " ", text)

        # Decode common HTML entities
        replacements = {
            "&nbsp;": " ", "&amp;": "&", "&lt;": "<",
            "&gt;": ">", "&quot;": '"', "&#39;": "'",
        }
        for entity, char in replacements.items():
            text = text.replace(entity, char)

        # Collapse whitespace
        text = re.sub(r"\s+", " ", text).strip()

        # Truncate to avoid LLM context overflow
        if len(text) > MAX_BODY_LENGTH:
            text = text[:MAX_BODY_LENGTH] + "... [truncated]"

        return text
