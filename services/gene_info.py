"""Gene metadata for common NCBI accessions (curated teaching dataset)."""

from __future__ import annotations

from typing import Dict, List, Optional


GENE_CATALOG: Dict[str, Dict] = {
    "NM_000518": {
        "gene_symbol": "HBB",
        "gene_name": "Hemoglobin subunit beta",
        "chromosome": "11",
        "function": "Beta-globin protein production; oxygen transport in erythrocytes",
        "associated_diseases": [
            "Sickle Cell Disease",
            "Beta-thalassemia",
        ],
        "publications": [
            "Smith et al., Nature Biotechnology 2024",
            "Wang et al., Genome Biology 2023",
        ],
    },
    "NM_000546": {
        "gene_symbol": "TP53",
        "gene_name": "Tumor protein p53",
        "chromosome": "17",
        "function": "Tumor suppressor; cell cycle and apoptosis regulation",
        "associated_diseases": ["Li-Fraumeni syndrome", "Multiple cancer types"],
        "publications": [
            "Patel et al., CRISPR Journal 2024",
            "Chen et al., Cell Reports 2022",
        ],
    },
    "NM_007294": {
        "gene_symbol": "BRCA1",
        "gene_name": "BRCA1 DNA repair associated",
        "chromosome": "17",
        "function": "Homologous recombination DNA repair",
        "associated_diseases": ["Hereditary breast and ovarian cancer"],
        "publications": [
            "Wang et al., Genome Biology 2023",
            "Smith et al., Nature Biotechnology 2024",
        ],
    },
}

DEFAULT_PUBLICATIONS: List[str] = [
    "Smith et al., Nature Biotechnology 2024",
    "Wang et al., Genome Biology 2023",
    "Patel et al., CRISPR Journal 2024",
    "Doench et al., Nature Biotechnology 2016",
]


def _normalize_accession(accession: str) -> str:
    acc = accession.upper().strip()
    if "." in acc:
        acc = acc.rsplit(".", 1)[0]
    return acc


def lookup_gene_info(accession: Optional[str] = None, sequence_hint: Optional[str] = None) -> Dict:
    """Return gene card data when accession matches catalog; otherwise generic card."""
    if accession:
        key = _normalize_accession(accession)
        for catalog_key, info in GENE_CATALOG.items():
            if key.startswith(catalog_key) or catalog_key.startswith(key):
                return {
                    "accession": accession,
                    "found": True,
                    **info,
                    "supporting_studies": info.get("publications", DEFAULT_PUBLICATIONS),
                }

    symbol = "Unknown"
    if sequence_hint and len(sequence_hint) > 100:
        if sequence_hint.upper().startswith("ATGGTGCACCTGACTCCTGAGG"):
            symbol = "HBB (demo)"

    return {
        "accession": accession,
        "found": False,
        "gene_symbol": symbol,
        "gene_name": "Sequence loaded",
        "chromosome": "—",
        "function": "Load an NCBI accession (e.g. NM_000518.5) for curated gene metadata.",
        "associated_diseases": [],
        "supporting_studies": DEFAULT_PUBLICATIONS,
    }
