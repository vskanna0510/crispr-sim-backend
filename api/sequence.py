"""Sequence input API routes."""

import uuid
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from sqlalchemy.orm import Session

from api.deps import _client_ip, log_audit, require_api_user
from db.base import get_db
from db.models import User
from models.schemas import SequencePasteRequest, SequenceResponse
from services.persistence import create_sequence_session
from services.user_settings import user_saves_history
from services.sequence_input import fetch_from_ncbi, parse_fasta_content
from services.validator import validate_and_clean

router = APIRouter(prefix="/sequence", tags=["Sequence Input"])


def _build_response(
    cleaned: str,
    result: dict,
    *,
    session_id: str,
) -> SequenceResponse:
    return SequenceResponse(
        sequence=cleaned,
        length=len(cleaned),
        valid=True,
        session_id=session_id,
        gc_percent=result.get("gc_percent"),
        composition=result.get("composition"),
    )


def _persist_session(
    db: Session,
    user: Optional[User],
    session_id: UUID,
    cleaned: str,
    result: dict,
    *,
    accession: Optional[str] = None,
    source: str = "paste",
) -> None:
    try:
        create_sequence_session(
            db,
            session_id=session_id,
            user_id=user.id if user else None,
            sequence=cleaned,
            gc_percent=result.get("gc_percent"),
            composition=result.get("composition"),
            accession=accession,
            source=source,
        )
    except Exception:
        db.rollback()


@router.post("/paste", response_model=SequenceResponse, summary="Paste a raw DNA string")
async def paste_sequence(
    request: Request,
    body: SequencePasteRequest,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(require_api_user),
):
    result = validate_and_clean(body.sequence)
    if not result["valid"]:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid characters found: {result['errors']}",
        )
    session_id = str(uuid.uuid4())
    if user_saves_history(db, user.id if user else None):
        _persist_session(db, user, UUID(session_id), result["cleaned"], result, source="paste")
    log_audit(
        db,
        user_id=user.id if user else None,
        action="sequence_paste",
        resource=session_id,
        ip_address=_client_ip(request),
        details={"length": len(result["cleaned"])},
    )
    return _build_response(result["cleaned"], result, session_id=session_id)


@router.post("/upload", response_model=SequenceResponse, summary="Upload a FASTA file")
async def upload_fasta(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(require_api_user),
):
    if not file.filename.endswith((".fasta", ".fa", ".fna", ".txt")):
        raise HTTPException(
            status_code=415,
            detail="File must be a FASTA file (.fasta / .fa / .fna / .txt)",
        )
    raw = await file.read()
    sequence = parse_fasta_content(raw.decode("utf-8", errors="ignore"))
    if not sequence:
        raise HTTPException(status_code=400, detail="Could not parse FASTA file.")
    result = validate_and_clean(sequence)
    if not result["valid"]:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid characters: {result['errors']}",
        )
    session_id = str(uuid.uuid4())
    if user_saves_history(db, user.id if user else None):
        _persist_session(db, user, UUID(session_id), result["cleaned"], result, source="fasta")
    log_audit(
        db,
        user_id=user.id if user else None,
        action="sequence_upload",
        resource=session_id,
        ip_address=_client_ip(request),
    )
    return _build_response(result["cleaned"], result, session_id=session_id)


@router.get(
    "/fetch/{accession}",
    response_model=SequenceResponse,
    summary="Fetch sequence from NCBI by accession ID",
)
async def fetch_ncbi(
    request: Request,
    accession: str,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(require_api_user),
):
    data = await fetch_from_ncbi(accession)
    if not data:
        raise HTTPException(
            status_code=404,
            detail=f"Sequence not found for accession '{accession}'. "
            "Check the ID or NCBI connectivity.",
        )
    result = validate_and_clean(data["sequence"])
    if not result["valid"]:
        raise HTTPException(
            status_code=422,
            detail=f"Fetched sequence contains invalid characters: {result['errors']}",
        )
    session_id = str(uuid.uuid4())
    if user_saves_history(db, user.id if user else None):
        _persist_session(
            db,
            user,
            UUID(session_id),
            result["cleaned"],
            result,
            accession=accession,
            source="ncbi",
        )
    log_audit(
        db,
        user_id=user.id if user else None,
        action="sequence_ncbi",
        resource=session_id,
        ip_address=_client_ip(request),
        details={"accession": accession},
    )
    return _build_response(result["cleaned"], result, session_id=session_id)
