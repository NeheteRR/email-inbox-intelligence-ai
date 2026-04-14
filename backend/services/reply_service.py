"""
services/reply_service.py — AI-Powered Email Reply Generator.

Uses Gemini to generate professional reply drafts based on
the email body and its intent-based category.

Provides:
  - build_reply_prompt()  — Constructs the LLM prompt
  - generate_reply()      — Returns 1–3 reply variations
"""

import json
import logging
import re
from typing import Any
from services.gemini_service import generate_response

logger = logging.getLogger(__name__)


# ── Per-Category Reply Tone Guidance ──────────────────────────────────────────
CATEGORY_TONE_MAP: dict[str, str] = {
    "Meetings":   "Confirm or propose a meeting time. Be concise and professional.",
    "Events":     "Accept, decline, or request more details about the event. Be polite.",
    "Tasks":      "Acknowledge the task, state your plan or ask for clarification if needed.",
    "Follow-ups": "Provide a thoughtful follow-up response. Be direct and helpful.",
    "Reports":    "Acknowledge receipt of the report and mention any next steps.",
    "References": "Acknowledge the information briefly. Keep it short.",
    "Finance":    "Confirm financial details, ask for clarification, or acknowledge receipt.",
    "Promotions": "Politely decline or request more information if genuinely interested.",
}

DEFAULT_TONE = "Be professional, concise, and helpful."


def build_reply_prompt(email_body: str, category: str, variation_index: int = 1) -> str:
    """
    Build a structured Gemini prompt for generating an email reply.

    Args:
        email_body:       The original email content to reply to.
        category:         Intent-based category (e.g. Tasks, Meetings).
        variation_index:  Which variation to generate (1, 2, or 3).
                          Each variation targets a different tone/length.

    Returns:
        Formatted prompt string ready for generate_response().
    """
    tone_guidance = CATEGORY_TONE_MAP.get(category, DEFAULT_TONE)

    variation_instructions = {
        1: "Write a SHORT reply (2–3 sentences). Direct and to-the-point.",
        2: "Write a MEDIUM reply (4–6 sentences). Friendly and professional.",
        3: "Write a DETAILED reply (7–10 sentences). Thorough and courteous.",
    }
    variation_note = variation_instructions.get(variation_index, variation_instructions[1])

    prompt = f"""\
You are a professional email assistant. Write a reply to the email below.

ORIGINAL EMAIL:
{email_body}

EMAIL CATEGORY: {category}
TONE GUIDANCE: {tone_guidance}
VARIATION: {variation_note}

Rules:
- Write ONLY the reply body text — no subject line, no "To:", no headers.
- Do NOT include any meta-commentary like "Here is a reply:" or explanations.
- Start directly with the greeting or the first sentence of the reply.
- Sign off naturally (e.g. "Best regards," or "Thanks,").
- Keep the language professional and natural.

Write the reply now:"""

    return prompt


def generate_reply(
    email_body: str,
    category: str,
    variations: int = 2,
) -> list[dict[str, Any]]:
    """
    Generate AI-powered reply suggestions for a given email.

    Calls Gemini once per variation, building distinct prompts for
    short, medium, and detailed tone variants.

    Args:
        email_body:  The original email text to reply to.
        category:    Intent-based category (drives tone guidance).
        variations:  Number of reply drafts to generate (1–3). Default: 2.

    Returns:
        List of dicts, each with:
          - variation (int): 1, 2, or 3
          - label (str):     "Short", "Medium", or "Detailed"
          - reply (str):     The generated reply text

    Example:
        [
          {"variation": 1, "label": "Short",  "reply": "Thanks for reaching out..."},
          {"variation": 2, "label": "Medium", "reply": "Thank you for your message..."},
        ]
    """
    variations = max(1, min(variations, 3))  # Clamp to 1–3
    labels = {1: "Short", 2: "Medium", 3: "Detailed"}
    results = []

    for i in range(1, variations + 1):
        prompt = build_reply_prompt(email_body, category, variation_index=i)
        try:
            raw = generate_response(prompt)
            reply_text = _clean_reply_text(raw)
            results.append({
                "variation": i,
                "label":     labels[i],
                "reply":     reply_text,
            })
            logger.info(
                f"Generated reply variation {i} ({labels[i]}) "
                f"for category '{category}' ({len(reply_text)} chars)"
            )
        except Exception as e:
            logger.error(f"Failed to generate reply variation {i}: {e}")
            results.append({
                "variation": i,
                "label":     labels[i],
                "reply":     f"[Reply generation failed: {str(e)}]",
            })

    return results


def _clean_reply_text(raw: str) -> str:
    """
    Strip any LLM preamble/postamble from the generated reply.

    Removes lines like:
    - "Here is a reply:"
    - "Sure, here's a professional reply:"
    - Empty leading/trailing lines

    Args:
        raw: Raw LLM output string.

    Returns:
        Cleaned reply body string.
    """
    if not raw:
        return ""

    # Remove common LLM preamble patterns
    preamble_patterns = [
        r"^(?:here(?:'s| is)(?: a| the)?(?: professional| short| medium| detailed)? reply[:\-]?)\s*",
        r"^(?:sure[,!]?\s+here(?:'s| is)[^:\n]*[:\-]?)\s*",
        r"^(?:of course[,!]?\s*[:\-]?)\s*",
        r"^(?:below is[^:\n]*[:\-]?)\s*",
    ]
    text = raw.strip()
    for pattern in preamble_patterns:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE).strip()

    # Remove markdown formatting if model returned it
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)  # **bold**
    text = re.sub(r"\*(.*?)\*", r"\1", text)        # *italic*

    return text.strip()
