"""The dense steering math — a rank-k bilinear reshape of the similarity metric.

This is the part that turns an *inherited* glyph direction into a *controllable,
query-time-weighted* axis. Given anchor directions â_k (unit vectors, one per glyph,
measured once by `dense.measure_anchor`) and per-query weights w_k:

    sim_eff(q, d) = cos(q, d) + Σ_k w_k · ⟨q, â_k⟩ · ⟨d, â_k⟩

w_k = 0 recovers plain cosine. Raising w_k for a chosen glyph makes that semantic
axis dominate the distance for *this* query only — dynamically reshaping the
embedding geometry without retraining.

Pure numpy: takes vectors, needs no model. (`dense.py` produces the vectors.)
"""
from __future__ import annotations

import numpy as np


def unit(v: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(v, axis=-1, keepdims=True)
    return v / np.clip(n, 1e-12, None)


def cosine(q: np.ndarray, d: np.ndarray) -> np.ndarray:
    """Cosine of a single query vector against a (n, dim) doc matrix."""
    return unit(np.atleast_2d(d)) @ unit(q)


def sim_eff(q: np.ndarray, d: np.ndarray, anchors: np.ndarray | None = None,
            weights: np.ndarray | list[float] | None = None) -> np.ndarray:
    """Bilinear-reshaped similarity of query `q` vs doc matrix `d` (n, dim).

    `anchors` is (k, dim); `weights` is length-k. Returns length-n scores.
    """
    d2 = np.atleast_2d(d)
    base = cosine(q, d2)                                   # (n,)
    if anchors is None or weights is None or len(weights) == 0:
        return base
    A = unit(np.atleast_2d(anchors))                      # (k, dim)
    w = np.asarray(weights, dtype=float)                 # (k,)
    qa = A @ unit(q)                                      # (k,) query·anchor
    da = unit(d2) @ A.T                                   # (n, k) doc·anchor
    correction = (da * (w * qa)).sum(axis=1)             # (n,)
    return base + correction


def rerank(q: np.ndarray, docs: np.ndarray, *, anchors=None, weights=None,
           ids: list | None = None) -> list[dict]:
    """Score docs by `sim_eff` and return them sorted best-first."""
    scores = sim_eff(q, docs, anchors, weights)
    order = np.argsort(-scores)
    ids = ids if ids is not None else list(range(len(scores)))
    return [{"id": ids[i], "score": float(scores[i])} for i in order]
