"""User settings and app ratings."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from api.deps import get_current_user
from db.base import get_db
from db.models import AppRating, User, UserSettings
from services.user_settings import get_or_create_settings

router = APIRouter(prefix="/settings", tags=["Settings"])


class SettingsResponse(BaseModel):
    save_history: bool


class SettingsUpdateRequest(BaseModel):
    save_history: bool


class RatingResponse(BaseModel):
    stars: int
    comment: Optional[str] = None
    updated_at: Optional[str] = None


class RatingSubmitRequest(BaseModel):
    stars: int = Field(ge=1, le=5)
    comment: Optional[str] = Field(default=None, max_length=1000)


@router.get("", response_model=SettingsResponse)
def get_settings(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    row = get_or_create_settings(db, user.id)
    return SettingsResponse(save_history=row.save_history)


@router.patch("", response_model=SettingsResponse)
def update_settings(
    body: SettingsUpdateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    row = get_or_create_settings(db, user.id)
    row.save_history = body.save_history
    row.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(row)
    return SettingsResponse(save_history=row.save_history)


@router.get("/rating", response_model=Optional[RatingResponse])
def get_rating(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    row = db.get(AppRating, user.id)
    if not row:
        return None
    return RatingResponse(
        stars=row.stars,
        comment=row.comment,
        updated_at=row.updated_at.isoformat() if row.updated_at else None,
    )


@router.post("/rating", response_model=RatingResponse)
def submit_rating(
    body: RatingSubmitRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    now = datetime.now(timezone.utc)
    row = db.get(AppRating, user.id)
    if row is None:
        row = AppRating(
            user_id=user.id,
            stars=body.stars,
            comment=body.comment,
            created_at=now,
            updated_at=now,
        )
        db.add(row)
    else:
        row.stars = body.stars
        row.comment = body.comment
        row.updated_at = now
    db.commit()
    db.refresh(row)
    return RatingResponse(
        stars=row.stars,
        comment=row.comment,
        updated_at=row.updated_at.isoformat() if row.updated_at else None,
    )
