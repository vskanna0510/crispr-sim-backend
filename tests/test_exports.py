import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

SAMPLE_ANALYSIS = {
    "summary": "NHEJ repair resulted in a 7 bp deletion with frameshift disruption.",
    "repair_type": "NHEJ",
    "safety_score": 62,
    "safety_label": "Moderate",
    "frameshift": True,
    "premature_stop": True,
    "original_length": 276,
    "edited_length": 269,
    "length_diff": 7,
    "original_dna": "ATGGTGCACCTGACTCCTGAGGAGAAGTCTGCCGTTACTGCCCTGTGG",
    "edited_dna": "ATGGTGCACCTGACTCCTGAGGAGAAGTCTGCCGTTACTGG",
    "original_protein": "MVHLTPEEKSAVTALWGKVNVDEVGGEALGRLLVVYPWTQRFFESFGDLSTPDAVMGNPK",
    "edited_protein": "MVHLTPEEKSAVTG*TWMKLVVRPWAGCWVVSTLGPRGSLSSLGIQLLMLLWATLR",
    "original_mrna": "AUGGUGCACCUGACUCCUGAGGAGAAGUCUGCCGUUACUGCCCUGUGGG",
    "edited_mrna": "AUGGUGCACCUGACUCCUGAGGAGAAGUCUGCCGUUACUGG",
}


def test_export_pdf():
    response = client.post("/analysis/export/pdf", json=SAMPLE_ANALYSIS)
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF")


def test_export_excel():
    response = client.post("/analysis/export/excel", json=SAMPLE_ANALYSIS)
    assert response.status_code == 200
    assert "openxmlformats-officedocument.spreadsheetml.sheet" in response.headers["content-type"]
    assert len(response.content) > 1000


def test_export_csv():
    response = client.post("/analysis/export/csv", json=SAMPLE_ANALYSIS)
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    assert "Metric,Value" in response.text
    assert "NHEJ" in response.text


def test_export_fasta():
    response = client.post("/analysis/export/fasta", json=SAMPLE_ANALYSIS)
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/plain; charset=utf-8"
    assert ">CRISPR_Sim|Original_DNA" in response.text
    assert ">CRISPR_Sim|Edited_Protein_NHEJ" in response.text
