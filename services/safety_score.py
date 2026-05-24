"""Composite CRISPR safety score for a selected guide."""

from __future__ import annotations

from typing import Dict, Optional

from ml.guide_scoring import score_grna
from services.off_target import predict_off_targets


def compute_safety_score(
    sequence: str,
    grna: str,
    pam_start: int,
    gc_percent: Optional[float] = None,
) -> Dict:
    score_info = score_grna(grna)
    ot = predict_off_targets(sequence, grna, pam_start)
    gc = gc_percent if gc_percent is not None else score_info.get("gc_content", 50)

    off_target_component = 40
    if ot["overall_risk"] == "HIGH":
        off_target_component = 12
    elif ot["overall_risk"] == "MODERATE":
        off_target_component = 26
    off_target_component -= ot["off_target_count"] * 2
    off_target_component = max(5, min(40, off_target_component))

    gc_component = 25 if 40 <= gc <= 60 else (15 if 30 <= gc <= 70 else 8)
    pam_component = 20 if score_info.get("grade") in ("A", "B") else 12
    efficiency_component = round(score_info["score"] * 15)

    total = int(round(off_target_component + gc_component + pam_component + efficiency_component))
    total = max(0, min(100, total))

    label = "Excellent" if total >= 85 else "Good" if total >= 70 else "Moderate" if total >= 55 else "Caution"

    return {
        "score": total,
        "max_score": 100,
        "label": label,
        "factors": {
            "off_target_risk": off_target_component,
            "gc_content": gc_component,
            "pam_quality": pam_component,
            "guide_efficiency": efficiency_component,
        },
        "off_target_summary": ot,
        "overall_risk": ot["overall_risk"],
    }
