"""
Lightweight RAG over local Markdown knowledge files.

Retrieval: Okapi BM25 across chunked documents.
Generation: If OPENAI_API_KEY is set, calls OpenAI chat with retrieved context;
otherwise composes an answer from the top chunks only.
"""

from __future__ import annotations

import math
import os
import re
from pathlib import Path
from typing import List, Tuple

import httpx
from pydantic import BaseModel

KNOWLEDGE_DIR = Path(__file__).resolve().parent.parent / "knowledge"


class DocumentChunk(BaseModel):
    doc_id: str
    text: str
    tokens: List[str]


def _tokenize(text: str) -> List[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def _load_chunks() -> List[DocumentChunk]:
    chunks: List[DocumentChunk] = []
    if not KNOWLEDGE_DIR.is_dir():
        return chunks
    for path in sorted(KNOWLEDGE_DIR.glob("*.md")):
        raw = path.read_text(encoding="utf-8")
        parts = re.split(r"\n(?=#+ |\n\n)", raw)
        for i, part in enumerate(parts):
            part = part.strip()
            if len(part) < 40:
                continue
            toks = _tokenize(part)
            if len(toks) < 6:
                continue
            doc_id = f"{path.stem}:{i}"
            chunks.append(DocumentChunk(doc_id=doc_id, text=part, tokens=toks))
    return chunks


_CHUNKS: List[DocumentChunk] | None = None
_DF: dict[str, int] | None = None
_N_DOCS = 0


def _ensure_index() -> None:
    global _CHUNKS, _DF, _N_DOCS
    if _CHUNKS is None:
        _CHUNKS = _load_chunks()
        df: dict[str, int] = {}
        for ch in _CHUNKS:
            seen = set(ch.tokens)
            for t in seen:
                df[t] = df.get(t, 0) + 1
        _DF = df
        _N_DOCS = max(len(_CHUNKS), 1)


def _bm25_scores(query: str, k1: float = 1.5, b: float = 0.75) -> List[Tuple[int, float]]:
    _ensure_index()
    assert _CHUNKS is not None and _DF is not None
    q_tokens = _tokenize(query)
    if not q_tokens:
        return []
    scores = [0.0] * len(_CHUNKS)
    avgdl = sum(len(c.tokens) for c in _CHUNKS) / _N_DOCS
    for i, ch in enumerate(_CHUNKS):
        dl = len(ch.tokens)
        tf: dict[str, int] = {}
        for t in ch.tokens:
            tf[t] = tf.get(t, 0) + 1
        score = 0.0
        for qt in q_tokens:
            n_qt = _DF.get(qt, 0)
            idf = math.log(1 + (_N_DOCS - n_qt + 0.5) / (n_qt + 0.5))
            f = tf.get(qt, 0)
            denom = f + k1 * (1 - b + b * dl / avgdl)
            score += idf * (f * (k1 + 1)) / denom if denom else 0.0
        scores[i] = score
    ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
    return ranked


def retrieve(query: str, top_k: int = 4) -> List[DocumentChunk]:
    ranked = _bm25_scores(query)
    _ensure_index()
    assert _CHUNKS is not None
    out: List[DocumentChunk] = []
    for idx, sc in ranked[:top_k]:
        if sc <= 0 and len(out) >= 1:
            break
        out.append(_CHUNKS[idx])
    if not out and _CHUNKS:
        out = _CHUNKS[: min(top_k, len(_CHUNKS))]
    return out


def _compose_local_answer(query: str, contexts: List[DocumentChunk]) -> str:
    lines = [
        "Here is what CRISPR-Sim documentation says, based on your question:",
        "",
    ]
    for j, ch in enumerate(contexts, start=1):
        preview = ch.text.strip().replace("\n", " ")
        if len(preview) > 650:
            preview = preview[:647] + "…"
        lines.append(f"[{j}] ({ch.doc_id})")
        lines.append(preview)
        lines.append("")
    lines.append(
        "Tip: run a full simulation in the app (Input → Viewer → PAM → Cut → Repair → Analysis) "
        "to see live numbers and sequences."
    )
    return "\n".join(lines)


async def _openai_answer(query: str, contexts: List[DocumentChunk]) -> str | None:
    key = os.getenv("OPENAI_API_KEY", "").strip()
    if not key:
        return None
    context_blob = "\n\n".join(f"### {c.doc_id}\n{c.text}" for c in contexts)
    system = (
        "You are CRISPR-Sim Help, an expert tutor for a CRISPR-Cas9 simulation app. "
        "Answer ONLY using the CONTEXT below plus standard molecular biology definitions. "
        "Be concise, friendly, and use short bullets when helpful. "
        "If CONTEXT is insufficient, say so and name which in-app screen helps."
    )
    user = f"CONTEXT:\n{context_blob}\n\nUSER QUESTION:\n{query}"
    payload = {
        "model": os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini"),
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.3,
        "max_tokens": 800,
    }
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            r = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            r.raise_for_status()
            data = r.json()
            return data["choices"][0]["message"]["content"].strip()
    except Exception:
        return None


async def rag_answer(query: str, top_k: int = 4) -> tuple[str, List[str]]:
    q = query.strip()
    if not q:
        return "Ask a question about CRISPR-Sim, DNA/RNA/protein, or the app screens.", []
    contexts = retrieve(q, top_k=top_k)
    sources = [c.doc_id for c in contexts]

    llm = await _openai_answer(q, contexts)
    if llm:
        return llm, sources
    return _compose_local_answer(q, contexts), sources
