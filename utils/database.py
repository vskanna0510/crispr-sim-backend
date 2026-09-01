"""Database initialisation (PostgreSQL via SQLAlchemy)."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def init_db() -> None:
    """Create tables and seed reference data if PostgreSQL is available."""
    try:
        from db.base import Base, engine
        from scripts.seed_database import seed

        from utils.migrations import apply_schema_patches

        Base.metadata.create_all(bind=engine)
        apply_schema_patches(engine)
        seed()
        logger.info("PostgreSQL schema ready and seed data loaded.")
    except Exception as exc:
        logger.warning("Database init skipped or partial: %s", exc)


def database_status() -> str:
    try:
        from db.base import engine
        from sqlalchemy import text

        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return "postgresql"
    except Exception:
        return "unavailable"
