"""Off-target prediction (heuristic): in-sequence similarity + illustrative genomic hits."""

from __future__ import annotations

import hashlib
from typing import Dict, List, Optional


def _hamming(a: str, b: str) -> int:
    return sum(x != y for x, y in zip(a, b))


def _risk_label(mismatches: int) -> str:
    if mismatches <= 1:
        return "HIGH"
    if mismatches <= 2:
        return "MODERATE"
    return "LOW"


def _risk_color(mismatches: int) -> str:
    if mismatches <= 1:
        return "danger"
    if mismatches <= 2:
        return "moderate"
    return "safe"


def _mock_genomic_site(grna: str, index: int, mismatches: int) -> Dict:
    digest = hashlib.md5(f"{grna}:{index}".encode()).hexdigest()
    chrom = int(digest[:2], 16) % 22 + 1
    pos = int(digest[2:10], 16) % 900_000_000 + 1_000_000
    return {
        "location": f"Chr{chrom}: {pos:,}",
        "mismatches": mismatches,
        "risk": _risk_label(mismatches),
        "risk_color": _risk_color(mismatches),
        "sequence_context": grna,
        "source": "heuristic_genome_proxy",
    }


def predict_off_targets(
    sequence: str,
    grna: str,
    pam_start: int,
    max_mismatches: int = 4,
    max_hits: int = 8,
) -> Dict:
    """
    Find similar 20-mer windows in the loaded sequence and attach illustrative
    off-target genomic coordinates for teaching / demo purposes.
    """
    seq = sequence.upper()
    guide = grna.upper()
    n = len(guide)
    if n == 0:
        return {"grna": grna, "off_target_count": 0, "sites": [], "overall_risk": "LOW"}

    in_sequence_hits: List[Dict] = []
    for i in range(max(0, len(seq) - n + 1)):
        if i == pam_start - n or abs(i - (pam_start - n)) < 3:
            continue
        window = seq[i: i + n]
        if len(window) < n:
            continue
        mm = _hamming(window, guide)
        if 0 < mm <= max_mismatches:
            in_sequence_hits.append({
                "location": f"In-sequence @ {i}",
                "mismatches": mm,
                "risk": _risk_label(mm),
                "risk_color": _risk_color(mm),
                "sequence_context": window,
                "source": "input_sequence",
            })

    in_sequence_hits.sort(key=lambda x: x["mismatches"])
    genomic = [
        _mock_genomic_site(guide, i, mm)
        for i, mm in enumerate([1, 2, 3][: max(0, 3 - len(in_sequence_hits))])
    ]

    sites = (in_sequence_hits + genomic)[:max_hits]
    count = len(sites)
    overall = "HIGH" if any(s["risk"] == "HIGH" for s in sites) else \
              "MODERATE" if any(s["risk"] == "MODERATE" for s in sites) else "LOW"

    return {
        "grna": guide,
        "off_target_count": count,
        "sites": sites,
        "overall_risk": overall,
        "overall_risk_color": _risk_color(1 if overall == "HIGH" else 2 if overall == "MODERATE" else 3),
    }
