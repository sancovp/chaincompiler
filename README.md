<div align="center">

# ChainCompiler

### A compiler-compiler for cognition.

*Define a notation. Gate it so the model never malforms it. Compile it into a universally-loadable skill. Compose those skills. Organize them into a navigable tree. Code validates every step.*

<br/>

**[★ GitHub](https://github.com/sancovp/chaincompiler)** · **[Live site](https://sancovp.github.io/chaincompiler/)** · **[🌼 The Hive Log](https://sancovp.github.io/chaincompiler/blog.html)**

<br/>

![tests](https://img.shields.io/badge/tests-120%20passing-16a34a) ![python](https://img.shields.io/badge/python-3.11%2B-3b6fd4) ![license](https://img.shields.io/badge/license-MIT-3b6fd4) ![type](https://img.shields.io/badge/one%20type-skill%20dir-16a34a) ![status](https://img.shields.io/badge/content%20judged-never-9a9a96)

<br/>

<img src="assets/architecture.svg" alt="ChainCompiler architecture" width="820"/>

</div>

---

## Why

LLMs learn **in-context** — give the model a notation and it thinks in that notation. The hard part was never running one notation; it was *minting, checking, composing, and organizing* them reliably. ChainCompiler is the machine for that. The point isn't any single notation — it's the factory that produces them, with a linter at every seam so the model can't drift out of its own syntax.

> **It is all syntax, by design.** Nothing here judges whether a chain's *content* is good. The compilers guarantee **well-formed, composable, organized** artifacts. Correctness of thought is not their job — and that boundary is load-bearing.

---

## The one idea: a closed algebra over one type

Everything reduces to a single type — the **skill dir** (`<name>/SKILL.md`), the unit any agent auto-loads. Every operation produces or consumes only that type, so composition **closes and recurses**:

```
*CC            constructs   →  skill dir       (lift a notation into the type)
skillchain     composes     →  skill dir       (a skillchain OF skillchains)
SkillTree      organizes    →  skill dirs      (a navigable tree of them)
```

The `*CC`s are *constructors*, `skillchain` is the *composition operator*, `SkillTree` is the *arrangement*, and validators do the job the substrate refuses to.

---

## The loop — every `*CC` runs this

<div align="center">
<img src="assets/loop.svg" alt="learn then gate then compile then package loop" width="760"/>
</div>

---

## Roadmap

<div align="center">
<img src="assets/roadmap.svg" alt="ChainCompiler roadmap" width="900"/>
</div>

**P0 Foundation** `✓` · **P1 Project Surface** `✓` · **P2 Exchange** `✓` · **P3 Self-Hosting & SI** `✓` · **P4 Marketplace** `▸` · **P5 Federation** `✓` ([plan](FEDERATION.md)) · **P6 Skill OS** `▸` · **P7 Plugin** `○`

Full detail in **[ROADMAP.md](ROADMAP.md)** (live on the **[site](site/)**); concrete tasks in **[BACKLOG.md](BACKLOG.md)**. The image and the site are *generated* from [`roadmap.json`](roadmap.json) by [`scripts/update_site.py`](scripts/update_site.py) — edit the data, run the script, everything updates.

---

## The stack, layer by layer

<details>
<summary><b>🐝 rulecatcher</b> — the linter / gate <i>(the engine's left half)</i></summary>

<br/>

Learns a notation's grammar from examples (`catch`), then lints text against it (`lint`) with a two-axis verdict:

- **`orthogonal`** — a known token in the wrong slot → *steerable* (rotate it).
- **`syntax_break`** — a token foreign to the language → *fatal*.

This is the gate that keeps the model writing valid custom syntax. *(Vendored at [`packages/rulecatcher`](packages/rulecatcher) — zero deps, 43 tests.)*

```bash
rulecatcher catch examples.txt --scope mydsl
rulecatcher lint  newtext.txt  --scope mydsl   # non-zero on a violation → CI-gateable
```
</details>

<details>
<summary><b>🍯 honeyc</b> — the compiler <i>(the engine's right half)</i></summary>

<br/>

Parses the **Dense Rune-Chain** glyph notation (`🌸‍💧 → 🍯 → 🍹`) into an AST, then renders it through lenses: triples, Prolog, Cypher, prose. `dietc` (a modular-nutrition compiler) rides on top — proof that honeyc hosts arbitrary domain compilers.

```bash
honeyc norm   examples/mbr.rune
honeyc render examples/mbr.rune --as prose
```
</details>

<details>
<summary><b>⛓️ ChainCompiler</b> — the substrate + umbrella <i>(this package)</i></summary>

<br/>

Wires the linter + compiler into the `learn → gate → compile` loop, writes the result as a `SKILL.md`, and exposes the top-door `construct_language()`. One name over the whole stack.

```bash
chaincompiler layers     # print the stack
chaincompiler demo       # mint a whole 'triage' cognition-language in one call
```
</details>

<details>
<summary><b>🎯 ACCC</b> — Attention Chains <i>(the atom)</i></summary>

<br/>

An **attention chain** is *inner* — a silent template for **how to think** about something (a scaffold for a section or your thinking). Not necessarily spoken.

```rune
[Symptom] ⇒ [Repro] ⇒ [Hypothesis] ⇒ |Localize|
```

`forge()` mints a *new* AC language (the compiler-compiler move); `gate()` lints it; `package()` emits the skill dir.
</details>

<details>
<summary><b>🗣️ CORCC</b> — Chains of Reasoning <i>(spoken; HAS an AC)</i></summary>

<br/>

A **CoR** is a *spoken, paragraphical AC that makes a decision*. Same chain, two registers: the inner AC (silent) generates it; the outer CoR is the paragraph the model says. The lint is the only check — a malformed CoR means the model drifted out of syntax ("melting").

```rune
[Invariants] ⇒ [ThoughtExperiment] ⇒ [Simplicity] ⇒ |Reframe|   # ThinkLikeEinstein
```
</details>

<details>
<summary><b>🧩 SCCC</b> — Skill Chains <i>(the highest composite)</i></summary>

<br/>

An **SC** chains ACs + CoRs + **regular skills** into a sequence, rolled up into one `SKILL.md`. Because everything is a skill dir, an **SC can chain another SC** — the algebra closes.

```rune
[ac:debug-attn] ⇒ [cor:thinklikeeinstein] ⇒ [skill:summarize] ⇒ |Answer|
```
</details>

<details>
<summary><b>🌳 SkillTree</b> — the organization <i>(progressive disclosure in the filesystem)</i></summary>

<br/>

See the next section — it has its own diagram and a live example.
</details>

<details>
<summary><b>🐝 GlyphSteer</b> — dual-regime retrieval steering <i>(P8 research; the flagship)</i></summary>

<br/>

**What it is.** An LLM annotates a corpus with a *compiled, controlled glyph vocabulary*. Those markers steer retrieval in **two regimes at once** — **lexically** (a rare ASCII tag = a maximal-IDF exact-match facet) and **densely** (an emoji carries a learned direction that nudges the chunk's embedding) — and are then **stripped from the returned text** (the *sidecar split*: indexed-form ≠ returned-form, a hard, tested HIDE invariant). It is HoneyC pointed at the index instead of Prolog, and the cousin of Anthropic's *Contextual Retrieval* — but with a queryable, faceted controlled vocabulary instead of free text.

```
indexed-form  = clean_text ⊕ glyph_code   → embedded / FTS5-indexed   (MATCHING)
returned-form = clean_text                 → handed to the reader      (READING)
```

**The benefit.** The exact result you want is pinned to the top — without a smarter query — and the machinery never leaks into the output. **Measured lexical lift: MRR 0.417 → 1.000** on the toy sentiment-faceted corpus.

**Demo:**

```python
from glyphsteer import SENTIMENT, Chunk, RuleAnnotator, annotate_chunk, build_index, search

ann = RuleAnnotator.keyword(SENTIMENT, {
    SENTIMENT.by_name("negative").glyph: ["failed", "broke", "terrible"],
    SENTIMENT.by_name("positive").glyph: ["great", "excellent", "succeeded"],
})
chunks = [annotate_chunk(Chunk(c.id, c.text), ann, SENTIMENT) for c in corpus]
con = build_index(chunks)
hits = search(con, "deployment", facet=SENTIMENT.by_name("negative").glyph)
# hits[i]["text"] is CLEAN — the glyph steered the match but never reaches the reader
```

```bash
pip install -e packages/glyphsteer            # lexical regime, zero heavy deps
pip install -e 'packages/glyphsteer[dense]'   # + the dense regime
glyphsteer query corpus.jsonl "deployment" -f 😡
```

**Verified finding:** FTS5's `unicode61` tokenizer **drops emoji**, so one *axis* carries two renderings — an emoji `glyph` (dense direction) + an ASCII `tag` (lexical facet). The dense regime ships as an ONNX/fastembed Docker sidecar (no torch); Q1–Q3 are measured and the emoji-direction is real but **model-dependent** (`bge-en` collapses all emoji to one token; a byte-aware XLM-R model separates them). See [`packages/glyphsteer/README.md`](packages/glyphsteer/README.md).
</details>

<details>
<summary><b>🛡️ Steward</b> — a warrant-gated loop-runner <i>(the Custodian genus, lowest rung)</i></summary>

<br/>

A **Steward** runs the **O → F → I → A → P** loop (observe · frame · integrate · authenticity · predict) and produces the one type — a skill-dir `Artifact`. The **A-stage is the LOCK**: it freezes a **warrant** and either admits/crystallizes the result or rejects it. So automation only acts *when it has earned the right*.

It composes: a base `Steward` → specialist Stewards (`chain` / `sm` / `compiler` / `core`) → a `meta_steward` that runs a *sequence* of Stewards — **presents as one, runs many** (homoiconic, so meta-Stewards nest). The warrant has a **fidelity tier** (`proto_soma` regex → `grammar` rulecatcher/GlyphSteer → `soma`); the same loop swaps tiers unchanged.

This is the headless/automation sibling of CCC's Cybernet (same Custodian genus). Canonical design + the bijection in [`packages/steward/DESIGN.md`](packages/steward/DESIGN.md).
</details>

---

## SkillTree — a tree you `cat` your way down

Claude Code auto-loads **only the root** `.claude/skills/` and **won't descend** into a nested `.claude`. So the tree lives in **`cat`-breadcrumbs**: each node's `SKILL.md` body hands you the `cat` command for its children. Load one root, walk to the exact leaf you need — nothing else pollutes context. It's progressive disclosure implemented in the filesystem, **JSON-driven**, and **validated** (the platform never checks the breadcrumbs — so we do).

<div align="center">
<img src="assets/skilltree.svg" alt="SkillTree cat-breadcrumb structure" width="760"/>
</div>

<details>
<summary><b>The real <code>cc_tree_test</code> — on disk</b></summary>

<br/>

```
cc_tree_test/
  .claude/skills/cc-skill-tree/SKILL.md          ← root (the ONLY thing that auto-loads)
  reason/.claude/skills/reason/SKILL.md
  reason/thinklikeeinstein/.claude/skills/thinklikeeinstein/SKILL.md   ← real CoR leaf
  reason/simplify-attn/.claude/skills/simplify-attn/SKILL.md
  debug/.claude/skills/debug/SKILL.md
  debug/debug-attn/.claude/skills/debug-attn/SKILL.md                  ← real AC leaf
```

The root's body — the breadcrumbs:

```markdown
## Descend — the next layer (2)
Auto-load stops here (nested `.claude` will not load). To go deeper, run the `cat`:

- reason (cor): `cat /…/cc_tree_test/reason/.claude/skills/reason/SKILL.md`
- debug  (cor): `cat /…/cc_tree_test/debug/.claude/skills/debug/SKILL.md`
```
</details>

```bash
skilltree build cc_tree_test.manifest.json cc_tree_test   # JSON → tree, then validate
skilltree validate cc_tree_test                            # every breadcrumb must resolve
```

The manifest is the org chart — **edit it however you want, rebuild, and every breadcrumb + dir regenerates.**

---

## Quickstart

```bash
# install every package in the monorepo, editable — rulecatcher included.
# one clone, one command, no external setup.
./install.sh            # pip install -e packages/* (no-deps)

chaincompiler demo      # construct a 'triage' language: AC + CoR + SC in one call
sccc        demo        # chain an AC + CoR + skill into one SKILL.md
skilltree   demo        # build a cat-breadcrumb tree, walk it, break a crumb → caught
```

```python
import chaincompiler as cc
from corcc.notation import EINSTEIN
bundle = cc.construct_language(
    "triage",
    ac_chain="[Symptom] ⇒ [Scope] ⇒ |Severity|",
    cor_persona=EINSTEIN,
    db=".cc.db", skills_dir="skills", out_dir="dist",
)   # → bundle.ac / bundle.cor / bundle.sc  (three SKILL.md packages)
```

---

## Repo layout

```
chaincompiler/                 # the monorepo (this repo)
  README · ROADMAP · FEDERATION · roadmap.json   # project surface
  assets/ · site/ · scripts/ · .github/          # roadmap SVG, site, generators, deploy
  packages/
    rulecatcher/                                   # the gate (vendored; zero deps)
    chaincompiler/   accc/   corcc/   sccc/       # substrate + the three layers
    skilltree/   si/   honeyc/   skillchain-compiler/   glyphsteer/   steward/
```

Everything is vendored in `packages/` — `./install.sh` wires it all editable, no external setup.

---

## The formal spec

```
SKILL_DIR   IS A <name>/SKILL.md            (self-describing, auto-loadable)
AC          IS A attention-template          (how to think; inner, silent)
COR         IS A spoken AC that decides       →  COR HAS AC
SC          IS A sequence                      →  SC HAS COR, AC, skills
*CC         IS A syntax compiler               →  *CC PRODUCES SKILL_DIR
skillchain  PRODUCES SKILL_DIR from SKILL_DIRs (composition closes)
SkillTree   IS A tree of SKILL_DIRs            (wired by cat-breadcrumbs)
```

---

## Changelog

### v0.1.28 — 2026-06-17
- **rulecatcher is now vendored — the gate ships with the repo.** It was the one package referenced as an *external dependency* (and the README leaked a local path to it), so a fresh clone could `./install.sh` but then hit `ImportError` the moment the gate ran — the `*CC` constructors, the bridge, and the persona compiler were dead for anyone but the author. `packages/rulecatcher` (zero deps, 43 tests) is now in the monorepo; `install.sh` installs it first, and `chaincompiler demo` runs end-to-end from a clean clone. Removed the external-dependency framing and the local path from the README + `install.sh` + `chaincompiler/pyproject.toml`.

### v0.1.27 — 2026-06-17
- **Landing-page funnel + GitHub links.** Rebuilt `site/index.html` as a long-scroll **benefit funnel** (what each tool *gets you*, not just what it is): a hero, a problem→dream turn, a benefit section per layer (engine · rulecatcher · honeyc · SkillTree · Steward · marketplace), a measured proof bar, then the existing **roadmap + changelog** (still rendered dynamically from `data.json`, now defensive in `app.js`) and a final CTA. A sticky top-nav and footer link straight to **[github.com/sancovp/chaincompiler](https://github.com/sancovp/chaincompiler)** and the Hive Log — the site previously linked to neither. New funnel styling in `site/style.css` (kept the dark theme; the blog is untouched).
- **GlyphSteer gets its own funnel section** — a gold-accented band with the `0.42 → 1.00` retrieval-lift stat, the "two regimes / one tag" cards, and the steer-then-hide promise, deep-linked from the nav.
- **README: demo each thing.** Added **GlyphSteer** (full what-it-is + the sidecar-split + a runnable demo) and **Steward** (the warrant-gated O/F/I/A/P loop) to *The stack, layer by layer*, and a GitHub / live-site / Hive-Log links row under the title.

### v0.1.26 — 2026-06-16
- **The Steward layer — the Custodian genus, lowest rung (off-graph).** `packages/steward`: a **Steward** = a loop-runner (O/F/I/A/P) gated by a **warrant**, producing the one type (a skill-dir `Artifact`); the **A-stage is the LOCK** (warrant-freeze → admit/crystallize or reject). This is the headless/automation sibling of CCC's Cybernet (same Custodian genus, CCC `DESIGN.md §2.1`), built bottom-up: base `Steward` → specialist Stewards (`chain`/`sm`/`compiler`/`core`) → `meta_steward` (a Steward that runs a *sequence* of Stewards — **presents as one, runs many**; homoiconic, so meta-Stewards nest). The **warrant has a fidelity tier** (`proto_soma` regex → `grammar` rulecatcher/GlyphSteer → `soma`) — the same loop swaps tiers unchanged, demonstrating the warrant-upgrade axis the CCC merge wants. 7 tests green. Canonical design + the CCC bijection in `packages/steward/DESIGN.md`. **Committed next-conversation work: implement the same hierarchy INTO CCC on the graph (Steward→Cybernet, warrant regex→rulecatcher→SOMA).**

### v0.1.25 — 2026-06-16
- **The Hive Log — a blog series on the site, in BizziBee's voice.** `site/blog.html` + `site/blog.js` + `site/blog.json` (generated by `scripts/build_blog.py`) tell the whole nectar-run as 10 posts: the emoji-direction awakening → the sidecar split (steer-then-hide) → the ONNX/no-torch container → the two findings that nearly killed it (FTS5/`[UNK]` emoji collapse + the one-env-var fix) → corpus grading → the LLM-authored legend → rulecatcher syntax gating → the BizziBee recognition (the plan) → the persona compiler closing the loop → an honest "what's solid / what's a knob / what's aspirational" ledger. Linked from the roadmap header; styled to match; numbers are the measured numbers.

### v0.1.24 — 2026-06-16
- **Persona compiler — the front-end that closes the loop on its own origin.** A BizziBee-style glyph-persona-prompt is a *program* in a cognition-DSL with three layers, and ChainCompiler now compiles each: `[VarDefs]` → a **glyphsteer legend** (glyph↔meaning), `🌸‍💧→🍯→🍹` dense-rune chains → **HoneyC**/**rulecatcher** (gate), `⚙️0–5` (`if`/`while`/`for`/`🔁`/terminal) → an extracted **workflow** (executable via the SI — aspirational), and `[ROLE]…[/ROLE]` → a **SKILL.md**. `chaincompiler.persona.compile_persona` + CLI `cc persona FILE --out DIR` parse the prompt into `<cogid>/SKILL.md` + `legend.json` + a rulecatcher-gated chain — putting the persona *inside the closed algebra*.
  - Verified on the original BizziBee prompt (`packages/chaincompiler/examples/bizzibee.txt`): extracts a 5-axis legend (incl. the ZWJ rune `🌸‍💧`=NectarWF as one glyph), 8 ⚙️ steps with detected control flow, a compiled SKILL.md, and gates a legend chain → `ok`. 11 chaincompiler tests green (91 across the repo).

### v0.1.23 — 2026-06-16
- **GlyphSteer syntax consistency via rulecatcher.** A glyph code is a little DSL, so it now goes through ChainCompiler's lint/gate engine (**rulecatcher**, via `chaincompiler.bridge`) — the same gate the `*CC` compilers use, making GlyphSteer's notation consistent with the rest of the system. New `glyphsteer.grammar.GlyphGrammar`: learns the grammar of canonical codes, then lints any code/tag-chain to one of three verdicts — `ok` · `orthogonal` (known glyphs, wrong order → `canonicalize` reorders to vocab order) · `syntax_break` (foreign token → fatal; rulecatcher owns this). Gating is over the ASCII **tag** rendering (rulecatcher drops emoji, same lesson as FTS5/dense). Optional-wired into `annotate_chunk(..., grammar=gg)` (repairs `orthogonal`, raises on `syntax_break`). Engine imported lazily so plain GlyphSteer never needs it; the `grammar` extra + sibling `chaincompiler` enable it. 37 glyphsteer tests green.

### v0.1.22 — 2026-06-16
- **GlyphSteer usage skills + subagent-verified.** Added two repo-level skills — `.claude/skills/glyphsteer` (lexical core, grading, legend authoring, the skilltree-search integration) and `.claude/skills/glyphsteer-dense` (the ONNX sidecar, the emoji-collapse gate, the magnitude probe, the anchor reshape). Both were tested end-to-end by a fresh subagent that used *only* the skills; two iteration rounds drove them to **every code/CLI snippet running verbatim** (fixes: added the `skilltree` install step, made the integration example's legend contain its facet glyph, widened the Q2 range to admit slightly-negative nudges, run-from-repo-root note).
  - Code fix the subagent caught: `eval.magnitude_probe` reported a stale hardcoded model label; it now reports the model actually serving embeddings (`dense.active_model()` → the sidecar's `/health`), so the results JSON is honest. Results regenerated. 74 tests green.

### v0.1.21 — 2026-06-16
- **GlyphSteer legend + ChainCompiler search integration.** An LLM can now *invent* a glyph language, persist it, and search by it.
  - **Legend** (`legend.py`): `author([{name,glyph,description}])` (tag auto-derived) → `save_legend`/`load_legend` (JSON) → `merge` several into a master legend (last-author-wins) → `render_legend` for display. The glyph↔meaning↔tag table the model invents and keeps across sessions.
  - **Wired into `skilltree.search`** (the ChainCompiler search arm): `build_index(root, vocab=...)` reads each skill's `glyphs:` frontmatter → faceted ASCII-tag column; `search(con, q, facet=🏆, vocab=...)` filters by glyph and returns the badge; CLI `skilltree search ROOT Q --facet 🏆 --legend l.json`. Fully backward compatible (`vocab=None` ⇒ unchanged). 74 tests green (glyphsteer 31 + skilltree 43).

### v0.1.20 — 2026-06-16
- **GlyphSteer: corpus grading** (the flagship lexical use). New built-in `GRADE` vocabulary (🏆 excellent / ✅ good / ⚠️ fair / ❌ poor) + `grade_label` + `GRADE_RANK`: an LLM grades "what's good and what isn't", and **search shows the grade** on every hit and can **facet** to a grade (`experiments/grade_demo.py`). Grading deliberately rides the **lexical** regime — a grade is a filter/display label, not a semantic direction (quality ≠ sentiment).
  - The index now carries the emoji `glyphs` (UNINDEXED, for display) alongside the ASCII `code` tags (INDEXED, for faceting), so hits return a human grade badge while the body text stays clean.
  - Robustness fix: `_fts_query` quotes each term, so FTS5 operators (`OR`/`AND`/`NOT`) appearing in user queries are treated as literals. 25 tests green.

### v0.1.19 — 2026-06-16
- **GlyphSteer dense sidecar + measured results.** Containerized the dense regime: `packages/glyphsteer/serve` is a Docker image (FastAPI + **fastembed → onnxruntime, no torch**, ~888MB, model pre-cached) exposing `/embed` over HTTP; the host `dense.py` gained a stdlib-only **remote backend** (+ fastembed/sentence-transformers local fallbacks), so the heavy runtime runs sidecar and the host stays light.
  - **THE finding (model-dependent emoji direction):** `bge-small-en-v1.5` maps *every* emoji to one token — all distinct emoji embed to pairwise cosine **1.000** (emoji-blind, dense claim impossible). A byte-aware multilingual model (`paraphrase-multilingual-MiniLM-L12-v2`, XLM-R) gives distinct emoji (0.77–0.97) and clean **Q1 separation +0.28…+0.58**. Caught by the probe, fixed by a one-env-var model swap — the reason the sidecar is swappable.
  - **Measured (byte-aware model):** Q1 alignment strong; Q2 per-token nudge modest (+0.02…+0.09 Δcos); Q3 anchor reshape a controllable ×2 gain at weight 1. Lexical Q4 unchanged (MRR 0.417→1.000). Artifacts in `experiments/results/`.
  - New dev-workflows DW-6 (emoji-collapse gate) + DW-7 (stand up the sidecar) and a sidecar component+sequence diagram in `.claude/rules`. 22 tests green.

### v0.1.18 — 2026-06-16
- **GlyphSteer** (`packages/glyphsteer`, P8 research) — dual-regime retrieval steering via compiled in-band glyph annotations. An LLM annotation pass writes a *controlled glyph vocabulary* onto a corpus; the markers steer retrieval **lexically** (a rare ASCII sentinel = maximal-IDF exact-match facet) and **densely** (an emoji's learned direction nudges the chunk vector), then are **stripped from the returned text** (the *sidecar split*: indexed-form ≠ returned-form, with a hard HIDE invariant). It is HoneyC pointed at the index (a glyph code is a HoneyC chain) and the cousin of Anthropic's Contextual Retrieval, with a *compiled, faceted controlled vocabulary* instead of free text.
  - **Verified finding:** FTS5's `unicode61` tokenizer **drops emoji** → one `Axis` carries two renderings: an emoji `glyph` (dense) + an ASCII `tag` (lexical). Captured as a regression test + dev-workflow DW-1.
  - **Lexical result:** retrieval lift MRR **0.417 → 1.000** on the toy sentiment-faceted corpus (`experiments/retrieval_lift.py`), zero deps. Dense magnitude probe (Q1–Q3) built, gated on the `[dense]` extra.
  - Ships `implementation_plan.md` (canonical), `.claude/rules` (write-down-everything meta-rule + component/flow Mermaid diagrams + discovered dev workflows), and the `glyphsteer` skill. 18 tests green.

### v0.1.17 — 2026-06-16
- **Backlog** — recorded the next search-arm direction (**anchor-based dynamic embedding geometry**, to be specified) and a re-materialize note for the live tree (to carry the new branch summaries).

### v0.1.16 — 2026-06-16
- **Template node-summaries** (`skilltree.model.compose_summary`) — every index/branch node gets a *deterministic* subtree summary (its coord + children + reachable descendants) baked into its body + used as its description. This is RAPTOR's "internal nodes carry a summary" retrieval-win **with no LLM**: a branch is now retrievable by any descendant's terms (search "symptom-localizer" surfaces the `debug` branch that leads to it). Closes the search-arm caveat from the research.

### v0.1.15 — 2026-06-16
- **Search arm** (the bandit's third arm) — `skilltree.search`: SQLite **FTS5/BM25** over the skill corpus + **coordinate-scoped subtree** search (rank within any `0.1`-rooted region), exposed as `skilltree search` and the **`si_search` MCP tool**. Research-scoped (3 arxiv scouts): FTS5+coord-scope now; dense/vector (RRF) + MCTS deferred as evidence-driven — see BACKLOG.

### v0.1.14 — 2026-06-16
- **`.claude/rules` + `.claude/skills`** in the repo. Rules: `00-keeping-roadmap-and-backlog-current` (the enforced discipline), `10-architecture-components` (mermaid component diagrams — full stack, the closed algebra, the Skill OS rings, the package graph), `20-architecture-flows` (mermaid sequence diagrams — the compiler loop, `construct_language`, SkillTree surface→cat, the contribution gate, the federation walk, the Skill OS loop). Skills: a `chaincompiler` repo-orientation skill + `report-missed-skill` surfaced.

### v0.1.13 — 2026-06-16
- **Roadmap P7 — Plugin** (bundle the whole thing as one Claude Code plugin) + a living **[BACKLOG.md](BACKLOG.md)** tracking the concrete tasks under each phase (P6 analytics-hook / frontend / improve-loop, P7 plugin, the aspirational tails, and "tree-ify the real ~/.claude/skills library").

### v0.1.12 — 2026-06-16
- **P6 Skill OS — the keystone: `report-missed-skill`** + the reports store (`skilltree.reports`): `report_missed` / `mark_problem` / `list_reports` / `summary` / `resolve`, CLI (`skilltree report-missed` / `mark-problem` / `reports`), and the shipped `report-missed-skill` skill (installed live). The agent (or the user) files missing/expected-but-unused skills into `~/.claude/skill-reports.json`; an improver agent reads the open queue and creates/improves skills. The system grows from its own gaps. (3 tests.)

### v0.1.11 — 2026-06-16
- **Coordinate addressing** — `assign_coords` gives every node a hierarchical address (root `0`, children `0.1`/`0.2`, grandchildren `0.1.1`…). `materialize(..., coords=True)` prefixes the coord onto each skill's **frontmatter `name` + dir** (`0.1-reason`), so the flat `~/.claude/skills` list is coord-sorted, reveals the tree, and every node is addressable by its coordinate. `link_tree` surfaces the coord-named symlinks at the top. Coords off by default (backward-compatible). (4 tests.)

### v0.1.10 — 2026-06-16
- **Surface trees from the top** — `skilltree.forest`: `link_tree` symlinks a tree's root + first-layer branches into the top-level `~/.claude/skills` (so it's visible in every session; deeper levels stay behind `cat` = progressive disclosure), `build_forest` makes one forest-root over many trees, plus `list_links`/`unlink`. Verified the auto-load rule empirically (probe): a `.claude/skills` *inside a skill dir* is NOT scanned (non-recursive), so the `cat`-breadcrumb tree is the right workaround — confirmed, not redundant. (3 tests.)

### v0.1.9 — 2026-06-16
- **P5.4 federation walk** — `skilltree.federation`: a child marketplace joins by a `registry`-kind entry pointing at its `registry.json`; `walk_federation` / `flatten_federation` traverse the tree of marketplaces under a root (pluggable `resolve`, so it works offline), `validate_federation` catches cycles + unresolved children + parent-backref mismatches, and `register_child` adds a federation link (unverified). **P5 Federation complete** (reputation/hosted-discovery remain aspirational). (5 tests.)

### v0.1.8 — 2026-06-16
- **P5.2 contribution flow** — the marketplace is now a git repo: `registry.json` (root, `parent: null`), `skilltree.registry` (schema + `validate_contribution` + maintainer-only `promote` + trust-floor `search`), `scripts/validate_registry.py` (self-contained CI gate) and `scripts/promote.py`, plus `.github/workflows/contribute.yml` — fork-safe `pull_request` (read-only, no secrets), runs the **base** gate against the PR's data. Contributions may only ADD `unverified` entries with provenance; trust changes / removals / re-parenting are blocked. (7 tests.)

### v0.1.7 — 2026-06-16
- **MIT license** — `LICENSE` added (open-core stance: the pattern/library is MIT; monetization belongs to the moat-bearing layer, e.g. a hosted federated marketplace).

### v0.1.6 — 2026-06-16
- **Public + Pages live** — the repo is public and the roadmap site deploys to GitHub Pages at https://sancovp.github.io/chaincompiler/. The `deploy` job now runs (it was skipped while private); the changelog-gated, self-regenerating pipeline is live end-to-end.

### v0.1.5 — 2026-06-16
- **P5.1 repo scaffolder** — `si.scaffold_repo`: stamp a ChainCompiler-shaped *node repo* from a skill tree (the tree + a federated `registry.json` + a runnable `serve_mcp.py` + README) with `validate_node`. The fractal made real: each emitted MCP becomes a repo whose marketplace federates under the parent. (3 tests.)

### v0.1.4 — 2026-06-16
- **Monorepo + published** — consolidated the 8 packages under `packages/` (rulecatcher stays an external dep), `install.sh`, and pushed to a private GitHub repo. 117 tests green post-move.
- **Deploy workflow decoupled** — split into a `validate` job (changelog gate + regenerate + staleness, runs on every push) and a `deploy` job gated on public visibility (Pages needs a public repo), so private pushes stay green.

### v0.1.3 — 2026-06-16
- **P5 Federation** — *planned*: design locked in **[FEDERATION.md](FEDERATION.md)**. Each emitted MCP becomes a ChainCompiler-shaped repo; the marketplace **is a git repo** (registry = `registry.json`, contribute = PR); contributions are **validated + queued + gated-promote** (no auto-merge); public skills are **untrusted by default** (SKILL.md = agent instructions = injection surface).

### v0.1.2 — 2026-06-16
- **P3 Self-Hosting & Self-Interpreter** ✓ — `si`: a chain-dialect interpreter (a Python dialect; defers to native ops), the tree-walk **execute** arm, `tree_to_mcp`, and an **SI MCP server that is also a skill** (`python -m si.server`, 5 tools). `construct_language` runs *inside* the dialect → ChainCompiler self-hosts.
- **P4 Marketplace** ▸ — `skilltree.marketplace`: programmatic `publish`/`search`, opt-in `public`, and a `notify` hook where a hosted service plugs in (hosted endpoint + cross-user discovery still aspirational).

### v0.1.1 — 2026-06-16
- **P1 Project Surface** ✓ — roadmap (SVG from data), dynamic site, changelog, `update_site.py`, changelog-gated deploy workflow.
- **P2 Exchange** ✓ — `skilltree.exchange`: a JSON/YAML manifest holds many skill trees under a master (a tree of trees); `build` + `validate`. CLI: `skilltree exchange build/validate`.

### v0.1.0 — 2026-06-16
- Foundation complete: `rulecatcher`, `honeyc`/`dietc`, `ChainCompiler`, `ACCC`/`CORCC`/`SCCC`, `SkillTree` — 107 tests.
- `construct_language()` mints a domain's AC + CoR + SC in one call.
- `SkillTree`: `cat`-breadcrumb trees from JSON with a validator; live `cc_tree_test`.
- Project surface: roadmap (SVG generated from data), dynamic website, this changelog, `update_site.py`, changelog-gated deploy workflow.

---

## Status

| package | is | tests |
|---|---|---|
| `rulecatcher` | the linter / gate | 43 |
| `honeyc` (+ `dietc`) | the compiler (+ domain proof) | 36 |
| `chaincompiler` | substrate + umbrella | 6 |
| `accc` / `corcc` / `sccc` | the three layers | 5 / 5 / 6 |
| `skilltree` | the organization | 6 |

**~107 passing.** Anchored by two proofs: `csgn-rulecatcher` (rulecatcher catching a real categorical-notation grammar) and the dense-rune origin docs.

### Not done yet (honestly)

- **`execute` / `search`** — the bandit's other two arms. `construct` is end-to-end; a programmatic `skilltree walk` is sketched, not built.
- **Global install** — nothing auto-loads into real sessions until a tree/language lands in `~/.claude/skills`.

---

## License

**MIT** — see [LICENSE](LICENSE). The pattern is the gift; the code is free to use, fork, and build on.
