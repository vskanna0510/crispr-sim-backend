"""Per-user settings (history saving, etc.)."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from db.models import UserSettings


def get_or_create_settings(db: Session, user_id: UUID) -> UserSettings:
    row = db.get(UserSettings, user_id)
    if row is None:
        row = UserSettings(user_id=user_id, save_history=True)
        db.add(row)
        db.commit()
        db.refresh(row)
    return row


def user_saves_history(db: Session, user_id: UUID | None) -> bool:
    if user_id is None:
        return True
    try:
        return get_or_create_settings(db, user_id).save_history
    except Exception:
        return True
