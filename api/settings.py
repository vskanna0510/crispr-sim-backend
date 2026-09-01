"""User settings, analytics, and app ratings."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from api.deps import get_current_user
from db.base import get_db
from db.models import AppRating, User, UserSettings
from services.analytics import get_user_analytics
from services.user_settings import get_or_create_settings

router = APIRouter(prefix="/settings", tags=["Settings"])

ThemeMode = Literal["system", "light", "dark"]


class SettingsResponse(BaseModel):
    save_history: bool
    theme_mode: ThemeMode = "system"
    analytics_enabled: bool = True


class SettingsUpdateRequest(BaseModel):
    save_history: Optional[bool] = None
    theme_mode: Optional[ThemeMode] = None
    analytics_enabled: Optional[bool] = None


class RatingResponse(BaseModel):
    stars: int
    comment: Optional[str] = None
    updated_at: Optional[str] = None


class RatingSubmitRequest(BaseModel):
    stars: int = Field(ge=1, le=5)
    comment: Optional[str] = Field(default=None, max_length=1000)


class AnalyticsResponse(BaseModel):
    total_sequences: int
    total_pam_scans: int
    total_simulations: int
    frameshift_count: int
    nhej_count: int
    hdr_count: int
    average_gc_percent: Optional[float] = None
    last_sequence_at: Optional[str] = None
    last_simulation_at: Optional[str] = None
    input_sources: dict[str, int] = Field(default_factory=dict)


def _settings_response(row: UserSettings) -> SettingsResponse:
    theme = row.theme_mode if row.theme_mode in ("system", "light", "dark") else "system"
    return SettingsResponse(
        save_history=row.save_history,
        theme_mode=theme,
        analytics_enabled=row.analytics_enabled,
    )


@router.get("", response_model=SettingsResponse)
def get_settings(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    row = get_or_create_settings(db, user.id)
    return _settings_response(row)


@router.patch("", response_model=SettingsResponse)
def update_settings(
    body: SettingsUpdateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    row = get_or_create_settings(db, user.id)
    if body.save_history is not None:
        row.save_history = body.save_history
    if body.theme_mode is not None:
        row.theme_mode = body.theme_mode
    if body.analytics_enabled is not None:
        row.analytics_enabled = body.analytics_enabled
    row.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(row)
    return _settings_response(row)


@router.get("/analytics", response_model=AnalyticsResponse)
def user_analytics(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    row = get_or_create_settings(db, user.id)
    if not row.analytics_enabled:
        raise HTTPException(
            status_code=403,
            detail="Analytics is disabled in your settings. Enable it to view usage stats.",
        )
    data: dict[str, Any] = get_user_analytics(db, user.id)
    return AnalyticsResponse(**data)


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
