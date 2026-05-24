"""DNA → mRNA → Protein translation service using BioPython."""

from Bio.Seq import Seq
from typing import Dict


def translate_sequence(dna: str) -> Dict:
    """
    Transcribe and translate a DNA sequence.

    The sequence is trimmed to the nearest codon boundary before translation
    so BioPython does not raise a partial-codon warning.

    Returns:
        {
            "dna":           str – original (untrimmed) input,
            "mrna":          str – transcribed mRNA,
            "protein":       str – translated amino-acid string (stop = '*'),
            "codon_count":   int,
            "trimmed_length":int,
        }
    """
    dna = dna.upper()
    remainder = len(dna) % 3
    trimmed = dna[: len(dna) - remainder] if remainder else dna

    seq = Seq(trimmed)
    mrna = str(seq.transcribe())
    protein = str(seq.translate())

    return {
        "dna":            dna,
        "mrna":           mrna,
        "protein":        protein,
        "codon_count":    len(trimmed) // 3,
        "trimmed_length": len(trimmed),
    }
