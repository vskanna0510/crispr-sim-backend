"""DNA sequence validation service."""

import re


VALID_BASES = frozenset("ATCG")


def validate_and_clean(sequence: str) -> dict:
    """
    Strip whitespace/newlines, uppercase, then check for non-ATCG characters.

    Returns:
        {
          "valid": bool,
          "cleaned": str | None,
          "errors": list[str],
          "gc_percent": float | None,
          "composition": dict | None,
        }
    """
    cleaned = sequence.upper().replace("\n", "").replace("\r", "").replace(" ", "")

    invalid_chars = sorted(set(re.findall(r"[^ATCG]", cleaned)))

    if invalid_chars:
        return {
            "valid": False,
            "cleaned": None,
            "errors": invalid_chars,
            "gc_percent": None,
            "composition": None,
        }

    length = len(cleaned)
    if length == 0:
        return {
            "valid": False,
            "cleaned": None,
            "errors": ["Sequence is empty"],
            "gc_percent": None,
            "composition": None,
        }

    gc_percent = (cleaned.count("G") + cleaned.count("C")) / length * 100
    composition = {
        "A": round(cleaned.count("A") / length * 100, 2),
        "T": round(cleaned.count("T") / length * 100, 2),
        "G": round(cleaned.count("G") / length * 100, 2),
        "C": round(cleaned.count("C") / length * 100, 2),
    }

    return {
        "valid": True,
        "cleaned": cleaned,
        "errors": [],
        "gc_percent": round(gc_percent, 2),
        "composition": composition,
    }
