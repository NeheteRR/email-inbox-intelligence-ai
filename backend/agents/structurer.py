"""
agents/structurer.py — Structuring Agent.

Responsibility: Combine raw email metadata with the analyzer's output
and produce a clean, validated JSON-ready Python dict.

Updated: Uses intent-based categories; adds `action` field derived from category.
"""

import logging
from typing import Any

from crewai import Agent, Task, LLM
from config import settings

logger = logging.getLogger(__name__)

# ── Intent-Based Category → Action Label Mapping ──────────────────────────────
ACTION_LABEL_MAP: dict[str, str] = {
    "Tasks":      "Action Required",
    "Follow-ups": "Needs Reply",
    "Events":     "Decision Needed",
    "Meetings":   "Schedule",
    "Finance":    "Verify",
    "Reports":    "Review",
    "References": "Review",
    "Promotions": "Review",
}


def get_action_label(category: str) -> str:
    """
    Derive a user-facing action label from an intent-based category.

    Args:
        category: One of the canonical intent-based category strings.

    Returns:
        A short action label string for dashboard display.

    Examples:
        >>> get_action_label("Tasks")
        'Action Required'
        >>> get_action_label("Follow-ups")
        'Needs Reply'
        >>> get_action_label("Unknown")
        'Review'
    """
    return ACTION_LABEL_MAP.get(category, "Review")


class StructurerAgent:
    """
    Agent 3: Email Structurer

    Merges email metadata (sender, subject) with LLM-generated
    analysis fields (summary, category, priority) and derives
    the action label. Produces the final DB-ready dict.
    """

    def __init__(self):
        self.agent = Agent(
            role="Data Structurer",
            llm=LLM(
                model="gemini/gemini-2.5-flash",
                api_key=settings.GEMINI_API_KEY,
            ),
            goal=(
                "Combine email metadata and analysis results into a "
                "clean, validated JSON-compatible Python dictionary "
                "including the intent-based category and action label."
            ),
            backstory=(
                "You are a data engineering specialist who transforms "
                "semi-structured text into precise, schema-conformant records "
                "ready for database insertion and API responses."
            ),
            verbose=True,
            allow_delegation=False,
        )

    def create_task(
        self,
        raw_email: dict[str, Any],
        analysis: dict[str, str],
    ) -> Task:
        """
        Build a CrewAI Task for structuring the final email record.

        Args:
            raw_email: Original email dict (sender, subject, body).
            analysis: Analyzer output (summary, category, priority).

        Returns:
            A CrewAI Task whose expected output is a structured record.
        """
        category = analysis.get("category", "References")
        action = get_action_label(category)

        description = (
            "Structure the following email data into a clean record:\n\n"
            f"  Sender:   {raw_email.get('sender', 'Unknown')}\n"
            f"  Subject:  {raw_email.get('subject', '(No Subject)')}\n"
            f"  Summary:  {analysis.get('summary', '')}\n"
            f"  Category: {category}\n"
            f"  Priority: {analysis.get('priority', 'Low')}\n"
            f"  Action:   {action}\n\n"
            "Validate all fields are non-empty. Return a JSON object with "
            "keys: sender, subject, summary, category, priority, action."
        )

        return Task(
            description=description,
            expected_output=(
                '{"sender": "...", "subject": "...", "summary": "...", '
                '"category": "...", "priority": "...", "action": "..."}'
            ),
            agent=self.agent,
        )

    def structure(
        self,
        raw_email: dict[str, Any],
        analysis: dict[str, str],
    ) -> dict[str, str]:
        """
        Directly produce a structured, validated email record.

        Used by the CrewAI orchestrator to build the final output
        without an additional LLM call (structuring is deterministic).

        Args:
            raw_email: Original email dict.
            analysis: Analyzer output dict.

        Returns:
            Clean structured dict with all required fields including `action`.
        """
        category = self._validate_category(analysis.get("category", "References"))
        action = get_action_label(category)

        structured = {
            "sender":   self._sanitize(raw_email.get("sender", "Unknown Sender")),
            "subject":  self._sanitize(raw_email.get("subject", "(No Subject)")),
            "summary":  self._sanitize(analysis.get("summary", "No summary available.")),
            "category": category,
            "priority": self._validate_priority(analysis.get("priority", "Low")),
            "action":   action,
        }

        logger.info(
            f"Structured email: subject='{structured['subject']}' "
            f"category={structured['category']} priority={structured['priority']} "
            f"action='{structured['action']}'"
        )
        return structured

    # ── Validation Helpers ────────────────────────────────────────────────

    @staticmethod
    def _sanitize(value: str) -> str:
        """Strip whitespace and ensure the value is non-empty."""
        return value.strip() if isinstance(value, str) and value.strip() else "N/A"

    @staticmethod
    def _validate_category(category: str) -> str:
        """Ensure category is one of the allowed intent-based labels."""
        allowed = {
            "Meetings", "Events", "Tasks", "Follow-ups",
            "Reports", "References", "Finance", "Promotions",
        }
        # Try exact match first
        if category in allowed:
            return category
        # Try title-cased match
        title = category.strip().title()
        if title in allowed:
            return title
        # Import normalize as a last resort
        from agents.analyzer import normalize_category
        return normalize_category(category)

    @staticmethod
    def _validate_priority(priority: str) -> str:
        """Ensure priority is Low, Medium, or High."""
        allowed = {"Low", "Medium", "High"}
        pri = priority.strip().capitalize()
        return pri if pri in allowed else "Low"
