"""
migrate_add_gmail_ids.py — One-shot schema migration script (v3.0.0 upgrade).

Adds two new columns to the `emails` table:
  - gmail_message_id TEXT  (nullable) — original Gmail API message ID
  - gmail_thread_id  TEXT  (nullable) — Gmail thread ID for threaded replies

Run once after upgrading to v3.0.0:
    python migrate_add_gmail_ids.py

Behaviour:
  - Checks whether each column already exists before adding it (idempotent).
  - Uses raw SQL via SQLAlchemy engine — no Alembic required.
  - Safe to run on a live database (ALTER TABLE ... ADD COLUMN IF NOT EXISTS).
  - Does NOT touch or delete any existing data.

PostgreSQL version required: 9.6+ (supports IF NOT EXISTS on ALTER TABLE).
"""

import logging
import sys

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

from config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


# ── Migration steps ────────────────────────────────────────────────────────────

MIGRATIONS = [
    {
        "description": "Add gmail_message_id column to emails table",
        "sql": """
            ALTER TABLE emails
            ADD COLUMN IF NOT EXISTS gmail_message_id TEXT;
        """,
    },
    {
        "description": "Add gmail_thread_id column to emails table",
        "sql": """
            ALTER TABLE emails
            ADD COLUMN IF NOT EXISTS gmail_thread_id TEXT;
        """,
    },
    {
        "description": "Create index on gmail_message_id for fast lookup",
        "sql": """
            CREATE INDEX IF NOT EXISTS ix_emails_gmail_message_id
            ON emails (gmail_message_id);
        """,
    },
]


def run_migration() -> None:
    """
    Execute all migration steps against the configured PostgreSQL database.

    Exits with code 0 on success, code 1 on failure.
    """
    logger.info(f"Connecting to database: {settings.DATABASE_URL[:40]}...")

    try:
        engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
    except Exception as e:
        logger.error(f"Failed to create database engine: {e}")
        sys.exit(1)

    with engine.connect() as conn:
        for i, step in enumerate(MIGRATIONS, start=1):
            logger.info(f"[{i}/{len(MIGRATIONS)}] {step['description']}...")
            try:
                conn.execute(text(step["sql"]))
                conn.commit()
                logger.info(f"  ✓ Done.")
            except SQLAlchemyError as e:
                logger.error(f"  ✗ Migration step {i} failed: {e}")
                conn.rollback()
                sys.exit(1)

    logger.info("=" * 60)
    logger.info("Migration complete. All columns added successfully.")
    logger.info("=" * 60)

    # Verify columns exist
    logger.info("Verifying schema...")
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'emails'
            ORDER BY ordinal_position;
        """))
        columns = [row[0] for row in result]
        logger.info(f"  emails table columns: {', '.join(columns)}")

        required = {"gmail_message_id", "gmail_thread_id"}
        missing = required - set(columns)
        if missing:
            logger.error(f"  ✗ Columns still missing after migration: {missing}")
            sys.exit(1)
        else:
            logger.info("  ✓ All required columns are present.")


if __name__ == "__main__":
    run_migration()
