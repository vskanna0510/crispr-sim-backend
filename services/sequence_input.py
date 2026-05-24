"""Sequence input handlers: paste, FASTA parse, NCBI E-Utils fetch."""

import io
from typing import Optional

import httpx
from Bio import SeqIO

NCBI_EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
NCBI_TIMEOUT = 20.0  # seconds


def parse_fasta_content(text: str) -> Optional[str]:
    """
    Parse the first record from a FASTA-formatted string.

    Returns the sequence string, or None if parsing fails.
    """
    try:
        handle = io.StringIO(text)
        records = list(SeqIO.parse(handle, "fasta"))
        if records:
            return str(records[0].seq).upper()
    except Exception:
        pass
    return None


async def fetch_from_ncbi(accession_id: str) -> Optional[dict]:
    """
    Retrieve a nucleotide sequence from NCBI via E-Utils.

    Args:
        accession_id: NCBI accession (e.g. 'NM_000518.5').

    Returns:
        {"sequence": str, "description": str} or None on failure.
    """
    params = {
        "db":      "nucleotide",
        "id":      accession_id,
        "rettype": "fasta",
        "retmode": "text",
    }
    try:
        async with httpx.AsyncClient(timeout=NCBI_TIMEOUT) as client:
            response = await client.get(NCBI_EFETCH_URL, params=params)
            response.raise_for_status()
            text = response.text

        handle = io.StringIO(text)
        records = list(SeqIO.parse(handle, "fasta"))
        if not records:
            return None

        record = records[0]
        return {
            "sequence":    str(record.seq).upper(),
            "description": record.description,
            "accession":   accession_id,
        }
    except Exception:
        return None
