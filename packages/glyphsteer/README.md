# GlyphSteer

**Dual-regime retrieval steering via compiled in-band glyph annotations.**

An LLM annotation pass writes a *controlled glyph vocabulary* onto a corpus. Those
markers **steer retrieval in two regimes at once** — lexically (a rare glyph-tag is a
maximal-IDF exact-match *facet*) and densely (an emoji carries a *learned direction* that
nudges the chunk's embedding) — and are then **stripped from the returned text**, so the
reader/generator never sees them.

> One artifact (the annotated chunk). Two indexes (BM25 + dense). Invisible at output.

This is **HoneyC pointed at the index instead of Prolog** (a glyph code is a HoneyC
chain), and the cousin of Anthropic's *Contextual Retrieval* — but with a **compiled,
queryable, faceted controlled vocabulary** in place of free-text context.

## The sidecar split (the keystone)

```
indexed-form  = clean_text ⊕ glyph_code     → embedded / FTS5-indexed  (MATCHING)
returned-form = clean_text                   → handed to the reader     (READING)
```

The glyph lives only in the matching representation. `check_hidden` / `assert_hidden`
make the hide a hard invariant.

## One axis, two renderings (a verified finding)

FTS5's `unicode61` tokenizer **drops emoji** (verified — it matches `0`). So each axis
carries two markers:

| | marker | regime | why |
|---|---|---|---|
| **glyph** | 😡 | dense | emoji has a learned direction, near-orthogonal to prose |
| **tag** | `gsxnegative` | lexical | rare ASCII single-token ⇒ maximal IDF, exact facet |

## Install & use

```bash
pip install -e .                # lexical regime, zero heavy deps
pip install -e '.[dense]'       # adds sentence-transformers for the dense regime
```

```python
from glyphsteer import SENTIMENT, Chunk, RuleAnnotator, annotate_chunk, build_index, search

ann = RuleAnnotator.keyword(SENTIMENT, {
    SENTIMENT.by_name("negative").glyph: ["failed", "broke", "terrible"],
    SENTIMENT.by_name("positive").glyph: ["great", "excellent", "succeeded"],
})
chunks = [annotate_chunk(Chunk(c.id, c.text), ann, SENTIMENT) for c in corpus]
con = build_index(chunks)
hits = search(con, "deployment", facet=SENTIMENT.by_name("negative").glyph)
# hits[i]["text"] is CLEAN — the glyph never leaks into the output
```

CLI: `glyphsteer vocab` · `glyphsteer annotate corpus.jsonl -k 😡=failed,broke` ·
`glyphsteer query corpus.jsonl "deployment" -f 😡`

## Flagship use: grade a corpus, search shows grades

The vocabulary is general (`SENTIMENT` is just the demo). The built-in `GRADE` vocabulary
(🏆 excellent / ✅ good / ⚠️ fair / ❌ poor) lets an LLM grade "what's good and what isn't";
search then shows the grade and can facet to it. **Grading rides the lexical regime** — a
grade is a label you filter/display by, not a semantic direction (`experiments/grade_demo.py`):

```
search 'database' — results WITH grades (best→worst):
  [🏆 excellent ] Use parameterized queries to prevent SQL injection (OWASP A03).
  [✅ good      ] Connection pooling improves DB throughput; benchmark before tuning.
  [⚠️ fair     ] Indexes might help query speed, not totally sure when.
  [❌ poor      ] If the database is slow just restart the server.
facet = poor only (the audit view):
  [❌ poor      ] You can concatenate user input into SQL strings, usually fine.
```

The grade glyph rides back in each hit's `code` for display; the body text stays clean.

## The dense sidecar (containerized, no torch)

The heavy neural runtime lives in a Docker image (`serve/`): **fastembed → onnxruntime**,
model weights pre-cached, ~888MB, **no torch**. The host calls it over HTTP and stays
dependency-light (the remote client is stdlib urllib). Swapping the embedding model is one
env var — which is exactly what made the emoji-collapse finding below discoverable.

```bash
cd serve && docker compose up --build -d           # serves :8088
export GLYPHSTEER_EMBED_URL=http://localhost:8088   # host now uses the sidecar
python experiments/emoji_collapse_check.py          # gate: is the model emoji-blind?
python experiments/magnitude_probe.py               # Q1–Q3
```

## Results (measured via the sidecar, 2026-06-16)

- **Lexical Q4 (retrieval lift):** MRR **0.417 → 1.000** on the toy sentiment-faceted
  corpus (`experiments/retrieval_lift.py`). Zero deps.
- **THE dense finding — emoji-direction is model-dependent:**

  | model | distinct-emoji cosine | Q1 separation | verdict |
  |---|---|---|---|
  | `bge-small-en-v1.5` (English) | **1.000** (collapse) | −0.01…+0.08 (noise) | emoji → `[UNK]`, **blind** |
  | `paraphrase-multilingual-MiniLM-L12-v2` (XLM-R) | 0.77–0.97 | **+0.28…+0.58** | carries direction ✓ |

- **With the byte-aware model:** Q1 (alignment) **passes strongly**; Q2 (per-token nudge)
  is **modest** (+0.02…+0.09 Δcos); Q3 (anchor reshape) is a **controllable gain** (×2 at
  weight 1) — so steering strength is a tuning knob, not a yes/no. See `implementation_plan.md`
  §3.1 and `experiments/results/magnitude_probe.json`.

## Layout
See [`implementation_plan.md`](implementation_plan.md) (canonical) and
[`.claude/rules/`](.claude/rules) for the component/flow diagrams and the discovered
development workflows.
