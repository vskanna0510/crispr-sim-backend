"""Aggregate per-user usage analytics from persisted workflow data."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from db.models import PamScanRecord, SequenceSession, SimulationRecord


def get_user_analytics(db: Session, user_id: UUID) -> dict[str, Any]:
    sessions_q = db.query(SequenceSession).filter(SequenceSession.user_id == user_id)
    scans_q = db.query(PamScanRecord).filter(PamScanRecord.user_id == user_id)
    sims_q = db.query(SimulationRecord).filter(SimulationRecord.user_id == user_id)

    total_sessions = sessions_q.count()
    total_scans = scans_q.count()
    total_simulations = sims_q.count()
    frameshift_count = sims_q.filter(SimulationRecord.frameshift.is_(True)).count()
    nhej_count = sims_q.filter(SimulationRecord.repair_type == "NHEJ").count()
    hdr_count = sims_q.filter(SimulationRecord.repair_type == "HDR").count()

    avg_gc = sessions_q.with_entities(func.avg(SequenceSession.gc_percent)).scalar()
    last_session: Optional[datetime] = (
        sessions_q.with_entities(func.max(SequenceSession.created_at)).scalar()
    )
    last_sim: Optional[datetime] = (
        sims_q.with_entities(func.max(SimulationRecord.created_at)).scalar()
    )

    sources = (
        db.query(SequenceSession.source, func.count(SequenceSession.id))
        .filter(SequenceSession.user_id == user_id)
        .group_by(SequenceSession.source)
        .all()
    )

    return {
        "total_sequences": total_sessions,
        "total_pam_scans": total_scans,
        "total_simulations": total_simulations,
        "frameshift_count": frameshift_count,
        "nhej_count": nhej_count,
        "hdr_count": hdr_count,
        "average_gc_percent": round(float(avg_gc), 2) if avg_gc is not None else None,
        "last_sequence_at": last_session.isoformat() if last_session else None,
        "last_simulation_at": last_sim.isoformat() if last_sim else None,
        "input_sources": {src: count for src, count in sources},
    }
