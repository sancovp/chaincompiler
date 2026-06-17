"""The bilinear metric reshape: weight 0 = plain cosine; raising it bends ranking."""
import numpy as np

from glyphsteer import cosine, rerank, sim_eff, unit


def test_zero_weight_recovers_cosine():
    rng = np.random.default_rng(0)
    q = rng.standard_normal(8)
    d = rng.standard_normal((5, 8))
    base = cosine(q, d)
    same = sim_eff(q, d, anchors=None, weights=None)
    assert np.allclose(base, same)
    also = sim_eff(q, d, anchors=d[:1], weights=[0.0])
    assert np.allclose(base, also)


def test_anchor_weight_promotes_aligned_doc():
    # two docs, equally similar to q at baseline; one lies along the anchor.
    dim = 16
    anchor = np.zeros(dim); anchor[0] = 1.0
    q = np.zeros(dim); q[1] = 1.0                       # q orthogonal to anchor...
    # craft q to have a small positive anchor component so ⟨q,â⟩>0
    q[0] = 0.5
    aligned = np.zeros(dim); aligned[0] = 1.0; aligned[1] = 1.0   # on the anchor + q dir
    off = np.zeros(dim); off[1] = 1.0; off[2] = 1.0               # off the anchor
    docs = np.vstack([off, aligned])
    base = cosine(q, docs)
    steered = sim_eff(q, docs, anchors=anchor[None, :], weights=[2.0])
    # the aligned doc gains MORE from steering than the off-anchor doc
    assert (steered[1] - base[1]) > (steered[0] - base[0])


def test_rerank_orders_best_first():
    q = np.array([1.0, 0.0])
    docs = np.array([[0.1, 1.0], [1.0, 0.05]])
    out = rerank(q, docs, ids=["far", "near"])
    assert out[0]["id"] == "near"
    assert out[0]["score"] >= out[1]["score"]


def test_unit_normalizes():
    v = np.array([3.0, 4.0])
    assert np.isclose(np.linalg.norm(unit(v)), 1.0)
