"""Sequence input API routes."""

import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException

from services.sequence_input import parse_fasta_content, fetch_from_ncbi
from services.validator import validate_and_clean
from models.schemas import SequencePasteRequest, SequenceResponse

router = APIRouter(prefix="/sequence", tags=["Sequence Input"])


def _build_response(cleaned: str, result: dict) -> SequenceResponse:
    return SequenceResponse(
        sequence=cleaned,
        length=len(cleaned),
        valid=True,
        session_id=str(uuid.uuid4()),
        gc_percent=result.get("gc_percent"),
        composition=result.get("composition"),
    )


@router.post("/paste", response_model=SequenceResponse, summary="Paste a raw DNA string")
async def paste_sequence(request: SequencePasteRequest):
    result = validate_and_clean(request.sequence)
    if not result["valid"]:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid characters found: {result['errors']}",
        )
    return _build_response(result["cleaned"], result)


@router.post("/upload", response_model=SequenceResponse, summary="Upload a FASTA file")
async def upload_fasta(file: UploadFile = File(...)):
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
    return _build_response(result["cleaned"], result)


@router.get(
    "/fetch/{accession}",
    response_model=SequenceResponse,
    summary="Fetch sequence from NCBI by accession ID",
)
async def fetch_ncbi(accession: str):
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
    resp = _build_response(result["cleaned"], result)
    resp.session_id = str(uuid.uuid4())
    return resp
