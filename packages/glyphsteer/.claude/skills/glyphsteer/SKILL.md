---
name: glyphsteer
description: Use when steering retrieval with hidden in-band markers — annotating a RAG corpus with a controlled emoji/glyph vocabulary that biases search (lexical facet + dense direction) but is stripped from returned text. Triggers on "glyph steer", "emoji annotation", "hidden retrieval markers", "steer RAG", "facet by sentiment", "annotate corpus for search".
---

# GlyphSteer

**Dual-regime retrieval steering via compiled in-band glyph annotations.** An LLM
annotation pass writes a controlled glyph vocabulary onto a corpus; the markers steer
retrieval in two regimes and then vanish from the output.

## The one idea (the sidecar split)
A chunk has two representations that need not match:
- **indexed-form** = `clean ⊕ glyph_code` → embedded / FTS5-indexed (MATCHING)
- **returned-form** = `clean` → handed to the reader (READING)

The marker steers findability, then disappears. `check_hidden` / `assert_hidden` enforce it.

## One axis, two renderings (the key finding)
FTS5's `unicode61` tokenizer **drops emoji**, so each axis carries BOTH:
- a **glyph** (emoji) — the *dense* marker: a learned direction, near-orthogonal to prose.
- a **tag** (ASCII sentinel, `gsxnegative`) — the *lexical* marker: rare ⇒ maximal-IDF facet.

## Use it
```python
from glyphsteer import SENTIMENT, Chunk, RuleAnnotator, annotate_chunk, build_index, search

ann = RuleAnnotator.keyword(SENTIMENT, {
    SENTIMENT.by_name("negative").glyph: ["failed", "broke", "terrible"],
})
chunks = [annotate_chunk(Chunk(c.id, c.text), ann, SENTIMENT) for c in corpus]
con = build_index(chunks)
hits = search(con, "deployment", facet=SENTIMENT.by_name("negative").glyph)  # → CLEAN text
```

CLI: `glyphsteer vocab` · `glyphsteer annotate corpus.jsonl -k 😡=failed,broke` ·
`glyphsteer query corpus.jsonl "deployment" -f 😡`

## Flagship use — grade a corpus, search shows grades
`GRADE` vocab (🏆/✅/⚠️/❌): an LLM grades each chunk; `search`/`facet_only` return the grade
glyph in each hit's `code` (display it via `grade_label`), and you can facet to a grade.
Grading rides the **lexical** regime (a grade is a filter/display label, not a semantic
direction — quality ≠ sentiment). Demo: `experiments/grade_demo.py`.

## Regimes
- **Lexical** (`pip install glyphsteer`): exact-match facet, zero deps, *true now*.
- **Dense** (`pip install 'glyphsteer[dense]'`): emoji direction + `steer.sim_eff` anchor
  reshape — gated on the magnitude probe (`experiments/magnitude_probe.py`).

It is **HoneyC pointed at the index** (a glyph code is a HoneyC chain) and the cousin of
Anthropic's Contextual Retrieval (embedded-form ≠ displayed-form), with a *compiled
controlled vocabulary* instead of free text. See `implementation_plan.md`.
