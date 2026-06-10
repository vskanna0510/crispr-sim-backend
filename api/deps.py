"""Shared FastAPI dependencies (auth, audit)."""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from core.config import get_settings
from core.security import decode_access_token
from db.base import get_db
from db.models import RevokedToken, User

bearer_scheme = HTTPBearer(auto_error=False)


def _client_ip(request: Request) -> Optional[str]:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return None


async def get_current_user_optional(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> Optional[User]:
    if not credentials:
        return None
    payload = decode_access_token(credentials.credentials)
    if not payload:
        return None
    jti = payload.get("jti")
    if jti and db.get(RevokedToken, jti):
        return None
    try:
        user_id = UUID(payload["sub"])
    except (KeyError, ValueError):
        return None
    user = db.get(User, user_id)
    if not user or not user.is_active:
        return None
    request.state.user = user
    return user


async def get_current_user(
    user: Optional[User] = Depends(get_current_user_optional),
) -> User:
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Register or log in.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def require_api_user(
    user: Optional[User] = Depends(get_current_user_optional),
) -> Optional[User]:
    """Require JWT when REQUIRE_AUTH=true; allow anonymous in tests."""
    settings = get_settings()
    if user is not None:
        return user
    if settings.require_auth:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Register or log in.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return None


def log_audit(
    db: Session,
    *,
    user_id: Optional[UUID],
    action: str,
    resource: Optional[str] = None,
    ip_address: Optional[str] = None,
    details: Optional[dict] = None,
) -> None:
    from db.models import AuditLog

    try:
        db.add(
            AuditLog(
                user_id=user_id,
                action=action,
                resource=resource,
                ip_address=ip_address,
                details=details,
            )
        )
        db.commit()
    except Exception:
        db.rollback()
