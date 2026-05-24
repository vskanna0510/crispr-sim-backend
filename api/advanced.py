"""Advanced CRISPR modules: Cas systems, off-target, safety, literature validation."""

from fastapi import APIRouter, HTTPException, Query

from models.schemas import (
    CasSystemInfo,
    OffTargetRequest,
    OffTargetResponse,
    OffTargetSite,
    SafetyScoreRequest,
    SafetyScoreResponse,
    GeneInfoResponse,
    LiteratureCaseSummary,
    LiteratureValidationRequest,
    LiteratureValidationResponse,
    LiteratureComparisonRow,
)
from services.cas_systems import CAS_REGISTRY
from services.off_target import predict_off_targets
from services.safety_score import compute_safety_score
from services.gene_info import lookup_gene_info
from services.literature_validation import list_validation_cases, validate_against_literature
from services.validator import validate_and_clean

router = APIRouter(tags=["Advanced CRISPR"])


@router.get("/advanced/cas-systems", response_model=list[CasSystemInfo], summary="List supported Cas systems")
async def get_cas_systems():
    return [
        CasSystemInfo(
            id=c.id,
            name=c.name,
            pam_motif=c.pam_motif,
            grna_length=c.grna_length,
            target_molecule=c.target_molecule,
            application=c.application,
            description=c.description,
        )
        for c in CAS_REGISTRY.values()
    ]


@router.get(
    "/sequence/gene-info/{accession}",
    response_model=GeneInfoResponse,
    summary="Gene information card for NCBI accession",
)
async def gene_info(accession: str):
    info = lookup_gene_info(accession=accession)
    return GeneInfoResponse(**info)


@router.post(
    "/crispr/off-target",
    response_model=OffTargetResponse,
    summary="Predict off-target binding sites for a guide RNA",
)
async def off_target(body: OffTargetRequest):
    result = validate_and_clean(body.sequence)
    if not result["valid"]:
        raise HTTPException(status_code=422, detail=result["errors"])
    ot = predict_off_targets(result["cleaned"], body.grna, body.pam_start)
    return OffTargetResponse(
        grna=ot["grna"],
        off_target_count=ot["off_target_count"],
        sites=[OffTargetSite(**s) for s in ot["sites"]],
        overall_risk=ot["overall_risk"],
        overall_risk_color=ot["overall_risk_color"],
    )


@router.post(
    "/crispr/safety-score",
    response_model=SafetyScoreResponse,
    summary="Composite CRISPR safety score for a guide",
)
async def safety_score(body: SafetyScoreRequest):
    result = validate_and_clean(body.sequence)
    if not result["valid"]:
        raise HTTPException(status_code=422, detail=result["errors"])
    score = compute_safety_score(
        result["cleaned"],
        body.grna,
        body.pam_start,
        body.gc_percent,
    )
    return SafetyScoreResponse(
        score=score["score"],
        max_score=score["max_score"],
        label=score["label"],
        factors=score["factors"],
        overall_risk=score["overall_risk"],
    )


@router.get(
    "/validation/cases",
    response_model=list[LiteratureCaseSummary],
    summary="Published validation case studies",
)
async def validation_cases():
    return [LiteratureCaseSummary(**c) for c in list_validation_cases()]


@router.post(
    "/validation/literature",
    response_model=LiteratureValidationResponse,
    summary="Validate app prediction against published outcomes",
)
async def literature_validation(body: LiteratureValidationRequest):
    result = validate_and_clean(body.original_sequence)
    if not result["valid"]:
        raise HTTPException(status_code=422, detail=result["errors"])
    try:
        out = validate_against_literature(
            body.case_id,
            result["cleaned"],
            edited_sequence=body.edited_sequence,
            cut_position=body.cut_position,
            deletion_size=body.deletion_size,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return LiteratureValidationResponse(
        case_id=out["case_id"],
        title=out["title"],
        literature=out["literature"],
        predicted=out["predicted"],
        comparison_rows=[LiteratureComparisonRow(**r) for r in out["comparison_rows"]],
        validation_score_percent=out["validation_score_percent"],
        summary=out["summary"],
        supporting_studies=out["supporting_studies"],
    )
