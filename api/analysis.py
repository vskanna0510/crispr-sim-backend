"""Translation and mutation analysis API routes."""

from fastapi import APIRouter, HTTPException

from services.validator import validate_and_clean
from services.translation import translate_sequence
from services.analysis import compare_sequences
from models.schemas import (
    TranslateRequest, TranslateResponse,
    CompareRequest, CompareResponse,
)

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
async def translate(request: TranslateRequest):
    seq = _require_valid(request.sequence)
    if len(seq) < 3:
        raise HTTPException(status_code=400, detail="Sequence too short to translate (< 3 bp).")
    return TranslateResponse(**translate_sequence(seq))


@router.post(
    "/compare",
    response_model=CompareResponse,
    summary="Compare original vs edited sequence for mutation effects",
)
async def compare(request: CompareRequest):
    orig = _require_valid(request.original_sequence, "original_sequence")
    edit = _require_valid(request.edited_sequence, "edited_sequence")
    if len(orig) < 3 or len(edit) < 3:
        raise HTTPException(status_code=400, detail="Both sequences must be ≥ 3 bp.")
    return CompareResponse(**compare_sequences(orig, edit))
