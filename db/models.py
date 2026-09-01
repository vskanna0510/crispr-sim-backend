"""PostgreSQL ORM models for CRISPR-Sim."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    sessions: Mapped[list["SequenceSession"]] = relationship(back_populates="user")
    simulations: Mapped[list["SimulationRecord"]] = relationship(back_populates="user")
    audit_logs: Mapped[list["AuditLog"]] = relationship(back_populates="user")
    settings: Mapped["UserSettings | None"] = relationship(back_populates="user", uselist=False)
    app_rating: Mapped["AppRating | None"] = relationship(back_populates="user", uselist=False)


class RevokedToken(Base):
    """JWT blocklist for logout."""

    __tablename__ = "revoked_tokens"

    jti: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id"))
    revoked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class SequenceSession(Base):
    __tablename__ = "sequence_sessions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id"), nullable=True, index=True
    )
    sequence: Mapped[str] = mapped_column(Text, nullable=False)
    length: Mapped[int] = mapped_column(Integer)
    gc_percent: Mapped[float | None] = mapped_column(Float, nullable=True)
    accession: Mapped[str | None] = mapped_column(String(64), nullable=True)
    source: Mapped[str] = mapped_column(String(32), default="paste")
    composition: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    user: Mapped[User | None] = relationship(back_populates="sessions")
    pam_scans: Mapped[list["PamScanRecord"]] = relationship(back_populates="session")
    simulations: Mapped[list["SimulationRecord"]] = relationship(back_populates="session")


class PamScanRecord(Base):
    __tablename__ = "pam_scans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("sequence_sessions.id"), index=True
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id"), nullable=True
    )
    cas_type: Mapped[str] = mapped_column(String(32), default="cas9")
    pam_count: Mapped[int] = mapped_column(Integer)
    ranked_guides: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    recommendation: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    session: Mapped[SequenceSession] = relationship(back_populates="pam_scans")


class SimulationRecord(Base):
    __tablename__ = "simulations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("sequence_sessions.id"), index=True
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id"), nullable=True, index=True
    )
    original_sequence: Mapped[str] = mapped_column(Text)
    edited_sequence: Mapped[str] = mapped_column(Text)
    repair_type: Mapped[str] = mapped_column(String(16))
    cut_position: Mapped[int] = mapped_column(Integer)
    cas_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    frameshift: Mapped[bool] = mapped_column(Boolean, default=False)
    premature_stop: Mapped[bool] = mapped_column(Boolean, default=False)
    analysis: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    user: Mapped[User | None] = relationship(back_populates="simulations")
    session: Mapped[SequenceSession] = relationship(back_populates="simulations")


class Gene(Base):
    __tablename__ = "genes"
    __table_args__ = (UniqueConstraint("accession_root", name="uq_genes_accession_root"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    accession_root: Mapped[str] = mapped_column(String(32), index=True)
    gene_symbol: Mapped[str] = mapped_column(String(32))
    gene_name: Mapped[str] = mapped_column(String(255))
    chromosome: Mapped[str] = mapped_column(String(8))
    function: Mapped[str] = mapped_column(Text)
    associated_diseases: Mapped[list] = mapped_column(JSON, default=list)
    supporting_studies: Mapped[list] = mapped_column(JSON, default=list)


class LiteratureCase(Base):
    __tablename__ = "literature_cases"
    __table_args__ = (UniqueConstraint("case_key", name="uq_literature_case_key"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    case_key: Mapped[str] = mapped_column(String(64), index=True)
    title: Mapped[str] = mapped_column(String(255))
    accession: Mapped[str | None] = mapped_column(String(64), nullable=True)
    description: Mapped[str] = mapped_column(Text)
    expected_outcomes: Mapped[dict] = mapped_column(JSON)
    demo_sequence_prefix: Mapped[str | None] = mapped_column(String(64), nullable=True)
    paper_ids: Mapped[list] = mapped_column(JSON, default=list)


class ResearchPaper(Base):
    __tablename__ = "research_papers"
    __table_args__ = (UniqueConstraint("pmid", name="uq_research_papers_pmid"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    pmid: Mapped[str] = mapped_column(String(32))
    title: Mapped[str] = mapped_column(Text)
    authors: Mapped[str] = mapped_column(String(512))
    journal: Mapped[str] = mapped_column(String(255))
    year: Mapped[int] = mapped_column(Integer)
    doi: Mapped[str | None] = mapped_column(String(128), nullable=True)
    abstract: Mapped[str] = mapped_column(Text)
    gene_symbols: Mapped[list] = mapped_column(JSON, default=list)
    topics: Mapped[list] = mapped_column(JSON, default=list)
    url: Mapped[str | None] = mapped_column(String(512), nullable=True)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id"), nullable=True
    )
    action: Mapped[str] = mapped_column(String(64))
    resource: Mapped[str | None] = mapped_column(String(128), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    details: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    user: Mapped[User | None] = relationship(back_populates="audit_logs")


class UserSettings(Base):
    __tablename__ = "user_settings"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id"), primary_key=True
    )
    save_history: Mapped[bool] = mapped_column(Boolean, default=True)
    theme_mode: Mapped[str] = mapped_column(String(16), default="system")
    analytics_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    user: Mapped[User] = relationship(back_populates="settings")


class AppRating(Base):
    __tablename__ = "app_ratings"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id"), primary_key=True
    )
    stars: Mapped[int] = mapped_column(Integer)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    user: Mapped[User] = relationship(back_populates="app_rating")
