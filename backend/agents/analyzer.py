"""
agents/analyzer.py — Analyzer Agent.

Responsibility: Use Ollama LLM to generate a summary, classify
the email into an intent-based category, and assign a priority level.

Updated: Prompt returns strict JSON; category list is intent-based.
"""

import json
import logging
import re
from typing import Any

from crewai import Agent, Task
from config import settings

from services.gemini_service import generate_response

logger = logging.getLogger(__name__)

# ── Valid Intent-Based Categories ─────────────────────────────────────────────
VALID_CATEGORIES = [
    "Meetings", "Events", "Tasks", "Follow-ups",
    "Reports", "References", "Finance", "Promotions", "Other"
]

def normalize_category(cat: str) -> str:
    """Normalize output cleanly using user-provided logic."""
    cat = cat.lower()
    if "meeting" in cat:
        return "Meetings"
    elif "event" in cat or "invite" in cat:
        return "Events"
    elif "task" in cat or "action" in cat:
        return "Tasks"
    elif "follow" in cat or "reminder" in cat:
        return "Follow-ups"
    elif "report" in cat or "update" in cat:
        return "Reports"
    elif "reference" in cat or "info" in cat:
        return "References"
    elif "invoice" in cat or "payment" in cat:
        return "Finance"
    elif "promo" in cat or "newsletter" in cat:
        return "Promotions"
    else:
        return "Other"

# ── Prompt Template ───────────────────────────────────────────────────────────
ANALYSIS_PROMPT_TEMPLATE = """\
You are an AI email assistant.

Analyze the email and classify it into EXACTLY ONE of the following categories:
- Meetings
- Events
- Tasks
- Follow-ups
- Reports
- References
- Finance
- Promotions
- Other

Rules:
- If the email clearly fits one category, choose that
- If it does NOT clearly fit any category, assign "Other"
- Do NOT invent new categories

Also provide:
1. A short 1-line summary
2. Category (strictly from list)
3. Priority (Low, Medium, High)

EMAIL:
Sender: {sender}
Subject: {subject}
Body: {body}

Return ONLY valid JSON:
{{
"summary": "...",
"category": "...",
"priority": "..."
}}
"""


class AnalyzerAgent:
    """
    Agent 2: Email Analyzer

    Uses the Gemini API to produce:
    - 1-line summary
    - Intent-based category classification
    - Priority level (secondary metadata)
    """

    def __init__(self):
        self.agent = Agent(
            role="Email Analyzer",
            goal=(
                "Analyze email content to generate a concise summary, "
                "classify its intent-based category, and assign a priority level."
            ),
            backstory=(
                "You are a senior email intelligence analyst trained to quickly "
                "extract key insights from emails and classify them by intent."
            ),
            verbose=True,
            allow_delegation=False,
        )

    def create_task(self, cleaned_email_text: str, raw_email: dict[str, Any]) -> Task:
        """
        Build a CrewAI Task that calls Gemini to analyze the email.

        Args:
            cleaned_email_text: Output from the EmailReaderAgent.
            raw_email: Original raw email dict for sender/subject fallback.

        Returns:
            A CrewAI Task whose output contains structured JSON analysis.
        """
        prompt = ANALYSIS_PROMPT_TEMPLATE.format(
            sender=raw_email.get("sender", "Unknown"),
            subject=raw_email.get("subject", "(No Subject)"),
            body=cleaned_email_text,
        )

        try:
            llm_response = generate_response(prompt)
        except Exception as e:
            logger.error(f"Gemini call failed during analysis: {e}")
            llm_response = '{"summary": "Could not analyze email.", "category": "Other", "priority": "Low"}'

        description = (
            f"The following LLM analysis was produced for the email:\n\n"
            f"{llm_response}\n\n"
            "Validate the JSON contains summary, category, and priority fields. "
            "If any field is missing, insert a sensible default."
        )

        return Task(
            description=description,
            expected_output=(
                'A JSON object: {"summary": "...", "category": "...", "priority": "..."} '
                "with category from the intent-based list and priority Low/Medium/High."
            ),
            agent=self.agent,
        )

    def analyze(self, raw_email: dict[str, Any]) -> dict[str, str]:
        """
        Directly call Gemini and parse the structured JSON response.
        Used by the CrewAI orchestrator for direct analysis.

        Args:
            raw_email: Dict with sender, subject, body fields.

        Returns:
            Dict with summary, category, priority keys.
        """
        prompt = ANALYSIS_PROMPT_TEMPLATE.format(
            sender=raw_email.get("sender", "Unknown"),
            subject=raw_email.get("subject", "(No Subject)"),
            body=raw_email.get("body", ""),
        )

        try:
            response = generate_response(prompt)
            return self._parse_response(response)
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            return {
                "summary": "Analysis unavailable.",
                "category": "Other",
                "priority": "Low",
            }

    # ── Parsing ───────────────────────────────────────────────────────────

    @staticmethod
    def _parse_response(response: str) -> dict[str, str]:
        """
        Parse the JSON LLM output into a Python dict.

        Attempts JSON parsing first; falls back to regex line-scraping
        to handle models that add extra prose around the JSON block.

        Args:
            response: Raw LLM text output.

        Returns:
            Dict with summary, category, priority (all normalized).
        """
        defaults = {
            "summary": "No summary available.",
            "category": "Other",
            "priority": "Low",
        }

        # ── Attempt 1: Extract and parse JSON block ────────────────────
        try:
            # Strip markdown fences if present (```json ... ```)
            cleaned = re.sub(r"```(?:json)?", "", response, flags=re.IGNORECASE).strip()
            # Extract the first {...} block
            match = re.search(r"\{.*?\}", cleaned, re.DOTALL)
            if match:
                data = json.loads(match.group())
                result = dict(defaults)
                if "summary" in data and data["summary"]:
                    result["summary"] = str(data["summary"]).strip()
                if "category" in data:
                    result["category"] = normalize_category(str(data.get("category", "")))
                if "priority" in data:
                    pri = str(data.get("priority", "")).strip().capitalize()
                    result["priority"] = pri if pri in {"Low", "Medium", "High"} else "Low"
                return result
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"JSON parse failed ({e}), falling back to line-scraping.")

        # ── Attempt 2: Legacy line-scraping fallback ───────────────────
        result = dict(defaults)
        for line in response.splitlines():
            line = line.strip()
            if line.upper().startswith("SUMMARY:"):
                val = line.split(":", 1)[1].strip()
                if val:
                    result["summary"] = val
            elif line.upper().startswith("CATEGORY:"):
                val = line.split(":", 1)[1].strip()
                result["category"] = normalize_category(val)
            elif line.upper().startswith("PRIORITY:"):
                val = line.split(":", 1)[1].strip().capitalize()
                if val in {"Low", "Medium", "High"}:
                    result["priority"] = val

        return result
