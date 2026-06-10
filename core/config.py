"""Application settings (env-driven)."""

from __future__ import annotations

import os
from functools import lru_cache


@lru_cache
def get_settings() -> "Settings":
    return Settings()


class Settings:
  def __init__(self) -> None:
    self.database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql://crispr:crispr_secret@localhost:5432/crispr_sim",
    )
    self.jwt_secret: str = os.getenv(
        "JWT_SECRET",
        "dev-change-this-jwt-secret-in-production",
    )
    self.jwt_algorithm: str = "HS256"
    self.access_token_expire_minutes: int = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440")
    )
    self.require_auth: bool = os.getenv("REQUIRE_AUTH", "true").lower() == "true"
    self.cors_origins: list[str] = [
        o.strip()
        for o in os.getenv("CORS_ORIGINS", "*").split(",")
        if o.strip()
    ]
