"""Lightweight schema patches for existing PostgreSQL databases."""

from __future__ import annotations

import logging

from sqlalchemy import text

logger = logging.getLogger(__name__)

_USER_SETTINGS_COLUMNS = (
    ("theme_mode", "VARCHAR(16) DEFAULT 'system'"),
    ("analytics_enabled", "BOOLEAN DEFAULT TRUE"),
)


def apply_schema_patches(engine) -> None:
    try:
        with engine.begin() as conn:
            for col, typedef in _USER_SETTINGS_COLUMNS:
                conn.execute(
                    text(
                        f"ALTER TABLE user_settings ADD COLUMN IF NOT EXISTS "
                        f"{col} {typedef}"
                    )
                )
    except Exception as exc:
        logger.warning("Schema patch skipped: %s", exc)
