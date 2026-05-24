"""Pydantic schemas for all API request/response models."""

from pydantic import BaseModel, Field
from typing import Optional, List


# ─── Sequence ────────────────────────────────────────────────────────────────

class SequencePasteRequest(BaseModel):
    sequence: str = Field(..., description="Raw DNA string (A/T/C/G)")


class SequenceResponse(BaseModel):
    sequence: str
    length: int
    valid: bool
    session_id: Optional[str] = None
    gc_percent: Optional[float] = None
    composition: Optional[dict] = None


# ─── PAM / gRNA ──────────────────────────────────────────────────────────────

class PAMSiteResult(BaseModel):
    pam: str
    start: int
    end: int
    grna: Optional[str] = None
    gc_percent: Optional[float] = None
    recommended: Optional[bool] = None
    rank: Optional[int] = None
    guide_id: Optional[str] = None
    efficiency_percent: Optional[float] = None
    specificity_percent: Optional[float] = None
    safety_percent: Optional[float] = None
    off_target_count: Optional[int] = None
    overall_risk: Optional[str] = None


class ScanRequest(BaseModel):
    sequence: str
    cas_type: str = Field("cas9", description="cas9 | cas12a | cas13")


class RankedGuideResult(BaseModel):
    rank: int
    guide_id: str
    grna: str
    pam: str
    pam_start: int
    efficiency_percent: float
    specificity_percent: float
    safety_percent: float
    grade: str
    off_target_count: int
    overall_risk: str
    recommended: Optional[bool] = None
    gc_percent: Optional[float] = None


class GuideRecommendation(BaseModel):
    guide_id: str
    grna: str
    pam_start: int
    efficiency_percent: float
    specificity_percent: float
    safety_percent: float
    reasons: List[str] = Field(default_factory=list)


class ScanResponse(BaseModel):
    sequence: str
    pam_sites: List[PAMSiteResult]
    count: int
    cas_type: str
    cas_name: str
    pam_motif: str
    target_molecule: str
    application: str
    ranked_guides: List[RankedGuideResult] = Field(default_factory=list)
    recommendation: Optional[GuideRecommendation] = None


# ─── Cut ─────────────────────────────────────────────────────────────────────

class CutRequest(BaseModel):
    sequence: str
    pam_start: int
    cas_type: str = Field("cas9", description="cas9 | cas12a | cas13")


class CutResponse(BaseModel):
    cut_position: int
    upstream: str
    downstream: str
    pam_start: int
    sequence: str


# ─── Repair ──────────────────────────────────────────────────────────────────

class NHEJRequest(BaseModel):
    sequence: str
    cut_position: int
    deletion_size: Optional[int] = Field(None, ge=1, le=10,
                                         description="Bases to delete (1–10); random if omitted")


class HDRRequest(BaseModel):
    sequence: str
    cut_position: int
    donor_template: str = Field(..., description="Donor sequence to insert at cut site")
    replacement_length: int = Field(0, ge=0, description="Bases to replace at cut site")


class RepairResponse(BaseModel):
    repaired_sequence: str
    repair_type: str
    cut_position: int
    deletion_size: Optional[int] = None
    donor_template: Optional[str] = None
    original_length: int
    repaired_length: int


# ─── Translation / Analysis ──────────────────────────────────────────────────

class TranslateRequest(BaseModel):
    sequence: str


class TranslateResponse(BaseModel):
    dna: str
    mrna: str
    protein: str
    codon_count: int
    trimmed_length: int


class CompareRequest(BaseModel):
    original_sequence: str
    edited_sequence: str


class CompareResponse(BaseModel):
    original_protein: str
    edited_protein: str
    original_mrna: str
    edited_mrna: str
    frameshift: bool
    premature_stop: bool
    length_diff: int
    original_length: int
    edited_length: int
    summary: str


# ─── RAG Chat ───────────────────────────────────────────────────────────────

class RAGChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000, description="User question")
    top_k: int = Field(4, ge=1, le=10, description="Number of knowledge chunks to retrieve")


class RAGChatResponse(BaseModel):
    answer: str
    sources: List[str] = Field(default_factory=list, description="Retrieved chunk ids")


# ─── Advanced modules ─────────────────────────────────────────────────────────

class CasSystemInfo(BaseModel):
    id: str
    name: str
    pam_motif: str
    grna_length: int
    target_molecule: str
    application: str
    description: str


class OffTargetSite(BaseModel):
    location: str
    mismatches: int
    risk: str
    risk_color: str
    sequence_context: str
    source: str


class OffTargetRequest(BaseModel):
    sequence: str
    grna: str
    pam_start: int


class OffTargetResponse(BaseModel):
    grna: str
    off_target_count: int
    sites: List[OffTargetSite]
    overall_risk: str
    overall_risk_color: str


class SafetyScoreRequest(BaseModel):
    sequence: str
    grna: str
    pam_start: int
    gc_percent: Optional[float] = None


class SafetyScoreResponse(BaseModel):
    score: int
    max_score: int
    label: str
    factors: dict
    overall_risk: str


class GeneInfoResponse(BaseModel):
    accession: Optional[str] = None
    found: bool
    gene_symbol: str
    gene_name: str
    chromosome: str
    function: str
    associated_diseases: List[str] = Field(default_factory=list)
    supporting_studies: List[str] = Field(default_factory=list)


class LiteratureCaseSummary(BaseModel):
    id: str
    title: str
    accession: Optional[str] = None
    description: str


class LiteratureValidationRequest(BaseModel):
    case_id: str
    original_sequence: str
    edited_sequence: Optional[str] = None
    cut_position: Optional[int] = None
    deletion_size: Optional[int] = None


class LiteratureComparisonRow(BaseModel):
    parameter: str
    literature: object
    application: object
    match: bool


class LiteratureValidationResponse(BaseModel):
    case_id: str
    title: str
    literature: dict
    predicted: dict
    comparison_rows: List[LiteratureComparisonRow]
    validation_score_percent: float
    summary: str
    supporting_studies: List[str]
