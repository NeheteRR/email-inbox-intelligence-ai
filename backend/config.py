"""
config.py — Centralized configuration via environment variables.

All hardcoded values are replaced with env-based settings.
Copy `.env.example` to `.env` and fill in your values.
"""

import os
from dotenv import load_dotenv, find_dotenv

# Use find_dotenv() to automatically locate the .env file even if it's in the parent root folder
load_dotenv(find_dotenv())


class Settings:
    """Application-wide settings loaded from environment variables."""

    # ── Gmail ──────────────────────────────────────────────────────────────
    GMAIL_CREDENTIALS_PATH: str = os.getenv("GMAIL_CREDENTIALS_PATH", "credentials.json")
    GMAIL_TOKEN_PATH: str = os.getenv("GMAIL_TOKEN_PATH", "token.json")
    EMAIL_FETCH_LIMIT: int = int(os.getenv("EMAIL_FETCH_LIMIT", "5"))

    # ── Google Calendar ────────────────────────────────────────────────────
    # Separate token file for Calendar scope — avoids invalidating Gmail token
    CALENDAR_TOKEN_PATH: str = os.getenv("CALENDAR_TOKEN_PATH", "calendar_token.json")

    # ── Gemini API ─────────────────────────────────────────────────────────
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

    # ── Database ───────────────────────────────────────────────────────────
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/email_db")

    # ── Application ────────────────────────────────────────────────────────
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))


settings = Settings()
