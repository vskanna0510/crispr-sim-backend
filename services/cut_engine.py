"""Cas9 double-strand break (DSB) simulation — supports Cas9, Cas12a, Cas13 proxy."""

from typing import Dict, Optional

from services.cas_systems import get_cas_system


def simulate_cut(
    sequence: str,
    pam_start: int,
    cas_type: str = "cas9",
    pam_end: Optional[int] = None,
) -> Dict:
    cas = get_cas_system(cas_type)
    if cas.target_molecule == "RNA":
        cut_position = pam_start
    elif cas.guide_upstream:
        cut_position = max(0, pam_start - cas.cut_offset)
    else:
        end = pam_end if pam_end is not None else pam_start + len(cas.pam_motif.replace("V", "A"))
        cut_position = min(len(sequence), end + cas.cut_offset)

    return {
        "cut_position": cut_position,
        "upstream":     sequence[:cut_position],
        "downstream":   sequence[cut_position:],
        "pam_start":    pam_start,
        "sequence":     sequence,
        "cas_type":     cas.id,
        "cas_name":     cas.name,
    }
