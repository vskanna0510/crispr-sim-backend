"""User session and simulation history from PostgreSQL."""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.deps import get_current_user
from db.base import get_db
from db.models import User
from services.persistence import get_user_sessions, get_user_simulations

router = APIRouter(prefix="/history", tags=["History"])


class SessionSummary(BaseModel):
    id: str
    length: int
    gc_percent: Optional[float]
    accession: Optional[str]
    source: str
    created_at: str


class SimulationSummary(BaseModel):
    id: int
    session_id: str
    repair_type: str
    cut_position: int
    frameshift: bool
    premature_stop: bool
    created_at: str


@router.get("/sessions", response_model=list[SessionSummary])
def list_sessions(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    rows = get_user_sessions(db, user.id)
    return [
        SessionSummary(
            id=str(r.id),
            length=r.length,
            gc_percent=r.gc_percent,
            accession=r.accession,
            source=r.source,
            created_at=r.created_at.isoformat(),
        )
        for r in rows
    ]


@router.get("/simulations", response_model=list[SimulationSummary])
def list_simulations(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    rows = get_user_simulations(db, user.id)
    return [
        SimulationSummary(
            id=r.id,
            session_id=str(r.session_id),
            repair_type=r.repair_type,
            cut_position=r.cut_position,
            frameshift=r.frameshift,
            premature_stop=r.premature_stop,
            created_at=r.created_at.isoformat(),
        )
        for r in rows
    ]


@router.delete("/sessions/{session_id}", summary="Delete a specific project/session")
def delete_session(
    session_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    from uuid import UUID
    from db.models import SequenceSession, SimulationRecord
    from fastapi import HTTPException, status

    try:
        sess_uuid = UUID(session_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid session UUID format.")

    session_obj = (
        db.query(SequenceSession)
        .filter(SequenceSession.id == sess_uuid, SequenceSession.user_id == user.id)
        .first()
    )
    if not session_obj:
        raise HTTPException(status_code=404, detail="Session not found or unauthorized.")

    db.query(SimulationRecord).filter(SimulationRecord.session_id == sess_uuid).delete()
    db.delete(session_obj)
    db.commit()
    return {"message": "Project session and simulations deleted successfully."}


@router.delete("/simulations/{simulation_id}", summary="Delete a specific simulation record")
def delete_simulation(
    simulation_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    from db.models import SimulationRecord
    from fastapi import HTTPException

    sim = (
        db.query(SimulationRecord)
        .filter(SimulationRecord.id == simulation_id, SimulationRecord.user_id == user.id)
        .first()
    )
    if not sim:
        raise HTTPException(status_code=404, detail="Simulation not found or unauthorized.")

    db.delete(sim)
    db.commit()
    return {"message": "Simulation record deleted successfully."}


@router.delete("/clear", summary="Delete all project sessions and simulation records for user")
def clear_all_user_data(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    from db.models import SequenceSession, SimulationRecord

    db.query(SimulationRecord).filter(SimulationRecord.user_id == user.id).delete()
    db.query(SequenceSession).filter(SequenceSession.user_id == user.id).delete()
    db.commit()
    return {"message": "All user project and simulation data cleared successfully."}


@router.get("/papers", response_model=list[dict[str, Any]])
def list_research_papers(db: Session = Depends(get_db)):
    from db.models import ResearchPaper

    papers = db.query(ResearchPaper).order_by(ResearchPaper.year.desc()).all()
    return [
        {
            "pmid": p.pmid,
            "title": p.title,
            "authors": p.authors,
            "journal": p.journal,
            "year": p.year,
            "doi": p.doi,
            "abstract": p.abstract,
            "gene_symbols": p.gene_symbols,
            "topics": p.topics,
            "url": p.url,
        }
        for p in papers
    ]
