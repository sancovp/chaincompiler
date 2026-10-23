---
name: glyphsteer-dense
description: Use when running GlyphSteer's DENSE regime — embedding-based emoji steering via the containerized ONNX sidecar. Covers standing up the glyphsteer-serve Docker image, the MANDATORY emoji-collapse gate (many models map all emoji to one token), the magnitude probe, and the anchor metric-reshape (steer.sim_eff). Triggers on "glyphsteer dense", "embedding steering", "emoji direction", "glyphsteer sidecar", "magnitude probe", "anchor reshape", "is the dense nudge big enough".
---

# GlyphSteer — the dense regime (containerized)

The dense half steers retrieval by the emoji's **learned direction** in embedding space.
The heavy neural runtime lives in a Docker sidecar (`fastembed → onnxruntime`, **no torch**);
the host calls it over HTTP and the steer/probe math runs host-side in pure numpy.

> Run all `packages/...` commands from the **repo root** (`.../chaincompiler`).

## 1. Stand up the sidecar

```bash
cd packages/glyphsteer/serve
# byte-aware multilingual model — REQUIRED (see the collapse gate below)
GLYPHSTEER_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 \
  docker compose up --build -d
curl localhost:8088/health      # {"status":"ok","model":"...MiniLM-L12-v2"}
curl localhost:8088/info        # {"model":"...","dim":384}
export GLYPHSTEER_EMBED_URL=http://localhost:8088   # host now uses the sidecar
```

The host `dense.embed(texts)` auto-routes to the container when `GLYPHSTEER_EMBED_URL` is set
(stdlib urllib — no host deps). Backends: `remote` (container, default when the env var is
set), `fastembed` (local ONNX), `st` (local sentence-transformers).

## 2. THE GATE — check emoji-collapse FIRST (non-negotiable)

Many English tokenizers (BERT/WordPiece, e.g. `bge-small-en-v1.5`) map **every** emoji to the
same token (`[UNK]`) → all emoji embed identically → dense steering is **impossible**. Always
run the gate before trusting any dense number:

```bash
GLYPHSTEER_EMBED_URL=http://localhost:8088 \
  python3 packages/glyphsteer/experiments/emoji_collapse_check.py
# mean off-diagonal cosine ≈ 1.000 ⇒ COLLAPSED (reject the model)
# well below 1.0 (e.g. 0.77–0.97) ⇒ DISTINCT (proceed)
```

Verified: `bge-small-en-v1.5` → 1.000 (blind). `paraphrase-multilingual-MiniLM-L12-v2` →
distinct, with clean alignment. Fix a collapse with a one-env-var model swap + rebuild.

## 3. Magnitude probe (Q1–Q3)

```bash
GLYPHSTEER_EMBED_URL=http://localhost:8088 \
  python3 packages/glyphsteer/experiments/magnitude_probe.py
```
- **Q1 (alignment):** `cos(glyph, aligned_word) − cos(glyph, unrelated)` — should be clearly
  positive (the emoji means what you think). Measured +0.28…+0.58 with the multilingual model.
- **Q2 (per-token nudge):** injecting one emoji shifts a neutral chunk's vector by Δcos
  ~−0.03…+0.09 — real but modest, and a single token can wash out or slightly *invert* under
  mean-pooling (e.g. ❓ measured −0.034). This is why Q2 is a tuning concern, not a guarantee.
- **Q3 (anchor reshape):** a controllable gain (×2 at weight 1).

## 4. Steer — the anchor metric reshape (pure numpy, host-side)

`sim_eff` (lives in `glyphsteer.steer`, re-exported at top level — `from glyphsteer import
sim_eff`) bends the similarity metric toward chosen anchors at query time:
`sim_eff(q,d) = cos(q,d) + Σ_k w_k·⟨q,â_k⟩·⟨d,â_k⟩`, with â_k from `dense.measure_anchor`.

```python
from glyphsteer import dense, sim_eff
anchor = dense.measure_anchor("😡")     # the glyph's learned direction (via the sidecar)
q = dense.embed(["the deploy broke"])[0]
docs = dense.embed(["it crashed badly", "it shipped fine"])
scored = sim_eff(q, docs, anchors=anchor[None, :], weights=[1.5])   # weight = the steering knob
```
weight 0 = plain cosine; raising it makes that axis dominate (too high → ignores the query).

## Honest status
Dense is **viable and measured** but its per-token strength is a *tuning knob*, not a free
lunch; end-to-end dense retrieval lift on a real (non-toy) corpus is the open item. Lexical
faceting (the core **glyphsteer** skill) is the regime that's a clean win today.

## Verify (run this)
```bash
cd packages/glyphsteer/serve && docker compose up --build -d && cd -
export GLYPHSTEER_EMBED_URL=http://localhost:8088
python3 packages/glyphsteer/experiments/emoji_collapse_check.py   # gate
python3 packages/glyphsteer/experiments/magnitude_probe.py        # Q1–Q3
```
Architecture/flows: `packages/glyphsteer/.claude/rules/{10,20}-architecture-*.md` (DW-6/DW-7).
