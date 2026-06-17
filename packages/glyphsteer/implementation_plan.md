# GlyphSteer — Implementation Plan

> **Canonical implementation plan** for the GlyphSteer package. This is the single
> source of structural truth for the build (per the repo's canonical-design rule).
> Update it in the same commit as any structural change. `ASPIRATIONAL:` marks
> what is planned but not yet built.

---

## 1. The thesis (the publishable claim)

**GlyphSteer** = a **compiled controlled vocabulary of in-band glyph markers** that an
LLM annotation pass writes onto a corpus, which then **steers retrieval in two regimes
at once** — lexically (a rare glyph is a maximal-IDF exact-match *facet*) and densely (a
glyph carries a *learned direction* in embedding space, so it nudges the chunk vector) —
while being **stripped from the returned text** so the reader/generator never sees it.

> One artifact (the annotated chunk). Two indexes (BM25 + dense). Invisible at output.

The keystone is the **sidecar split**: a chunk has two representations that need not be
the same string —

- **indexed-form** = `clean_text ⊕ glyph_code`  → what we embed / FTS5-index (matching)
- **returned-form** = `clean_text`               → what we hand the reader (reading)

The glyph lives **only** in the matching representation. Annotation that votes on its own
findability, then disappears.

### Why each regime works (the mechanism, stated precisely)

**ONE AXIS, TWO RENDERINGS (corrected by a verified finding):** FTS5's `unicode61`
tokenizer **DROPS emoji** — an emoji in the body is not even indexable. So the lexical
facet cannot be the emoji; it is an **ASCII sentinel `tag`** per axis (e.g. `gsxnegative`),
a rare single token (max IDF). The **emoji** serves the **dense** regime only. Same axis,
two renderings; `index.py` faceting takes a glyph and resolves it to its tag.

| Regime | The rendering used | Why it steers | Lever |
|---|---|---|---|
| **Lexical (BM25)** | the axis's **ASCII sentinel tag** (`gsxnegative`) — *not* the emoji (FTS5 drops it) | a rare single token ⇒ near-max IDF ⇒ exact, deterministic rank-pin / facet | **a reserved rare ASCII token** |
| **Dense (embeddings)** | the **emoji** | the model learned the glyph from human usage (emoji2vec, 1609.08359), so it sits near its semantic neighbors; injecting it shifts the pooled vector along that direction | **direction + near-orthogonality to prose** (and the model must not collapse emoji — §3.1) |

**The trap this plan guards against:** rarity is the lever for lexical; *direction* is the
lever for dense. A glyph chosen only for uniqueness gives dense *separation* but not
*control*. To get **control** in the dense regime we either (i) pick glyphs whose learned
direction matches the intended axis (sentiment is the strongest case — emoji *are* how
humans encode sentiment, Novak 2015), or (ii) **measure** each glyph's direction once and
**project** (the anchor reshape, §4.6).

## 1.5 Applications — the vocabulary is general (sentiment was just the demo)

GlyphSteer is vocabulary-agnostic: `SENTIMENT` is one built-in, `GRADE` is another, and any
`Vocabulary([Axis(...)])` works. The flagship application is **corpus grading**:

> An LLM grades every chunk ("what's good and what isn't") with the `GRADE` vocabulary
> (🏆 excellent / ✅ good / ⚠️ fair / ❌ poor); search then **shows the grade** on each hit
> and can **facet** to a grade ("excellent only", or audit "poor only").

**Grading rides the LEXICAL regime — the reliable one — by design, NOT the dense one.** A
grade is a label you *filter and display by*, not a semantic direction. Conflating quality
with the sentiment-emoji direction is a trap: a correct chunk can be grim ("the patient
died"), an upbeat chunk can be junk. So grade = lexical facet (deterministic, zero deps);
dense direction stays for genuinely-semantic axes (tone/topic). Demo: `experiments/grade_demo.py`;
the grade glyph rides back in each hit's `code` for display while the body text stays clean.

## 2. Prior art & honest delta (so the claim survives review)

- **Cousin — Anthropic Contextual Retrieval (Sept 2024):** prepend LLM-generated context
  before embedding ⇒ embedded-form ≠ displayed-form. Same skeleton as our sidecar split.
- **GlyphSteer's genuine delta over it:**
  1. **Compiled controlled vocabulary**, not free text → queryable / composable / *faceted*
     (you can `WHERE code MATCH '😡'`, not just embed prose).
  2. **Compression** — a few glyphs vs a sentence of context ⇒ cheaper embed, higher
     signal density per token.
  3. **Dual-regime single marker** — the *same* glyph is a BM25 facet *and* a dense anchor.
  4. **Anchor projection** (§4.6) — turns the *inherited* emoji direction into a
     *controllable, query-time-weighted* axis (a rank-k bilinear metric reshape).
- **The annotation pass is a ChainCompiler skillchain** (SC over the corpus), and the
  glyph code is a **HoneyC chain** — GlyphSteer is *HoneyC pointed at the index instead of
  at Prolog*. This is the integration story, not a coincidence.

## 3. The open empirical question (what the eval must answer)

Hiding makes the *output* clean; it does **nothing** for the *strength* of the dense nudge.
So the gating numbers are:

- **Q1 (alignment):** is `cos(glyph, aligned_word) ≫ cos(glyph, unrelated_word)`? (does the
  glyph mean what we think)
- **Q2 (magnitude):** when we inject a glyph into a neutral chunk, how far does its vector
  move toward the intended axis (`Δcos`)? Big enough to reorder results, or a toy?
- **Q3 (need-for-projection):** does the anchor reshape (§4.6) meaningfully amplify Q2?
- **Q4 (retrieval lift):** on a labeled toy corpus, does annotate→steer beat the
  no-annotation baseline (MRR / recall@k), lexically and densely?

Lexical regime needs none of this — it is *exact-match true* and provable with zero deps.
Dense regime is gated on Q1–Q3 and needs an embedding model stood up.

### 3.1 RESULTS (measured 2026-06-16, via the `glyphsteer-serve` ONNX sidecar)

**THE FINDING — emoji-direction is model/tokenizer dependent (a failure mode + its fix):**

| model | distinct-emoji pairwise cos | Q1 separation | verdict |
|---|---|---|---|
| `BAAI/bge-small-en-v1.5` (English WordPiece) | **1.000** (total collapse) | −0.009 … +0.080 (noise) | **emoji-blind — all emoji → one token ([UNK])** |
| `paraphrase-multilingual-MiniLM-L12-v2` (XLM-R, byte-aware) | 0.77 … 0.97 (distinct) | **+0.28 … +0.58** | **emoji carry clean direction** |

This is why the sidecar is **model-swappable**: the failure was invisible until measured,
and fixable in one env var. Run `experiments/emoji_collapse_check.py` against ANY candidate
model *first* (dev-workflow DW-6).

**With the byte-aware model:**
- **Q1 (alignment): PASS, strong** — `cos(glyph, aligned) − cos(glyph, unrelated)` = +0.28…+0.58
  for all 5 axes (😊+0.45, 😡+0.39, 🔥+0.35, ❓+0.58, ⚠️+0.28).
- **Q2 (per-token magnitude): MODEST** — injecting one emoji into a neutral sentence shifts
  its vector by Δcos +0.02…+0.09 (❓ −0.03). Real but small; per-token mean-pooling dilutes it.
- **Q3 (projection): a CONTROLLABLE GAIN** — `steer.sim_eff` at weight=1 doubles the nudge
  (×2.0, uniform, as the bilinear math predicts); raising the weight scales it further. So
  "is the nudge big enough?" is a *tuning* question, not yes/no — the anchor weight is the knob.
  (Caveat: too-high weight collapses ranking onto the anchor, ignoring the query — sane range.)
- **Q4 (lexical): MRR 0.417 → 1.000** (`retrieval_lift.py`). Dense Q4 to follow now that Q1–Q3 clear.

Full data: `experiments/results/magnitude_probe.json`.

## 4. Architecture (modules)

```
packages/glyphsteer/
  implementation_plan.md      ← this file (canonical)
  README.md
  pyproject.toml              (deps: numpy; extras: dense=[sentence-transformers])
  src/glyphsteer/
    __init__.py
    vocab.py      §4.1  controlled glyph vocabulary; validate; HoneyC code bridge
    annotate.py   §4.2  the annotation pass (RuleAnnotator + pluggable LLMAnnotator)
    encode.py     §4.3  THE sidecar split: indexed_form / returned_form + invariant
    index.py      §4.4  lexical FTS5 index over indexed-form; facet filter; return clean
    dense.py      §4.5  optional dense layer (lazy sentence-transformers); anchor measure
    steer.py      §4.6  bilinear metric reshape sim_eff(q,d,anchors,weights)
    eval.py       §4.7  magnitude probe + retrieval lift harness
    cli.py              annotate / index / search / probe
  tests/                vocab, encode (the hide invariant), index (e2e), steer (math)
  experiments/          magnitude_probe.py, retrieval_lift.py, emoji_collapse_check.py
    results/            magnitude_probe.json (measured artifacts)
  serve/                Dockerfile, app.py (FastAPI), requirements.txt, docker-compose.yml
                        — the ONNX/fastembed embedding sidecar (no torch)
  .claude/rules/        00 write-down-archi-and-flows (META), 10 components, 20 flows
  .claude/skills/glyphsteer/SKILL.md
```

### 4.1 `vocab.py`
`Axis(name, glyph, description)`; `Vocabulary(axes)`. Validation: glyphs unique; each glyph
non-alphanumeric & non-ASCII (so it's a clean lexical routing key that never collides with a
prose word); `code(glyphs)` joins to a compact string; `glyphs_in(text)` / `strip(text)`.
Bridge: a code is a HoneyC chain (`a→b`), so `to_honeyc()` emits chain notation.

### 4.2 `annotate.py`
`Annotation(axis, glyph)`. `Annotator` protocol → `annotate(chunk_text) -> list[Annotation]`.
- `RuleAnnotator(rules: dict[glyph, predicate])` — deterministic, no LLM, **reproducible**
  (the test/CI annotator).
- `LLMAnnotator(judge: Callable[[str, Vocabulary], str])` — injectable; the real pass. The
  judge returns a glyph code string; we parse it back through the vocab (unknown glyphs
  dropped — the vocab is the gate, mirroring the *CC "syntax-only" discipline).

### 4.3 `encode.py` (keystone)
`Chunk(id, text, code="", meta={})`. 
- `indexed_form(chunk) -> clean ⊕ SEP ⊕ code`
- `returned_form(chunk) -> clean`, **provably glyph-free** (`vocab.strip`).
- `annotate_chunk(chunk, annotator, vocab) -> Chunk(code=...)`.
- **Invariant** (tested): `set(vocab.glyphs_in(returned_form(c))) == ∅` and every annotated
  glyph ∈ `indexed_form(c)`.

### 4.4 `index.py`
FTS5 table `chunks(id UNINDEXED, body, code, clean UNINDEXED)` where `body` = indexed-form.
`search(con, query, *, facet=None)` BM25-ranked; `facet` adds `AND code MATCH glyph` (exact).
Hits return **clean** text (the hide, enforced at the read boundary). Mirrors skilltree.search.

### 4.5 `dense.py`  *(optional extra)*
Lazy import of `sentence-transformers` (`all-MiniLM-L6-v2` default). `embed(texts)`,
`measure_anchor(glyph)` = `embed([glyph])[0]`. Raises a clear error if the extra isn't
installed — the rest of the package works without it.

### 4.6 `steer.py`
Pure-numpy metric reshape (no model needed — takes vectors):
```
sim_eff(q, d) = cos(q, d) + Σ_k w_k · ⟨q, â_k⟩ · ⟨d, â_k⟩
```
`â_k` = unit anchor directions (from §4.5), `w_k` = per-query weights. `rerank(q, docs,
anchors, weights)`. This is the rank-k bilinear correction that makes the inherited glyph
direction a *controllable, query-time* axis.

### 4.7 `eval.py`
`magnitude_probe(vocab, dense, pairs)` → Q1/Q2 table. `retrieval_lift(corpus, queries,
labels, ...)` → MRR/recall@k baseline-vs-steered, lexical and dense. Emits a JSON report =
the paper's results table.

## 4.8 VERIFIED FINDING — FTS5 drops emoji ⇒ one axis, two renderings

While building `index.py`, faceting on the emoji returned **0 hits**. Verified directly:

```python
con.execute("CREATE VIRTUAL TABLE t USING fts5(c)")
con.execute("INSERT INTO t(c) VALUES (?)", ("😡",))          # → MATCH "😡" gives 0
con.execute("INSERT INTO t(c) VALUES (?)", ("gsxnegative",)) # → MATCH gsxnegative gives 1
```

FTS5's `unicode61` tokenizer treats emoji as separators — they are **not indexed**. So the
**lexical facet cannot be the emoji**; it must be an ASCII single-token sentinel `tag`
(`gsxnegative`). The emoji remains the **dense** marker (the embedder *does* tokenize it
and it carries a learned direction). Hence **one `Axis`, two renderings**: `glyph` (dense)
+ `tag` (lexical), auto-derived. Captured as regression `tests/test_dual_regime.py` and
dev-workflow **DW-1** in `.claude/rules/20-architecture-flows.md`.

## 5. Build order (status)

- [x] P0 scaffold: pyproject, package, plan
- [x] P1 `vocab.py` + tests (Axis dual-rendering glyph+tag, validation, HoneyC bridge)
- [x] P2 `encode.py` + the **hide invariant** test (the keystone) — `check_hidden` green
- [x] P3 `annotate.py` (RuleAnnotator + injectable LLMAnnotator) + tests
- [x] P4 `index.py` lexical e2e + test (annotate→encode→index→facet→return-clean, zero deps)
- [x] P5 `steer.py` bilinear + test (pure numpy; zero-weight = cosine; anchor promotes aligned)
- [x] P6 `dense.py` multi-backend (remote/fastembed/st) + probe — **Q1–Q3 MEASURED (§3.1)**
- [x] P7 `eval.py` + `experiments/retrieval_lift.py` — **lexical Q4 result: MRR 0.417 → 1.000 (+0.583)**
- [x] P8 `cli.py` (annotate / query / vocab — verified end-to-end)
- [x] P9 README + arch/flow diagrams in `.claude/rules` + skill
- [x] P9.5 `serve/` ONNX sidecar (Docker, no torch) — built, run, probed; the model-collapse
      finding (§3.1) found+fixed via model swap
- [ ] P10 paper draft `ASPIRATIONAL:` (arXiv short) — now unblocked; needs the dense arm of
      Q4 (faceted dense retrieval lift with the anchor reshape) + a real (non-toy) corpus

### Status: lexical regime COMPLETE & verified. Dense regime BUILT, containerized, and
MEASURED: emoji-direction confirmed real but model-dependent (§3.1) — bge-en collapses
emoji, multilingual XLM-R does not; Q1 strong, Q2 modest, Q3 a controllable gain. 22 tests
green. Remaining for the paper: dense Q4 on a real corpus.

## 5.1 Legend + ChainCompiler search integration (DONE 2026-06-16)

- `legend.py` — an LLM **authors** a vocabulary (`author([{name,glyph,description}])`, tag
  auto-derived), it **persists** (`save_legend`/`load_legend`, JSON), **accumulates** into a
  master legend (`merge`, last-author-wins), and **renders** for display (`render_legend`).
  The legend = the glyph↔meaning↔tag table the LLM invents and keeps.
- `GRADE` vocabulary + `grade_label` + `experiments/grade_demo.py` — grading a RAG corpus
  ("what's good and what isn't") rides the **lexical** facet (reliable), search returns the
  grade badge. (Quality ≠ sentiment — grading is a facet, not a dense direction.)
- **Integrated into `skilltree.search`** (the ChainCompiler search arm): `build_index(root,
  vocab=...)` reads each skill's `glyphs:` frontmatter → ASCII tags column; `search(con, q,
  facet=glyph, vocab=...)` filters by glyph and returns the glyph badge. Backward compatible
  (`vocab=None` ⇒ original behaviour). CLI: `skilltree search ROOT Q --facet 🏆 --legend l.json`.

## 5.2 Syntax consistency via rulecatcher (DONE 2026-06-16)

`grammar.py` (`GlyphGrammar`) puts **rulecatcher under GlyphSteer** — a glyph code is a DSL,
so it goes through ChainCompiler's lint/gate engine (via `chaincompiler.bridge.learn`/`gate`),
the same gate the `*CC` compilers use. Gating is over the ASCII **tag** rendering (rulecatcher
drops emoji, same lesson as FTS5/dense). Three verdicts mirror rulecatcher's:
- `ok` — well-formed, canonical order.
- `orthogonal` — known tags, wrong order → steerable; `canonicalize` reorders to vocab order
  (a partial-order check GlyphSteer owns, since n-gram grammars express partial order poorly).
- `syntax_break` — a foreign token (rulecatcher's strength: it owns this verdict).

Wired (optional) into `annotate_chunk(..., grammar=gg)`: `orthogonal` repaired, `syntax_break`
raises. Needs the `grammar` extra + the sibling `chaincompiler` package. `glyphsteer.grammar`
imports the engine lazily, so importing GlyphSteer never requires it. 6 tests.

## 6. ASPIRATIONAL

- `ASPIRATIONAL:` LLM annotator wired to a real skillchain over the live skill corpus.
- `ASPIRATIONAL:` RRF fusion of lexical+dense (k=60) once both are measured.
- `ASPIRATIONAL:` arXiv short paper "GlyphSteer: Dual-Regime Retrieval Steering via
  Compiled In-Band Glyph Annotations" with the §3 numbers.
- `ASPIRATIONAL:` ship as a ChainCompiler skill + MCP tool (`gs_annotate`, `gs_search`).
