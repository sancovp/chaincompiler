"""The evaluation harness — produces the numbers the claim lives or dies on.

Q1 alignment   : cos(glyph, aligned_word) ≫ cos(glyph, unrelated_word)?
Q2 magnitude   : injecting a glyph into a neutral chunk moves its vector by Δcos toward
                 the axis — big enough to reorder, or a toy?
Q3 projection  : does the steer.py anchor reshape amplify Q2?
Q4 retrieval   : on labeled data, does annotate→steer beat the no-annotation baseline
                 (MRR / recall@k), lexically and densely?

The dense parts (Q1–Q3, and the dense arm of Q4) require the `dense` extra; the
lexical arm of Q4 runs with zero deps.
"""
from __future__ import annotations

import numpy as np

from .encode import Chunk, annotate_chunk
from .index import build_index, search
from .steer import cosine, sim_eff
from .vocab import Vocabulary


# ---- retrieval metrics -------------------------------------------------------
def mrr(ranked_ids: list, relevant: set) -> float:
    for i, rid in enumerate(ranked_ids, 1):
        if rid in relevant:
            return 1.0 / i
    return 0.0


def recall_at_k(ranked_ids: list, relevant: set, k: int) -> float:
    if not relevant:
        return 0.0
    hit = len(set(ranked_ids[:k]) & relevant)
    return hit / len(relevant)


# ---- Q1/Q2/Q3 : the dense probe ---------------------------------------------
def magnitude_probe(vocab: Vocabulary, *, aligned: dict[str, str],
                    unrelated: dict[str, str], neutral: str,
                    model: str | None = None) -> dict:
    """Answer Q1–Q3 for each glyph.

    `aligned`/`unrelated`: {glyph: word}. `neutral`: a sentence to inject into.
    Returns a per-glyph report with cos-alignment, the Δcos injection nudge, and the
    projected (steered) nudge.
    """
    from . import dense  # lazy — needs the extra
    # report the model ACTUALLY serving embeddings (the remote sidecar may differ from
    # any local default), so the results JSON never carries a stale/wrong model label.
    model = dense.active_model() if model is None else model
    rows = []
    nvec = dense.embed([neutral], model=model)[0]
    for a in vocab.axes:
        g = a.glyph
        gvec = dense.measure_anchor(g, model=model)
        aw = aligned.get(g)
        uw = unrelated.get(g)
        cos_aligned = cos_unrelated = None
        if aw:
            cos_aligned = float(cosine(dense.embed([aw], model=model)[0],
                                       gvec[None, :])[0])
        if uw:
            cos_unrelated = float(cosine(dense.embed([uw], model=model)[0],
                                         gvec[None, :])[0])
        injected = dense.embed([f"{neutral} {g}"], model=model)[0]
        # Q2: how much did injecting g move the chunk toward g's own direction?
        delta_cos = float(cosine(gvec, injected[None, :])[0]
                          - cosine(gvec, nvec[None, :])[0])
        # Q3: the steered (projected) view of the same nudge
        steered = float(sim_eff(gvec, injected[None, :], gvec[None, :], [1.0])[0]
                        - sim_eff(gvec, nvec[None, :], gvec[None, :], [1.0])[0])
        rows.append({"glyph": g, "axis": a.name,
                     "cos_aligned": cos_aligned, "cos_unrelated": cos_unrelated,
                     "Q1_separation": (None if cos_aligned is None or cos_unrelated is None
                                       else cos_aligned - cos_unrelated),
                     "Q2_delta_cos": delta_cos, "Q3_steered_delta": steered})
    return {"model": model, "neutral": neutral, "glyphs": rows}


# ---- Q4 : retrieval lift -----------------------------------------------------
def retrieval_lift_lexical(corpus: list[Chunk], queries: list[dict],
                           annotator, vocab: Vocabulary, *, k: int = 5) -> dict:
    """Lexical Q4: MRR/recall with vs without the glyph sidecar.

    `queries`: [{"text": str, "facet": glyph|None, "relevant": set[id]}].
    Baseline indexes clean text; steered indexes annotated chunks and faceting on.
    """
    base_chunks = [Chunk(c.id, c.text) for c in corpus]
    ann_chunks = [annotate_chunk(c, annotator, vocab) for c in corpus]
    base_con = build_index(base_chunks, vocab)
    ann_con = build_index(ann_chunks, vocab)

    def run(con, use_facet):
        mrrs, recs = [], []
        for q in queries:
            facet = q.get("facet") if use_facet else None
            hits = search(con, q["text"], facet=facet, vocab=vocab, limit=k)
            ids = [h["id"] for h in hits]
            mrrs.append(mrr(ids, q["relevant"]))
            recs.append(recall_at_k(ids, q["relevant"], k))
        return {"mrr": float(np.mean(mrrs)), f"recall@{k}": float(np.mean(recs))}

    return {"baseline": run(base_con, False), "steered": run(ann_con, True), "k": k}
