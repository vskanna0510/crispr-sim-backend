"""Rank gRNA candidates by efficiency, specificity, and composite safety."""

from __future__ import annotations

from typing import Dict, List

from ml.guide_scoring import score_grna
from services.off_target import predict_off_targets


def _specificity_from_offtargets(off_target_count: int, overall_risk: str) -> float:
    base = 0.97 - off_target_count * 0.04
    if overall_risk == "HIGH":
        base -= 0.12
    elif overall_risk == "MODERATE":
        base -= 0.06
    return round(max(0.55, min(0.99, base)) * 100, 1)


def rank_guides(sequence: str, pam_sites: List[Dict]) -> Dict:
    ranked: List[Dict] = []
    idx = 0
    for site in pam_sites:
        grna = site.get("grna")
        if not grna:
            continue
        idx += 1
        score_info = score_grna(grna)
        ot = predict_off_targets(sequence, grna, site["start"])
        efficiency = round(score_info["score"] * 100, 1)
        specificity = _specificity_from_offtargets(ot["off_target_count"], ot["overall_risk"])
        gc = site.get("gc_percent") or score_info.get("gc_content", 0)
        gc_bonus = 4 if 40 <= gc <= 60 else 0
        safety = round((specificity * 0.55 + efficiency * 0.35 + gc_bonus) / 1.0, 1)
        safety = min(99.0, max(50.0, safety))

        ranked.append({
            "rank": 0,
            "guide_id": f"gRNA-{idx}",
            "grna": grna,
            "pam": site["pam"],
            "pam_start": site["start"],
            "efficiency_percent": efficiency,
            "specificity_percent": specificity,
            "safety_percent": safety,
            "grade": score_info.get("grade", "C"),
            "off_target_count": ot["off_target_count"],
            "overall_risk": ot["overall_risk"],
            "recommended": site.get("recommended"),
            "gc_percent": gc,
        })

    ranked.sort(
        key=lambda x: (x["safety_percent"], x["specificity_percent"], x["efficiency_percent"]),
        reverse=True,
    )
    for i, entry in enumerate(ranked, start=1):
        entry["rank"] = i

    recommendation = ranked[0] if ranked else None
    reasons: List[str] = []
    if recommendation:
        if recommendation["specificity_percent"] >= 90:
            reasons.append("Highest specificity among candidates")
        if recommendation["off_target_count"] <= 1:
            reasons.append("Lowest off-target risk")
        if recommendation.get("recommended"):
            reasons.append("Optimal GC content (40–60%)")
        if recommendation["efficiency_percent"] >= 85:
            reasons.append("Strong predicted editing efficiency")
        if not reasons:
            reasons.append("Best composite safety score")

    return {
        "total_guides": len(ranked),
        "ranked_guides": ranked,
        "recommended_guide": recommendation,
        "recommendation_reasons": reasons,
    }
