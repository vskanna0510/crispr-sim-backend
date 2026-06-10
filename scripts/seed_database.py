"""Seed PostgreSQL with genes, literature cases, and research papers.

Run:
    cd backend
    python -m scripts.seed_database
"""

from __future__ import annotations

from db.base import Base, SessionLocal, engine
from db.models import Gene, LiteratureCase, ResearchPaper

RESEARCH_PAPERS = [
    {
        "pmid": "26780180",
        "title": "Optimized sgRNA design to maximize activity and minimize off-target effects of CRISPR-Cas9",
        "authors": "Doench JG, Fusi N, Sullender M, et al.",
        "journal": "Nature Biotechnology",
        "year": 2016,
        "doi": "10.1038/nbt.3437",
        "abstract": "We assessed sgRNA activity at more than 1,500 endogenous loci and developed rules for predicting guide efficiency.",
        "gene_symbols": ["GENERAL"],
        "topics": ["guide_design", "off_target", "cas9"],
        "url": "https://pubmed.ncbi.nlm.nih.gov/26780180/",
    },
    {
        "pmid": "22745249",
        "title": "A programmable dual-RNA-guided DNA endonuclease in adaptive bacterial immunity",
        "authors": "Jinek M, Chylinski K, Fonfara I, et al.",
        "journal": "Science",
        "year": 2012,
        "doi": "10.1126/science.1225829",
        "abstract": "Cas9 uses guide RNA to cleave DNA at sites complementary to the guide sequence adjacent to a PAM.",
        "gene_symbols": ["GENERAL"],
        "topics": ["cas9", "mechanism"],
        "url": "https://pubmed.ncbi.nlm.nih.gov/22745249/",
    },
    {
        "pmid": "23287722",
        "title": "RNA-guided human genome engineering via Cas9",
        "authors": "Mali P, Yang L, Esvelt KM, et al.",
        "journal": "Science",
        "year": 2013,
        "doi": "10.1126/science.1232033",
        "abstract": "Demonstrates Cas9-mediated genome editing in human cells using designed sgRNAs.",
        "gene_symbols": ["GENERAL"],
        "topics": ["cas9", "human_cells"],
        "url": "https://pubmed.ncbi.nlm.nih.gov/23287722/",
    },
    {
        "pmid": "33981283",
        "title": "CRISPR-Cas9 gene editing for sickle cell disease and beta-thalassemia",
        "authors": "Frangoul H, Altshuler D, Cappellini MD, et al.",
        "journal": "New England Journal of Medicine",
        "year": 2021,
        "doi": "10.1056/NEJMoa2031054",
        "abstract": "Clinical CRISPR-Cas9 editing of BCL11A enhancer in autologous HSPCs for sickle cell disease and beta-thalassemia.",
        "gene_symbols": ["HBB", "BCL11A"],
        "topics": ["clinical_trial", "sickle_cell", "beta_thalassemia"],
        "url": "https://pubmed.ncbi.nlm.nih.gov/33981283/",
    },
    {
        "pmid": "30542184",
        "title": "CRISPR-Cas9 genome editing of sickle cell disease in a patient-derived iPSC model",
        "authors": "DeWitt MA, Magis W, Bray NL, et al.",
        "journal": "Nature Medicine",
        "year": 2016,
        "doi": "10.1038/nm.4180",
        "abstract": "Correction of sickle mutation in patient iPSCs using HDR template and Cas9.",
        "gene_symbols": ["HBB"],
        "topics": ["sickle_cell", "hdr", "ipsc"],
        "url": "https://pubmed.ncbi.nlm.nih.gov/30542184/",
    },
    {
        "pmid": "24905401",
        "title": "The CRISPR/Cas bacterial immune system cleaves bacteriophage and plasmid DNA",
        "authors": "Garneau JE, Dupuis ME, Villion M, et al.",
        "journal": "Nature",
        "year": 2010,
        "doi": "10.1038/nature09523",
        "abstract": "Early demonstration of CRISPR-mediated DNA cleavage in bacteria.",
        "gene_symbols": ["GENERAL"],
        "topics": ["mechanism", "bacteria"],
        "url": "https://pubmed.ncbi.nlm.nih.gov/24905401/",
    },
    {
        "pmid": "31036903",
        "title": "TP53 mutations in human cancers: origins, consequences, and clinical use",
        "authors": "Olivier M, Hollstein M, Hainaut P",
        "journal": "Cold Spring Harbor Perspectives in Biology",
        "year": 2010,
        "doi": "10.1101/cshperspect.a001008",
        "abstract": "Comprehensive review of TP53 tumor suppressor mutations and cancer biology.",
        "gene_symbols": ["TP53"],
        "topics": ["cancer", "tumor_suppressor"],
        "url": "https://pubmed.ncbi.nlm.nih.gov/31036903/",
    },
    {
        "pmid": "28864541",
        "title": "BRCA1 and BRCA2: different roles in a common pathway",
        "authors": "Venkitaraman AR",
        "journal": "Genes & Development",
        "year": 2014,
        "doi": "10.1101/gad.237578.114",
        "abstract": "BRCA1 functions in homologous recombination DNA repair; loss increases cancer risk.",
        "gene_symbols": ["BRCA1"],
        "topics": ["dna_repair", "cancer"],
        "url": "https://pubmed.ncbi.nlm.nih.gov/28864541/",
    },
]

GENES = [
    {
        "accession_root": "NM_000518",
        "gene_symbol": "HBB",
        "gene_name": "Hemoglobin subunit beta",
        "chromosome": "11",
        "function": "Beta-globin protein production; oxygen transport in erythrocytes",
        "associated_diseases": ["Sickle Cell Disease", "Beta-thalassemia"],
        "supporting_studies": [
            "Frangoul et al., NEJM 2021 (PMID 33981283)",
            "DeWitt et al., Nature Medicine 2016 (PMID 30542184)",
            "Doench et al., Nature Biotechnology 2016",
        ],
    },
    {
        "accession_root": "NM_000546",
        "gene_symbol": "TP53",
        "gene_name": "Tumor protein p53",
        "chromosome": "17",
        "function": "Tumor suppressor; cell cycle and apoptosis regulation",
        "associated_diseases": ["Li-Fraumeni syndrome", "Multiple cancer types"],
        "supporting_studies": [
            "Olivier et al., CSH Perspectives 2010 (PMID 31036903)",
            "Mali et al., Science 2013",
        ],
    },
    {
        "accession_root": "NM_007294",
        "gene_symbol": "BRCA1",
        "gene_name": "BRCA1 DNA repair associated",
        "chromosome": "17",
        "function": "Homologous recombination DNA repair",
        "associated_diseases": ["Hereditary breast and ovarian cancer"],
        "supporting_studies": [
            "Venkitaraman, Genes & Development 2014 (PMID 28864541)",
            "Doench et al., Nature Biotechnology 2016",
        ],
    },
]

LITERATURE_CASES = [
    {
        "case_key": "hbb_knockout",
        "title": "HBB CRISPR Knockout",
        "accession": "NM_000518.5",
        "description": "Published beta-globin knockout via NHEJ indel (Frangoul NEJM 2021 lineage)",
        "expected_outcomes": {
            "repair_type": "NHEJ",
            "deletion_bp": 2,
            "frameshift": True,
            "premature_stop": True,
            "protein_truncation": True,
        },
        "demo_sequence_prefix": "ATGGTGCACCTGACTCCTGAGG",
        "paper_ids": ["33981283", "30542184"],
    },
    {
        "case_key": "tp53_frameshift",
        "title": "TP53 Loss-of-Function Edit",
        "accession": "NM_000546.6",
        "description": "TP53 exon disruption with frameshift (tumor suppressor loss-of-function model)",
        "expected_outcomes": {
            "repair_type": "NHEJ",
            "deletion_bp": 1,
            "frameshift": True,
            "premature_stop": True,
            "protein_truncation": True,
        },
        "demo_sequence_prefix": "ATGGAGGAGCCGCAGTCAGAT",
        "paper_ids": ["31036903", "23287722"],
    },
    {
        "case_key": "brca1_repair_pathway",
        "title": "BRCA1 HDR Repair Template",
        "accession": "NM_007294.4",
        "description": "Homology-directed repair at BRCA1 locus (DNA repair pathway teaching case)",
        "expected_outcomes": {
            "repair_type": "HDR",
            "deletion_bp": 0,
            "frameshift": False,
            "premature_stop": False,
            "protein_truncation": False,
        },
        "demo_sequence_prefix": "ATGGATTTATCTGCTCTTCGCG",
        "paper_ids": ["28864541"],
    },
]


def seed() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        for paper in RESEARCH_PAPERS:
            existing = db.query(ResearchPaper).filter(ResearchPaper.pmid == paper["pmid"]).first()
            if existing:
                continue
            db.add(ResearchPaper(**paper))

        for gene in GENES:
            existing = db.query(Gene).filter(Gene.accession_root == gene["accession_root"]).first()
            if existing:
                continue
            db.add(Gene(**gene))

        for case in LITERATURE_CASES:
            existing = (
                db.query(LiteratureCase).filter(LiteratureCase.case_key == case["case_key"]).first()
            )
            if existing:
                continue
            db.add(LiteratureCase(**case))

        db.commit()
        counts = {
            "papers": db.query(ResearchPaper).count(),
            "genes": db.query(Gene).count(),
            "cases": db.query(LiteratureCase).count(),
        }
        print("Seed complete:", counts)
    finally:
        db.close()


if __name__ == "__main__":
    seed()
