"""CRISPR simulation API routes: PAM scan, cut, NHEJ, HDR."""

from fastapi import APIRouter, HTTPException

from services.validator import validate_and_clean
from services.cas_systems import get_cas_system, scan_pam_for_cas, extract_grna_for_cas
from services.cut_engine import simulate_cut
from services.repair_engine import nhej_repair, hdr_repair
from services.guide_ranking import rank_guides
from models.schemas import (
    ScanRequest, ScanResponse, PAMSiteResult,
    RankedGuideResult, GuideRecommendation,
    CutRequest, CutResponse,
    NHEJRequest, HDRRequest, RepairResponse,
)

router = APIRouter(prefix="/crispr", tags=["CRISPR Simulation"])


def _require_valid_sequence(sequence: str) -> str:
    result = validate_and_clean(sequence)
    if not result["valid"]:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid DNA sequence: {result['errors']}",
        )
    return result["cleaned"]


def _enrich_sites(sequence: str, raw_sites: list, cas) -> list:
    enriched = []
    for site in raw_sites:
        info = extract_grna_for_cas(sequence, site["start"], site["end"], cas)
        entry = dict(site)
        if info:
            entry.update({
                "grna": info["grna"],
                "gc_percent": info["gc_percent"],
                "recommended": info["recommended"],
            })
        else:
            entry.update({"grna": None, "gc_percent": None, "recommended": None})
        enriched.append(entry)
    return enriched


def _merge_ranking(pam_sites: list, ranking: dict) -> list:
    rank_map = {g["pam_start"]: g for g in ranking.get("ranked_guides", [])}
    merged = []
    for site in pam_sites:
        entry = dict(site)
        r = rank_map.get(site["start"])
        if r:
            entry.update({
                "rank": r["rank"],
                "guide_id": r["guide_id"],
                "efficiency_percent": r["efficiency_percent"],
                "specificity_percent": r["specificity_percent"],
                "safety_percent": r["safety_percent"],
                "off_target_count": r["off_target_count"],
                "overall_risk": r["overall_risk"],
            })
        merged.append(entry)
    return merged


@router.post("/scan", response_model=ScanResponse, summary="Scan PAM sites for selected Cas system")
async def scan_pam(request: ScanRequest):
    seq = _require_valid_sequence(request.sequence)
    try:
        cas = get_cas_system(request.cas_type)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    raw_sites = scan_pam_for_cas(seq, cas)
    enriched = _enrich_sites(seq, raw_sites, cas)
    ranking = rank_guides(seq, enriched)
    merged = _merge_ranking(enriched, ranking)

    pam_results = [PAMSiteResult(**site) for site in merged]
    ranked = [RankedGuideResult(**g) for g in ranking["ranked_guides"]]

    rec = ranking.get("recommended_guide")
    recommendation = None
    if rec:
        recommendation = GuideRecommendation(
            guide_id=rec["guide_id"],
            grna=rec["grna"],
            pam_start=rec["pam_start"],
            efficiency_percent=rec["efficiency_percent"],
            specificity_percent=rec["specificity_percent"],
            safety_percent=rec["safety_percent"],
            reasons=ranking.get("recommendation_reasons", []),
        )

    return ScanResponse(
        sequence=seq,
        pam_sites=pam_results,
        count=len(pam_results),
        cas_type=cas.id,
        cas_name=cas.name,
        pam_motif=cas.pam_motif,
        target_molecule=cas.target_molecule,
        application=cas.application,
        ranked_guides=ranked,
        recommendation=recommendation,
    )


@router.post("/cut", response_model=CutResponse, summary="Simulate Cas cut at selected PAM")
async def cut(request: CutRequest):
    seq = _require_valid_sequence(request.sequence)
    if request.pam_start < 0 or request.pam_start >= len(seq):
        raise HTTPException(
            status_code=400,
            detail=f"pam_start {request.pam_start} is out of valid range.",
        )
    try:
        cas = get_cas_system(request.cas_type)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    pam_end = request.pam_start + 3
    if cas.id == "cas12a":
        pam_end = request.pam_start + 4
    result = simulate_cut(seq, request.pam_start, request.cas_type, pam_end=pam_end)
    return CutResponse(**{k: v for k, v in result.items() if k in CutResponse.model_fields})


@router.post("/nhej", response_model=RepairResponse, summary="Apply NHEJ (indel) repair")
async def nhej(request: NHEJRequest):
    seq = _require_valid_sequence(request.sequence)
    if request.cut_position < 0 or request.cut_position >= len(seq):
        raise HTTPException(status_code=400, detail="cut_position is out of range.")
    result = nhej_repair(seq, request.cut_position, request.deletion_size)
    return RepairResponse(**result)


@router.post("/hdr", response_model=RepairResponse, summary="Apply HDR (donor template) repair")
async def hdr(request: HDRRequest):
    seq = _require_valid_sequence(request.sequence)
    donor_check = validate_and_clean(request.donor_template)
    if not donor_check["valid"]:
        raise HTTPException(
            status_code=422,
            detail=f"Donor template contains invalid characters: {donor_check['errors']}",
        )
    if request.cut_position < 0 or request.cut_position >= len(seq):
        raise HTTPException(status_code=400, detail="cut_position is out of range.")
    result = hdr_repair(
        seq,
        request.cut_position,
        donor_check["cleaned"],
        request.replacement_length,
    )
    return RepairResponse(**result)
