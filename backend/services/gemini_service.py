"""
services/gemini_service.py — Google Gemini API client.

Provides a `generate_response()` function that communicates
with the Gemini API (gemini-2.5-flash) to generate LLM responses.
"""

import logging
import google.generativeai as genai
from google.api_core.exceptions import GoogleAPIError

from config import settings

logger = logging.getLogger(__name__)

# Configure the Gemini library with out API key
if settings.GEMINI_API_KEY:
    genai.configure(api_key=settings.GEMINI_API_KEY)
else:
    logger.warning("GEMINI_API_KEY is not set. Gemini API calls will fail.")


def generate_response(prompt: str) -> str:
    """
    Send a text prompt to the Gemini API and return the response.

    Uses `gemini-2.5-flash` for fast, accurate interactions.

    Args:
        prompt: The text prompt to send to the model.

    Returns:
        The model's response as a plain string.

    Raises:
        ValueError: If GEMINI_API_KEY is missing or response is empty.
        RuntimeError: On connection or API errors.
    """
    if not settings.GEMINI_API_KEY:
        raise ValueError(
            "GEMINI_API_KEY is missing. "
            "Please add it to your .env file."
        )

    logger.debug(f"Sending prompt to Gemini: {prompt[:80]}...")

    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        
        # Configure generation for deterministic output
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.2,
                top_p=0.9,
            )
        )
        
        text = response.text.strip()
        
        if not text:
            raise ValueError("Gemini returned an empty response.")
            
        logger.debug(f"Gemini response length: {len(text)}")
        return text

    except GoogleAPIError as e:
        logger.error(f"Gemini API error: {e}")
        raise RuntimeError(f"Gemini API error: {e}") from e
    except Exception as e:
        logger.error(f"Unexpected error communicating with Gemini: {e}")
        raise RuntimeError(f"Unexpected error with Gemini: {e}") from e
