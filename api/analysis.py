"""Translation and mutation analysis API routes."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.deps import require_api_user
from db.base import get_db
from db.models import User
from models.schemas import (
    CompareRequest,
    CompareResponse,
    TranslateRequest,
    TranslateResponse,
)
from services.analysis import compare_sequences
from services.persistence import save_simulation_record
from services.translation import translate_sequence
from services.validator import validate_and_clean

router = APIRouter(prefix="/analysis", tags=["Translation & Analysis"])


def _require_valid(sequence: str, label: str = "sequence") -> str:
    result = validate_and_clean(sequence)
    if not result["valid"]:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid DNA in {label}: {result['errors']}",
        )
    return result["cleaned"]


@router.post(
    "/translate",
    response_model=TranslateResponse,
    summary="Translate DNA → mRNA → Protein",
)
async def translate(
    request: TranslateRequest,
    user: Optional[User] = Depends(require_api_user),
):
    seq = _require_valid(request.sequence)
    if len(seq) < 3:
        raise HTTPException(status_code=400, detail="Sequence too short to translate (< 3 bp).")
    return TranslateResponse(**translate_sequence(seq))


@router.post(
    "/compare",
    response_model=CompareResponse,
    summary="Compare original vs edited sequence for mutation effects",
)
async def compare(
    request: CompareRequest,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(require_api_user),
):
    orig = _require_valid(request.original_sequence, "original_sequence")
    edit = _require_valid(request.edited_sequence, "edited_sequence")
    if len(orig) < 3 or len(edit) < 3:
        raise HTTPException(status_code=400, detail="Both sequences must be ≥ 3 bp.")
    result = compare_sequences(orig, edit)
    response = CompareResponse(**result)

    if request.session_id and request.repair_type and request.cut_position is not None:
        try:
            save_simulation_record(
                db,
                session_id=UUID(request.session_id),
                user_id=user.id if user else None,
                original_sequence=orig,
                edited_sequence=edit,
                repair_type=request.repair_type,
                cut_position=request.cut_position,
                cas_type=request.cas_type,
                frameshift=result.get("frameshift", False),
                premature_stop=result.get("premature_stop", False),
                analysis=result,
            )
        except Exception:
            db.rollback()

    return response
