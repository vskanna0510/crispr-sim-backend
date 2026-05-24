"""PAM site scanning service.

SpCas9 recognises the NGG PAM motif on the non-template strand.
Pattern: [ATCG]GG  (covers AGG, TGG, CGG, GGG)
"""

import re
from typing import List, Dict


PAM_PATTERN = re.compile(r"(?=([ATCG]GG))")


def scan_pam_sites(sequence: str) -> List[Dict]:
    """
    Slide the PAM regex across the full sequence and return every match.

    Returns a list of dicts:
        {
            "pam":   str   – the 3-char NGG motif,
            "start": int   – 0-based index of the N in NGG,
            "end":   int   – exclusive end (start + 3),
        }
    """
    sequence = sequence.upper()
    results = []
    for match in PAM_PATTERN.finditer(sequence):
        start = match.start()
        results.append({
            "pam":   match.group(1),
            "start": start,
            "end":   start + 3,
        })
    return results
