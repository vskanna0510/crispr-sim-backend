"""Load gene and literature catalogs from PostgreSQL with in-code fallback."""

from __future__ import annotations

from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from db.base import SessionLocal
from db.models import Gene, LiteratureCase, ResearchPaper
from services.gene_info import GENE_CATALOG, DEFAULT_PUBLICATIONS, lookup_gene_info as _lookup_fallback
from services.literature_validation import LITERATURE_CASES, list_validation_cases as _cases_fallback


def _db() -> Session:
    return SessionLocal()


def lookup_gene_from_db(accession: Optional[str] = None, sequence_hint: Optional[str] = None) -> Dict:
    if not accession:
        return _lookup_fallback(accession, sequence_hint)

    acc = accession.upper().strip()
    root = acc.rsplit(".", 1)[0] if "." in acc else acc

    db = _db()
    try:
        row = (
            db.query(Gene)
            .filter(Gene.accession_root.in_([root, acc]))
            .first()
        )
        if not row:
            for g in db.query(Gene).all():
                if root.startswith(g.accession_root) or g.accession_root.startswith(root):
                    row = g
                    break
        if row:
            return {
                "accession": accession,
                "found": True,
                "gene_symbol": row.gene_symbol,
                "gene_name": row.gene_name,
                "chromosome": row.chromosome,
                "function": row.function,
                "associated_diseases": row.associated_diseases or [],
                "supporting_studies": row.supporting_studies or DEFAULT_PUBLICATIONS,
            }
    except Exception:
        pass
    finally:
        db.close()

    return _lookup_fallback(accession, sequence_hint)


def list_literature_cases_from_db() -> List[Dict]:
    db = _db()
    try:
        rows = db.query(LiteratureCase).order_by(LiteratureCase.id).all()
        if rows:
            return [
                {
                    "id": r.case_key,
                    "title": r.title,
                    "accession": r.accession,
                    "description": r.description,
                }
                for r in rows
            ]
    except Exception:
        pass
    finally:
        db.close()
    return _cases_fallback()


def get_literature_case_from_db(case_id: str) -> Optional[Dict]:
    db = _db()
    try:
        row = db.query(LiteratureCase).filter(LiteratureCase.case_key == case_id).first()
        if row:
            return {
                "id": row.case_key,
                "title": row.title,
                "accession": row.accession,
                "description": row.description,
                "literature": row.expected_outcomes,
                "demo_sequence_prefix": row.demo_sequence_prefix,
            }
    except Exception:
        pass
    finally:
        db.close()
    return LITERATURE_CASES.get(case_id)


def list_papers_for_gene(symbol: str) -> List[Dict]:
    db = _db()
    try:
        papers = db.query(ResearchPaper).all()
        sym = symbol.upper()
        return [
            {
                "pmid": p.pmid,
                "title": p.title,
                "authors": p.authors,
                "journal": p.journal,
                "year": p.year,
                "doi": p.doi,
                "url": p.url,
            }
            for p in papers
            if sym in (p.gene_symbols or []) or "GENERAL" in (p.gene_symbols or [])
        ]
    except Exception:
        return []
    finally:
        db.close()
