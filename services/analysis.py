"""Mutation analysis service: compare original vs edited sequences."""

from .translation import translate_sequence
from typing import Dict


def compare_sequences(original: str, edited: str) -> Dict:
    """
    Translate both sequences and analyse mutation effects.

    Detects:
    - Frameshift mutation: indel length not divisible by 3.
    - Premature stop codon: '*' appears earlier in the edited protein
      than in the original protein.

    Returns a CompareResponse-compatible dict.
    """
    orig_t = translate_sequence(original)
    edit_t = translate_sequence(edited)

    orig_protein = orig_t["protein"]
    edit_protein = edit_t["protein"]

    length_diff = len(original) - len(edited)
    frameshift = (length_diff % 3) != 0

    # Locate stop codons
    orig_stop = orig_protein.find("*")
    edit_stop = edit_protein.find("*")

    if orig_stop == -1:
        # Original has no stop codon within the fragment
        premature_stop = (edit_stop != -1) and (edit_stop < len(orig_protein) - 1)
    else:
        premature_stop = (edit_stop != -1) and (edit_stop < orig_stop)

    # Human-readable summary
    issues = []
    if frameshift:
        issues.append("frameshift mutation")
    if premature_stop:
        issues.append("premature stop codon")
    summary = ("Detected: " + ", ".join(issues) + ".") if issues else "No major mutations detected."

    return {
        "original_protein": orig_protein,
        "edited_protein":   edit_protein,
        "original_mrna":    orig_t["mrna"],
        "edited_mrna":      edit_t["mrna"],
        "frameshift":       frameshift,
        "premature_stop":   premature_stop,
        "length_diff":      length_diff,
        "original_length":  len(original),
        "edited_length":    len(edited),
        "summary":          summary,
    }
