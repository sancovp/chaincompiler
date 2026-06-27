---
name: glyphsteer
description: Use when steering retrieval with hidden in-band glyph markers — an LLM annotates a corpus with a controlled emoji/glyph vocabulary that biases search (lexical facet + dense direction) but is stripped from returned text; also for grading a RAG corpus and searching with grade badges, and for authoring/persisting a glyph "legend". Triggers on "glyphsteer", "emoji annotation", "hidden retrieval markers", "steer RAG", "grade a corpus", "facet by sentiment/grade", "glyph legend", "annotate corpus for search".
---

# GlyphSteer — how to use it

Dual-regime retrieval steering via **compiled in-band glyph annotations**. An LLM writes a
controlled glyph vocabulary onto a corpus; the markers steer retrieval and then **vanish
from the output**. Package: `glyphsteer` (in this repo: `packages/glyphsteer`). Install:
`python3 -m pip install -e packages/glyphsteer`.

> Run all `packages/...` commands from the **repo root** (`.../chaincompiler`) — the paths
> are repo-root-relative.

## The mental model (3 facts)

1. **Sidecar split** — a chunk has two representations that need not match:
   `indexed-form = clean ⊕ glyph_code` (what gets matched) vs `returned-form = clean`
   (what the reader sees). The marker steers findability, then disappears.
2. **One axis, two renderings** — FTS5's tokenizer **drops emoji**, so each axis carries
   BOTH: a **glyph** (emoji = the *dense* marker, a learned direction) AND a **tag** (ASCII
   sentinel like `gsxnegative` = the *lexical* marker, a rare max-IDF facet). You facet with
   the glyph; the library resolves it to its tag internally.
3. **The vocabulary is the gate** — annotation only counts if the glyph is in the vocab;
   unknown glyphs are dropped (syntax-only discipline, like the `*CC` compilers).

## Quickstart — annotate, index, facet, return clean (zero deps)

```python
from glyphsteer import SENTIMENT, Chunk, RuleAnnotator, annotate_chunk, build_index, search

corpus = [Chunk("a", "the deploy pipeline passed and works great"),
          Chunk("b", "the deploy pipeline crashed, this is broken and terrible")]

ann = RuleAnnotator.keyword(SENTIMENT, {
    SENTIMENT.by_name("positive").glyph: ["great", "works", "passed"],
    SENTIMENT.by_name("negative").glyph: ["broken", "terrible", "crashed"],
})
chunks = [annotate_chunk(c, ann, SENTIMENT) for c in corpus]   # attaches the glyph code
con = build_index(chunks, SENTIMENT)                            # 2nd arg = the vocab
neg = SENTIMENT.by_name("negative").glyph
hits = search(con, "deploy", facet=neg, vocab=SENTIMENT)       # facet by a glyph
print(hits[0]["text"])   # CLEAN text — the glyph is NOT in it (the hide)
```

Key calls: `annotate_chunk(chunk, annotator, vocab)` · `build_index(chunks, vocab)` ·
`search(con, query, facet=glyph, vocab=...)` · `facet_only(con, glyph, vocab=...)`.
The hide invariant: `from glyphsteer import check_hidden; assert check_hidden(chunk, vocab)`.

## Grade a corpus, search shows grades (the flagship)

`GRADE` is a built-in quality vocabulary (🏆 excellent / ✅ good / ⚠️ fair / ❌ poor). An LLM
grades each chunk; search returns the grade badge and can facet to a grade.

```python
from glyphsteer import GRADE, GRADE_RANK, Chunk, build_index, search, grade_label
from glyphsteer.index import facet_only
EXC, POOR = GRADE.by_name("excellent").glyph, GRADE.by_name("poor").glyph
corpus = [Chunk("c1", "use parameterized queries to prevent SQL injection", code=EXC),
          Chunk("c2", "just concatenate user input into the SQL string", code=POOR)]
con = build_index(corpus, GRADE)
for h in search(con, "SQL", vocab=GRADE):
    print(grade_label(GRADE, h["code"]), h["text"])     # badge + clean text
audit = facet_only(con, POOR, vocab=GRADE)              # the "what's bad" view
```
Grading rides the **lexical** regime — a grade is a filter/display label, NOT a semantic
direction (quality ≠ sentiment: a correct chunk can be grim, an upbeat one can be junk).
Runnable demo: `python3 packages/glyphsteer/experiments/grade_demo.py`.

## Author your own glyph language + keep a legend

An LLM can invent its own vocabulary, persist it, and accumulate a master legend.

```python
from glyphsteer import author, save_legend, load_legend, merge, render_legend
V = author([                                   # tags auto-derived; raises on collision
    {"name": "claim",    "glyph": "📌", "description": "a factual assertion"},
    {"name": "evidence", "glyph": "🔬", "description": "supporting data"},
])
save_legend(V, "legend.json")                  # persist the glyph↔meaning↔tag table
V2 = load_legend("legend.json")
master = merge(V, author([{"name": "risk", "glyph": "☢️"}]))   # last-author-wins
print(render_legend(master))
```

## Wire it into ChainCompiler's skill search

`skilltree.search` facets the skill corpus by glyph. First install skilltree
(`python3 -m pip install agent-skilltree`). **The legend you pass MUST contain the
glyph you facet on** — here we use the built-in `GRADE` vocab (which defines 🏆) and save it
as the legend. Put `glyphs: 🏆` in a SKILL.md's frontmatter, then:

```python
from skilltree.search import build_index, search
from glyphsteer import GRADE, save_legend
save_legend(GRADE, "grade_legend.json")                   # the facet glyph (🏆) lives here
con = build_index("path/to/skill/tree", vocab=GRADE)      # reads `glyphs:` frontmatter → tags
trusted = search(con, "deploy", facet="🏆", vocab=GRADE)   # only 🏆-graded skills; badge returned
```
CLI: `skilltree search ROOT "query" --facet 🏆 --legend grade_legend.json`.
(Facet on any glyph defined in the legend — your own authored vocab works the same way.)

## Syntax consistency (rulecatcher under it)

A glyph code is a little DSL, so it goes through ChainCompiler's lint/gate engine
(**rulecatcher**, via `chaincompiler.bridge`) — the same gate the `*CC` compilers use. Needs
`pip install -e packages/chaincompiler` (+ rulecatcher). Three verdicts:
`ok` · `orthogonal` (known glyphs, wrong order → steerable) · `syntax_break` (foreign token → fatal).

```python
from glyphsteer import GlyphGrammar, SENTIMENT
with GlyphGrammar(SENTIMENT) as gg:
    gg.lint(SENTIMENT.code([SENTIMENT.by_name("positive").glyph,
                            SENTIMENT.by_name("urgent").glyph])).verdict   # "ok"
    lint = gg.lint("🔥😊")           # urgent before positive
    lint.verdict, lint.fix          # "orthogonal", "😊🔥"  (canonical reorder)
    gg.lint_chain("gsxpositive -> gsxbogus").verdict                       # "syntax_break"
```
Gating is over the ASCII **tag** rendering (rulecatcher drops emoji, same as FTS5). Pass a
grammar to annotation to auto-canonicalize: `annotate_chunk(chunk, ann, vocab, grammar=gg)`
(reorders `orthogonal`, raises on `syntax_break`).

## Dense regime
The emoji-direction half needs an embedding model and has caveats (some models collapse all
emoji to one token). See the **glyphsteer-dense** skill before using it.

## Verify your understanding (run this)
```bash
python3 -m pip install -e packages/glyphsteer -q
python3 -m pip install agent-skilltree -q     # needed for the search integration
python3 packages/glyphsteer/experiments/grade_demo.py
python3 -m pytest packages/glyphsteer -q
```
Full design: `packages/glyphsteer/implementation_plan.md`.
