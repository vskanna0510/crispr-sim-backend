"""
Guide RNA Efficiency Scoring Module
=====================================
Current status: Heuristic placeholder.

This module is intentionally structured to allow a drop-in replacement of
the heuristic scorer with a trained scikit-learn Random Forest model once
labelled training data (e.g. Doench 2016 / Azimuth dataset) is available.

Usage::

    from ml.guide_scoring import score_grna

    result = score_grna("GCACTGAGCTAGCTAGCTAG")
    print(result["score"], result["grade"])

Future upgrade path:
    1. Collect gRNA efficiency data (sequence + measured editing efficiency).
    2. Call ``train_and_save_model(training_data, "ml/models/rf_guide.pkl")``.
    3. Replace the heuristic in ``score_grna`` with ``load_model`` + ``predict``.
"""

from __future__ import annotations
from typing import List, Dict, Optional


# ─── Feature extraction ───────────────────────────────────────────────────────

def extract_features(grna: str) -> List[float]:
    """
    Encode a 20-nt gRNA sequence as a numeric feature vector.

    Features (15 total):
        [0]   GC content (fraction)
        [1–4] Mono-nucleotide frequencies (A, T, G, C)
        [5–9] One-hot: is position 1–5 a G?  (seed region start)
        [10–14] One-hot: is position 16–20 a C? (PAM-proximal)
    """
    seq = grna.upper()
    n = len(seq)
    if n == 0:
        return [0.0] * 15

    gc  = (seq.count("G") + seq.count("C")) / n
    a_f = seq.count("A") / n
    t_f = seq.count("T") / n
    g_f = seq.count("G") / n
    c_f = seq.count("C") / n

    seed_g   = [1.0 if (i < len(seq) and seq[i] == "G") else 0.0 for i in range(5)]
    prox_c   = [1.0 if (15 + i < len(seq) and seq[15 + i] == "C") else 0.0 for i in range(5)]

    return [gc, a_f, t_f, g_f, c_f] + seed_g + prox_c


# ─── Heuristic scorer ─────────────────────────────────────────────────────────

def score_grna(grna: str) -> Dict:
    """
    Return a predicted efficiency score for a 20-nt gRNA.

    The current implementation applies known heuristic rules from the
    literature (Doench et al., Xu et al.). Replace the body with a
    ``model.predict()`` call once a trained model is available.

    Returns:
        {
            "grna":        str,
            "score":       float (0–1, higher = more efficient),
            "grade":       str   (A / B / C / D / F),
            "gc_content":  float,
            "features":    list[float],
            "note":        str,
        }
    """
    seq = grna.upper()

    if len(seq) != 20:
        return {
            "grna":    grna,
            "score":   0.0,
            "grade":   "F",
            "error":   f"gRNA must be exactly 20 nt (got {len(seq)})",
        }

    gc = (seq.count("G") + seq.count("C")) / 20 * 100
    score = 0.5  # baseline

    # GC content: 40–60 % optimal
    if 40.0 <= gc <= 60.0:
        score += 0.20
    elif 30.0 <= gc < 40.0 or 60.0 < gc <= 70.0:
        score += 0.08
    else:
        score -= 0.10

    # Poly-T run (≥ 4) terminates RNA Pol III transcription
    if "TTTT" in seq:
        score -= 0.15

    # G-quadruplex risk (GGGG)
    if "GGGG" in seq:
        score -= 0.10

    # Prefer G at position 20 (adjacent to PAM)
    if seq[-1] == "G":
        score += 0.05

    # Avoid T at PAM-proximal position 20
    if seq[-1] != "T":
        score += 0.02

    # Prefer G/C at seed region (positions 1–5 from 5' end)
    seed_gc = sum(1 for b in seq[:5] if b in "GC")
    score += seed_gc * 0.01

    score = max(0.0, min(1.0, round(score, 3)))

    grade = "A" if score >= 0.70 else \
            "B" if score >= 0.60 else \
            "C" if score >= 0.50 else \
            "D" if score >= 0.40 else "F"

    return {
        "grna":       grna,
        "score":      score,
        "grade":      grade,
        "gc_content": round(gc, 2),
        "features":   extract_features(grna),
        "note":       "Heuristic placeholder – replace with trained RF model for production.",
    }


# ─── Future: Random Forest integration ───────────────────────────────────────

def train_and_save_model(
    training_data: List[tuple],
    model_path: str = "ml/models/rf_guide.pkl",
) -> None:
    """
    Train a Random Forest on (grna_sequence, efficiency_score) pairs and
    persist it with joblib.

    Args:
        training_data: list of (str, float) tuples.
        model_path:    destination .pkl path.

    Example::

        from sklearn.ensemble import RandomForestRegressor
        import joblib, numpy as np

        X = np.array([extract_features(seq) for seq, _ in training_data])
        y = np.array([score for _, score in training_data])

        model = RandomForestRegressor(n_estimators=200, random_state=42)
        model.fit(X, y)
        joblib.dump(model, model_path)
        print("Model saved to", model_path)
    """
    # Placeholder – implement once labelled data is available.
    raise NotImplementedError("Training requires scikit-learn and labelled efficiency data.")


def load_model(model_path: str) -> Optional[object]:
    """
    Load a previously trained model from disk.

    Returns:
        Loaded model object, or None if the file does not exist.

    Example::

        import joblib
        return joblib.load(model_path)
    """
    try:
        import joblib          # type: ignore
        return joblib.load(model_path)
    except (ImportError, FileNotFoundError):
        return None
