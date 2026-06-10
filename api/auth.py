"""Authentication: register, login, logout, profile."""

from __future__ import annotations

import re
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from api.deps import get_current_user, log_audit, _client_ip
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
