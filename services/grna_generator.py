"""Guide RNA (gRNA) extraction and scoring service.

SpCas9 gRNA = 20 nucleotides immediately upstream of the PAM site.
GC content between 40–60 % is considered optimal for stability.
"""

from typing import Optional, Dict


GRNA_LENGTH = 20
GC_MIN = 40.0
GC_MAX = 60.0


def calculate_gc(sequence: str) -> float:
    """Return GC percentage (0–100) for a nucleotide string."""
    if not sequence:
        return 0.0
    g_c = sequence.count("G") + sequence.count("C")
    return round(g_c / len(sequence) * 100, 2)


def extract_grna(sequence: str, pam_start: int) -> Optional[Dict]:
    """
    Extract the 20-nt gRNA upstream of *pam_start*.

    Returns None if the PAM is too close to the sequence start.
    """
    if pam_start < GRNA_LENGTH:
        return None

    grna = sequence[pam_start - GRNA_LENGTH: pam_start]
    gc = calculate_gc(grna)

    return {
        "grna":        grna,
        "gc_percent":  gc,
        "recommended": GC_MIN <= gc <= GC_MAX,
        "pam_start":   pam_start,
        "length":      GRNA_LENGTH,
    }


def enrich_pam_sites(sequence: str, pam_sites: list) -> list:
    """
    Attach gRNA info to every PAM site that has enough upstream context.

    Modifies each dict in-place and returns the enriched list.
    """
    enriched = []
    for site in pam_sites:
        info = extract_grna(sequence, site["start"])
        entry = dict(site)
        if info:
            entry.update({
                "grna":        info["grna"],
                "gc_percent":  info["gc_percent"],
                "recommended": info["recommended"],
            })
        else:
            entry.update({"grna": None, "gc_percent": None, "recommended": None})
        enriched.append(entry)
    return enriched
