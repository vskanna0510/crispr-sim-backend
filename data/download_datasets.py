"""
Dataset downloader for CRISPR-Sim.

Downloads real genomic sequences from NCBI E-Utils and saves them as
FASTA files in the datasets/ directory.

Usage:
    cd crispr_sim/backend
    python data/download_datasets.py

Requires:
    pip install httpx biopython
"""

import asyncio
import io
import sys
from pathlib import Path

import httpx
from Bio import SeqIO

DATASETS_DIR = Path(__file__).parent / "datasets"
EFETCH_URL   = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

# ─── Target sequences ─────────────────────────────────────────────────────────
# (accession, filename, human-readable label)
TARGETS = [
    ("NM_000518.5", "hbb_NM000518.fasta",   "Homo sapiens HBB (hemoglobin beta) mRNA"),
    ("NM_000546.6", "tp53_NM000546.fasta",   "Homo sapiens TP53 (tumor protein p53) mRNA"),
    ("NM_007294.4", "brca1_NM007294.fasta",  "Homo sapiens BRCA1 DNA repair mRNA"),
]

# ─── Synthetic samples (always written, no internet required) ─────────────────
SYNTHETIC = [
    {
        "id":          "SYNTH_HBB_FRAGMENT",
        "description": "Synthetic HBB fragment with NGG PAM sites for CRISPR-Sim demo",
        "sequence": (
            "ATGGTGCACCTGACTCCTGAGGAGAAGTCTGCCGTTACTGCCCTGTGGGGCAAGGTGAACGTGGATGAA"
            "GTTGGTGGTGAGGCCCTGGGCAGGCTGCTGGTGGTCTACCCTTGGACCCAGAGGTTCTTTGAGTCCTT"
            "TGGGGATCTGTCCACTCCTGATGCTGTTATGGGCAACCCTAAGGTGAAGGCTCATGGCAAGAAAGTGCT"
            "CGGTGCCTTTAGTGATGGCCTGGCTCACCTGGACAACCTCAAGGGCACCTTTGCCACACTGAGTGAGCT"
            "GCACTGTGACAAGCTGCACGTGGATCCTGAGAACTTCAGG"
        ),
        "filename": "synth_hbb_fragment.fasta",
    },
    {
        "id":          "SYNTH_TP53_FRAGMENT",
        "description": "Synthetic TP53 fragment with NGG PAM sites for CRISPR-Sim demo",
        "sequence": (
            "ATGGAGGAGCCGCAGTCAGATCCTAGCGTTGAATCAGAGGCCTGAGTCAGTTCAGAGGAAGCTGTGTC"
            "CTGTGGCACCACCGCCCTGCACCAGCCCCAGCCCAGGTCTCTCTCCCAGCCAAAGAAGAAACCACTGGA"
            "TGGAGAATATTTCACCCTTCAGATCCGTGGGCGTGAGCGCTTCGAGATGTTCCGAGAGCTGAATGAGGC"
            "CTTGGAACTCAAGCCGTCTCAGGAAGGAAATTTGCGTGTGGAGTATTTGGATGACAGAAACACT"
        ),
        "filename": "synth_tp53_fragment.fasta",
    },
    {
        "id":          "SYNTH_BRCA1_FRAGMENT",
        "description": "Synthetic BRCA1 fragment with NGG PAM sites for CRISPR-Sim demo",
        "sequence": (
            "ATGGATTTATCTGCTCTTCGCGTTGAAGAAGTACAAAATGTCATTAATGCTATGCAGAAAATCTTAGA"
            "GTGTCCCATCTGTCTGGAGTTGATCAAGGAACCTGTCTCCACAAAGTGTGACCACATATTTTGCAAATT"
            "TTGCATGCTGAAACTTCTCAACCAGAAGAAAGGGCCTTCACAGTGTCCTTTATGTAAGAATGATATAAC"
            "CAAAAGCAGCAGAAATCCCACCTCAGCAGCAGATACTGCAGAGCAGAGGATGGTCAGCAGTTCGGAGGG"
        ),
        "filename": "synth_brca1_fragment.fasta",
    },
    {
        "id":          "SYNTH_DEMO_SHORT",
        "description": "Short 120-bp demo sequence – ideal for quick CRISPR-Sim walkthroughs",
        "sequence": (
            "ATGCATGCATGCATGCATGCATGCATGCATGCAGGATGCATGCATGCATGCATGCATGCATGCAGGAT"
            "GCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCAGG"
        ),
        "filename": "synth_demo_short.fasta",
    },
]


def write_fasta(path: Path, seq_id: str, description: str, sequence: str) -> None:
    with open(path, "w") as fh:
        fh.write(f">{seq_id} {description}\n")
        for i in range(0, len(sequence), 70):
            fh.write(sequence[i: i + 70] + "\n")
    print(f"  ✔ Wrote {path.name}  ({len(sequence)} bp)")


async def download_ncbi(accession: str, filename: str, label: str) -> bool:
    out_path = DATASETS_DIR / filename
    if out_path.exists():
        print(f"  ↷ {filename} already exists – skipping download.")
        return True

    params = {
        "db": "nucleotide", "id": accession,
        "rettype": "fasta", "retmode": "text",
    }
    print(f"  ⬇ Downloading {label} ({accession}) …")
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.get(EFETCH_URL, params=params)
            r.raise_for_status()
        records = list(SeqIO.parse(io.StringIO(r.text), "fasta"))
        if not records:
            print(f"  ✘ No records returned for {accession}")
            return False
        rec = records[0]
        write_fasta(out_path, rec.id, rec.description, str(rec.seq).upper())
        return True
    except Exception as exc:
        print(f"  ✘ Failed ({exc}). Falling back to synthetic sample.")
        return False


async def main() -> None:
    DATASETS_DIR.mkdir(parents=True, exist_ok=True)
    print("\n=== CRISPR-Sim Dataset Downloader ===\n")

    # 1. Write synthetic samples (no internet required)
    print("Writing synthetic sample sequences …")
    for s in SYNTHETIC:
        write_fasta(
            DATASETS_DIR / s["filename"],
            s["id"], s["description"], s["sequence"],
        )

    # 2. Attempt real NCBI downloads
    print("\nDownloading from NCBI (requires internet) …")
    for accession, filename, label in TARGETS:
        await download_ncbi(accession, filename, label)

    print("\nDone. Datasets available in:", DATASETS_DIR)


if __name__ == "__main__":
    asyncio.run(main())
