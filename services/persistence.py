"""Persist simulation workflow data to PostgreSQL."""

from __future__ import annotations

from typing import Any, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from db.models import PamScanRecord, SequenceSession, SimulationRecord


def create_sequence_session(
    db: Session,
    *,
    session_id: UUID,
    user_id: Optional[UUID],
    sequence: str,
    gc_percent: Optional[float],
    composition: Optional[dict],
    accession: Optional[str] = None,
    source: str = "paste",
) -> SequenceSession:
    row = SequenceSession(
        id=session_id,
        user_id=user_id,
        sequence=sequence,
        length=len(sequence),
        gc_percent=gc_percent,
        accession=accession,
        source=source,
        composition=composition,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def save_pam_scan(
    db: Session,
    *,
    session_id: UUID,
    user_id: Optional[UUID],
    cas_type: str,
    pam_count: int,
    ranked_guides: Any,
    recommendation: Any,
) -> PamScanRecord:
    row = PamScanRecord(
        session_id=session_id,
        user_id=user_id,
        cas_type=cas_type,
        pam_count=pam_count,
        ranked_guides=ranked_guides,
        recommendation=recommendation,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def save_simulation_record(
    db: Session,
    *,
    session_id: UUID,
    user_id: Optional[UUID],
    original_sequence: str,
    edited_sequence: str,
    repair_type: str,
    cut_position: int,
    cas_type: Optional[str],
    frameshift: bool,
    premature_stop: bool,
    analysis: Optional[dict],
) -> SimulationRecord:
    row = SimulationRecord(
        session_id=session_id,
        user_id=user_id,
        original_sequence=original_sequence,
        edited_sequence=edited_sequence,
        repair_type=repair_type,
        cut_position=cut_position,
        cas_type=cas_type,
        frameshift=frameshift,
        premature_stop=premature_stop,
        analysis=analysis,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def get_user_sessions(db: Session, user_id: UUID, limit: int = 50) -> list[SequenceSession]:
    return (
        db.query(SequenceSession)
        .filter(SequenceSession.user_id == user_id)
        .order_by(SequenceSession.created_at.desc())
        .limit(limit)
        .all()
    )


def get_user_simulations(db: Session, user_id: UUID, limit: int = 50) -> list[SimulationRecord]:
    return (
        db.query(SimulationRecord)
        .filter(SimulationRecord.user_id == user_id)
        .order_by(SimulationRecord.created_at.desc())
        .limit(limit)
        .all()
    )
