"""Multi-Cas system definitions: PAM patterns, gRNA length, cut geometry."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass(frozen=True)
class CasSystem:
    id: str
    name: str
    pam_motif: str
    pam_regex: re.Pattern
    grna_length: int
    cut_offset: int
    guide_upstream: bool
    target_molecule: str
    application: str
    description: str


CAS9 = CasSystem(
    id="cas9",
    name="Cas9 (SpCas9)",
    pam_motif="NGG",
    pam_regex=re.compile(r"(?=([ATCG]GG))"),
    grna_length=20,
    cut_offset=3,
    guide_upstream=True,
    target_molecule="DNA",
    application="Standard DNA double-strand break editing",
    description="Most widely used nuclease; requires NGG PAM on the target strand.",
)

CAS12A = CasSystem(
    id="cas12a",
    name="Cas12a (Cpf1)",
    pam_motif="TTTV",
    pam_regex=re.compile(r"(?=(TTT[ACG]))"),
    grna_length=23,
    cut_offset=18,
    guide_upstream=False,
    target_molecule="DNA",
    application="Alternative DNA editing with staggered cut and T-rich PAM",
    description="Creates staggered cuts; PAM is TTTV and the guide lies downstream of the PAM.",
)

CAS13 = CasSystem(
    id="cas13",
    name="Cas13",
    pam_motif="Poly-U / RNA target",
    pam_regex=re.compile(r"(?=(TTTT+))"),
    grna_length=22,
    cut_offset=0,
    guide_upstream=True,
    target_molecule="RNA",
    application="RNA knockdown, diagnostics, and transcript editing",
    description="Targets RNA rather than DNA; simulated here using U-rich motifs as proxy sites.",
)

CAS_REGISTRY: Dict[str, CasSystem] = {
    s.id: s for s in (CAS9, CAS12A, CAS13)
}


def get_cas_system(cas_type: str) -> CasSystem:
    key = (cas_type or "cas9").lower().strip()
    if key not in CAS_REGISTRY:
        raise ValueError(f"Unknown Cas system '{cas_type}'. Choose: {', '.join(CAS_REGISTRY)}")
    return CAS_REGISTRY[key]


def scan_pam_for_cas(sequence: str, cas: CasSystem) -> List[Dict]:
    sequence = sequence.upper()
    results = []
    for match in cas.pam_regex.finditer(sequence):
        start = match.start()
        pam = match.group(1)
        results.append({
            "pam": pam,
            "start": start,
            "end": start + len(pam),
            "cas_type": cas.id,
        })
    return results


def extract_grna_for_cas(sequence: str, pam_start: int, pam_end: int, cas: CasSystem) -> Optional[Dict]:
    from services.grna_generator import calculate_gc, GC_MIN, GC_MAX

    seq = sequence.upper()
    if cas.guide_upstream:
        if pam_start < cas.grna_length:
            return None
        grna = seq[pam_start - cas.grna_length: pam_start]
    else:
        if pam_end + cas.grna_length > len(seq):
            return None
        grna = seq[pam_end: pam_end + cas.grna_length]

    gc = calculate_gc(grna)
    return {
        "grna": grna,
        "gc_percent": gc,
        "recommended": GC_MIN <= gc <= GC_MAX,
        "pam_start": pam_start,
        "length": cas.grna_length,
    }
