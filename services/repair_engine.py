"""DNA repair simulation service.

Two pathways modelled:

NHEJ – Non-Homologous End Joining
    Error-prone mechanism; introduces small insertions/deletions (indels)
    at the cut site, usually disrupting the open reading frame.

HDR  – Homology-Directed Repair
    Precise repair using a provided donor template; models intended gene
    correction or knock-in experiments.
"""

import random
from typing import Dict, Optional


def nhej_repair(
    sequence: str,
    cut_position: int,
    deletion_size: Optional[int] = None,
) -> Dict:
    """
    Simulate NHEJ by deleting *deletion_size* bases at the cut site.

    If *deletion_size* is None a random value between 1 and 4 is chosen,
    mimicking the stochastic nature of cellular NHEJ.

    Args:
        sequence:      Full DNA string.
        cut_position:  0-based index of the DSB.
        deletion_size: Number of bases to delete (1–10).

    Returns:
        RepairResponse-compatible dict.
    """
    if deletion_size is None:
        deletion_size = random.randint(1, 4)

    deletion_size = max(1, min(deletion_size, len(sequence) - cut_position))

    repaired = sequence[:cut_position] + sequence[cut_position + deletion_size:]

    return {
        "repaired_sequence": repaired,
        "repair_type":       "NHEJ",
        "cut_position":      cut_position,
        "deletion_size":     deletion_size,
        "donor_template":    None,
        "original_length":   len(sequence),
        "repaired_length":   len(repaired),
    }


def hdr_repair(
    sequence: str,
    cut_position: int,
    donor_template: str,
    replacement_length: int = 0,
) -> Dict:
    """
    Simulate HDR by inserting *donor_template* at the cut site,
    optionally replacing *replacement_length* bases of the original.

    Args:
        sequence:           Full DNA string.
        cut_position:       0-based index of the DSB.
        donor_template:     Donor sequence to insert.
        replacement_length: Bases of the original to replace (default 0 = pure insertion).

    Returns:
        RepairResponse-compatible dict.
    """
    donor_template = donor_template.upper()
    replacement_length = max(0, min(replacement_length, len(sequence) - cut_position))

    repaired = (
        sequence[:cut_position]
        + donor_template
        + sequence[cut_position + replacement_length:]
    )

    return {
        "repaired_sequence": repaired,
        "repair_type":       "HDR",
        "cut_position":      cut_position,
        "deletion_size":     None,
        "donor_template":    donor_template,
        "original_length":   len(sequence),
        "repaired_length":   len(repaired),
    }
