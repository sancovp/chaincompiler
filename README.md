<div align="center">

# ChainCompiler

### A compiler-compiler for cognition.

*Define a notation. Gate it so the model never malforms it. Compile it into a universally-loadable skill. Compose those skills. Organize them into a navigable tree. Code validates every step.*

<br/>

**[★ GitHub](https://github.com/sancovp/chaincompiler)** · **[Live site](https://sancovp.github.io/chaincompiler/)** · **[🌼 The Hive Log](https://sancovp.github.io/chaincompiler/blog.html)**

<br/>

![tests](https://img.shields.io/badge/tests-185%20passing-16a34a) ![python](https://img.shields.io/badge/python-3.11%2B-3b6fd4) ![license](https://img.shields.io/badge/license-MIT-3b6fd4) ![type](https://img.shields.io/badge/one%20type-skill%20dir-16a34a) ![status](https://img.shields.io/badge/content%20judged-never-9a9a96)

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

**P0 Foundation** `✓` · **P1 Project Surface** `✓` · **P2 Exchange** `✓` · **P3 Self-Hosting & SI** `✓` · **P4 Marketplace** `▸` · **P5 Federation** `✓` ([plan](FEDERATION.md)) · **P6 Skill OS** `▸` · **P7 Plugin** `▸`

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
<summary><b>🎭 archetype</b> — archetype as a state machine, compiled <i>(the thesis, applied to the psyche)</i></summary>

<br/>

An archetype is **not a noun** but a recursive individuation circuit
`⟨Persona, Shadow, Self, Odyssey, Becoming⟩`: `Shadow = DeniedInverse(Persona)`,
`Self = Integrate(Persona, Shadow)` (a *purified* Persona that bypasses the Shadow
fails **C2**), `Becoming = TypeLift(Self)`. `compile_archetype` infers the missing
aspects from one seed, builds the **multi-journey Odyssey** (a *succession* of hero's
journeys — call-out, one automorphism-encounter per pantheon member, a **post-return**
HJ), tests **quining** (orbit-closure), validates **C1–C6**, and emits Cypher / Prolog /
JSON / readable — or the one type via `emit_skill`. *You don't list archetypes, you
compile the transformation law.*

```bash
archetype compile Hero --substrate "example world" --depth 4 --emit all
archetype demo
```

The state-machine mechanics are G0-by-definition; the music↔archetype frame is a G8
resonance; whether the Becoming-cycle **closes or only tempers** (the comma) is the
open seam. Spec: [ARCHETYPE-COMPILER.md](ARCHETYPE-COMPILER.md).
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

python3 examples/_all/run_all.py   # ⭐ THE everything example — one domain through ALL 10
                                   #    packages, end to end: persona → honeyc → gate →
                                   #    construct → tree → steer → custody → interpret.
                                   #    19/19 checks; the closed algebra, dogfooded.

chaincompiler demo      # construct a 'triage' language: AC + CoR + SC in one call
sccc        demo        # chain an AC + CoR + skill into one SKILL.md
skilltree   demo        # build a cat-breadcrumb tree, walk it, break a crumb → caught
```

> **[`examples/_all`](examples/_all)** is the dogfood: not ten isolated demos, but
> **one artifact built by all ten tools in sequence** — proving every operation
> produces or consumes the same type (a skill dir), so the algebra actually closes.

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
    si/   honeyc/   skillchain-compiler/   glyphsteer/   archetype/
```

`./install.sh` wires every package editable. **SkillTree** is published standalone on PyPI as
**[`agent-skilltree`](https://pypi.org/project/agent-skilltree/)** (the bare name `skilltree` is taken by
an unrelated package) — import name stays `skilltree`; `install.sh` pulls it. Everything else is vendored
in `packages/`.

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
BANDIT      IS A ChainSelector                 (the default COR: select vs construct)
BANDIT      PRODUCES BanditChainSystem         (roll up AC→COR→SC, CLOSE it → a domain persona)
BanditChainSystem  HAS KB, GlyphSteer-self-improve  (the persona builds + reads itself better)
hierarchicalize    PRODUCES SelfView           (BANDIT rolls the move over its OWN parts → granular self)
```

---

## Changelog

### v0.1.44 — 2026-07-10
- **P9 Tome — the chapter rung lands: `skill2framework` + the `framework` package (Move 2 of the nomicon/scalable-publishing incorporation).** New **`packages/framework`** = the chapter rung's deterministic glue: `JourneyCore` + `render_blog1` (the blog-organ law — FILL the model, never hand-write the narrative), `assemble_chapter` (blogs → self-contained chapter dir with relative cross-links/CTAs/manifest), `package_plugin` (framework skill + chapter → installable plugin dir, chapter links repathed + resolution-checked), and `fold_into_tome` — the terminal bind, **delegating to `skilltree.tome.fold` (`agent-skilltree ≥0.3.0`)**: the author's SkillTome is a SkillTree whose volume nodes hold frameworks as generated `## Frameworks` table rows (idempotent code op — no LLM hand-edits the table). Six stage prompt-skills under `skills/skill2framework/` (DIY port of the proven doc-mirror set, score 1.00 FULL_E2E 2026-06-03; inputs adapted to CC-native sources), composed by **`chains/skill2framework.chain`** (skill steps + CoR bridges) and compiled to the rollup `skills/skill2framework/skill2framework/SKILL.md`. Vocabulary: the generated index/router is the **`{aios}-volume`** (SkillVolume; "{aios}-nomicon" is the legacy name). Deterministic spine proven E2E (blog → chapter → plugin → fold → `skilltree validate` green); the framework package ships 5 tests. `install.sh` gains `framework` + bumps `agent-skilltree>=0.3.0`.

### v0.1.43 — 2026-06-29
- **The dependency cycle is cut: chaincompiler now rides a `prompt-engineering` base (cycle → DAG).** The monorepo had a *circular* dependency — `chaincompiler` imported `accc/corcc/sccc` and they imported `chaincompiler` back — with no deterministic prompt engine at the bottom (prompt-making sat *on top of* the rulecatcher grammar tower). Fixed by **dependency inversion**: the standalone **`prompt-engineering`** package is now THE base — `prompt_engineering` carries the deterministic prompt engine + `grammar` (the rulecatcher seam: `learn`/`gate`/`grammar_lines`) + `skillpack` (`write_skill`, now **skilltree-aware** — coordinate-addressed placement). The 7 `*CC` back-edges repoint DOWN onto it; `chaincompiler.bridge`/`skillpack` **re-export** from the base (one implementation, no drift); the layering (`skilltree`/`rulecatcher`/`honeyc` < base < `accc/corcc/sccc` < `chaincompiler`) is enforced by an **import-linter** contract (RED→GREEN was the success signal). The CORCC cue/skeleton format converged onto a base primitive (`cor_skeleton`); `resolve_steps`/seeds correctly stay in the `*CC`. Public API + CLI + `install.sh` unchanged. **185 passing**, GATE-CYCLE GREEN. Full spec: [`REBUILD-SPEC.md`](REBUILD-SPEC.md).

### v0.1.42 — 2026-06-27
- **SkillTree de-duplicated — published standalone as `agent-skilltree`, the bundled copy removed.** `packages/skilltree` was a *stale fork* (v0.1.0) of the canonical standalone (`github.com/sancovp/skilltree`, v0.2.0, which was ahead: `mapper.py` + a bigger `search`/`__init__`; the bundle had nothing unique, `cohere`/`materialize`/`validate` byte-identical). The obvious fix — depend on the published package — was blocked: **the PyPI name `skilltree` is taken by an unrelated `pygame` package.** So SkillTree is now published as **[`agent-skilltree`](https://pypi.org/project/agent-skilltree/)** (import name stays `skilltree`, so every `import skilltree` is unchanged); `chaincompiler` + `si` depend on it, `install.sh` pulls it, and `packages/skilltree` is deleted. The whole suite stays green on the published package (`gba`/`bandit`/`cog`/`si` import it). Also fixed the stale test badge (`120` → the real **182** for `pytest packages/`; SkillTree's own suite now lives in its repo).

### v0.1.41 — 2026-06-18
- **The auto-load mechanism, VERIFIED — and skilltree fixed to match it.** We proved against the live Claude Code runtime exactly what makes SkillTree work (frozen in `.claude/rules/02-the-autoload-mechanism.md`): context + menu = `~/.claude` (always, one layer) **+ every project dir you _Read into_** (its `CLAUDE.md` + `.claude/rules` + `.claude/skills`, dynamically, one layer) — descendants don't load until Read, out-of-project dirs don't trigger, and **the trigger is the Read TOOL, not `cat`** (a Bash `cat` of the same file injects nothing). Three coordinated fixes followed: **(1) breadcrumbs say `Read`, not `cat`** — the generated descend-menus instructed `cat <path>`, which silently fails to load a child; updated the emitter + every breadcrumb parser (`materialize`/`cohere`/`forest`/`exchange`/`validate`/`si`). **(2) `emit` is lossless + journaled + symlink-aware** — tree-ifying a forest now MOVES each skill dir wholesale (all baggage preserved, no body-only re-render, no silent `rmtree`) and **de-symlinks symlink'd skills** (copy the resolved content, journal the link) into `.emit-journal.json`; `unemit` replays it backwards for an exact, byte-identical undo (symlinks restored). **(3) descent-trigger pinned** — Reading a child's nested `SKILL.md` fires that node's layer (ancestors load, descendants don't), so the breadcrumb target is correct as-is. **Dogfooded on our own 8-skill `.claude/skills` forest** (4 real + 4 symlinks): `emit` → only the root remains at the top (melt fixed), COHERENT → `unemit` → byte-identical. The dogfood **caught a real symlink bug** the sandboxes couldn't (4/8 dev skills are symlinks) — found, fixed, frozen (`test_cohere.py`: lossless, symlink, Read-wording, mixed-coord regressions; `test_emit_roundtrip.py`: a baggage+symlink tree-ify→`unemit` byte-identical round-trip; `test_notifications.py`: the decoherence-rule flip). (Full suite **248 passing**.)

### v0.1.40 — 2026-06-18
- **skilltree's missing front half: `discover → cohere → emit` (the filesystem ⇄ tree inverse + the decoherence gate).** `materialize` only went tree → disk (destructively); there was no way to read the *live* `.claude` dirs back, no coherence check, no in-place fix. Added `skilltree.cohere`: **`discover(root)`** reconstructs the tree that is *actually* on disk (handles both a nested AIOS and a bare flat forest); **`cohere(root)`** reports DECOHERENCE — how reality drifted from the engineered shape (`bare_forest`, `uncoordinated`, `stale_breadcrumb`, `coord_drift`, `stray_skill`, `missing_node`); **`emit(root)`** re-coheres IN PLACE (reassign coords + rewrite `cat`-breadcrumbs/index, non-destructive — no `rmtree`), and with `--root-forest` performs the **forest→tree fix**: relocates flat leaves into nested node-dirs so they stop auto-loading and only the root remains, then writes the breadcrumbs. CLI: `skilltree discover|cohere|emit`; `cohere` exits non-zero on drift, so a **cron can notify on decoherence** ("you decohered X — look at the tree shape"). This is rule 01 (`everything-is-a-tree`) made operational: `cohere` *finds* the bare forest, `emit` *roots* it. Frozen as metaformal self-tests (`test_cohere.py`, 4) that trigger the real fs and observe the state-change — the first run caught three real bugs in the code (forest-vs-stray confusion, a plain/coord name mismatch, breadcrumbs pointing at the dir not `SKILL.md`).
- **The decoherence cron + the self-managed notification rule + the `skilltree` skill.** On top of the gate: **`write_notifications(root, rules_dir)`** runs `cohere` and rewrites a self-managed top-level rule **`00-system-notifications`** (default `~/.claude/rules`) — "None. Systems nominal." flips to 🔴 ERROR / 🟡 WARN + a "To fix → run the `skilltree` skill" instruction that leaks into every session's system prompt. **`watch(root, interval)`** is the background loop (every ~5 min); it is **read-only on the tree** (only the rule file changes) — the *fix* stays agent-initiated, because `emit` can relocate real skills. The root is the **user level (`~/.claude`)**, the lord's seat: the top can rewrite a rule that leaks down to every session ("you decohered X — here's the tree shape, recohere it"). New CLI `skilltree notify|watch` and the home-installable **`skilltree` skill** (the recohere flow + navigation how-to = the notification's fix target). Frozen by `test_notifications.py` (×4): trigger the real `cohere→render→write` on a sandbox and observe the rule flip nominal⇄ERROR.
- **`emit`'s tree-ify is now LOSSLESS + REVERSIBLE.** The first cut re-rendered SKILL.md-only and `rmtree`'d the original — silently dropping a skill's other files (a `reference.md`, `scripts/`). Rewritten: it **moves the whole dir** (`shutil.move`, all baggage preserved) and **journals every move** to `.emit-journal.json`; new **`unemit(root)`** / `skilltree unemit` replays the journal backwards for an **exact round-trip** (dirs moved back, SKILL.md restored verbatim, synthesized root + manifest removed, empty nesting pruned). Proven by `test_emit_is_lossless_and_reversible` (a `reference.md` survives `emit` then `unemit`) + a CLI round-trip. The forest→tree fix is now safe to run on a real library — nothing is destroyed, only moved-with-a-receipt. (Full suite **245 passing**.)

### v0.1.39 — 2026-06-18
- **dietc re-expressed as a chaincompiler-built AIOS — the v1 recursion runs (`examples/nutrition`).** dietc was meant to be *the worked example made by the system* but shipped as 11 hand-coded Python modules with **0 skills / 0 chains** — the recursion (*chaincompiler makes dietc*) never ran on it. Now it does: `examples/nutrition/build.py` calls `make_gba("nutrition", aios/, atoms=[gap, cap, safety])` (→ 3 AC attention frames + the NutritionBandit CoR + the rollup SC + the loop flow, coord-addressed) then appends two flow-skills the same way `make_gba` adds the loop flow — **`nutrition-recommend`** (the patch decision, a CoR) and **`compile-day`** (the pipeline SC that *calls* the dietc Python tools: `load → build_day_state → gapcap.compute → patch.plan → safety.check → render`). The split follows the law (**only code what must execute**): dietc's `vectors`/`gapcap`/`patch`/`safety`/`load`/`engine` stay **Python tools** (the math is theirs; a prompt never computes a nutrient value); its *how-to-think* becomes **AC/CoR skills**; its *pipeline* becomes a **walked flow**. dietc's **"NOT medical advice"** is preserved in the role + a `90-safety` rule (always run `safety.check`). Verified by a **metaformal self-test** (`examples/nutrition/test_nutrition_aios.py`): it triggers the real build (observe: closed, 0 violations, `compile-day` coord-addressed at `0.4`, `90-safety` on disk) AND the real dietc pipeline on the `PotatoDay` fixture (a potato-only day → a 1680 kcal gap; the safety check fires) — the substrate is the oracle, no predicted value asserted. The deliverable is the **AIOS template** it reveals (tools in Python · cognition in AC/CoR · pipeline as a walked flow · gated + coord-addressed + self-expanding) — what chaincompiler then applies to itself. (Full suite **235 passing**.)

### v0.1.38 — 2026-06-17
- **Self-expansion + the workflow-as-a-skill + a strict gate (three corrections from the "it's all prompts; Python guarantees shape" pass).** **(1) Self-expansion mechanic** — every dir is automatically an AIOS, so making a skill *obligates* placing it in the tree and (for a domain) AIOS-ing it. Shipped the home-level **`adding-a-skill`** skill (the standing base-agent obligation: gate → place in tree by coord → AIOS a new domain → version it) + a GBA `04-self-expansion` rule pointing at it, and **newest-version routing** in `skilltree.search` (`version:` frontmatter + `search(..., newest_only=True)` / `gba search --newest` forwards only the latest version per logical skill — history kept on disk, latest served). **(2) The GBA's default loop is now a flow-skill IN the tree** (`<domain>-loop`, coord-addressed) instead of only a rule — so uniformly *agent = persona + skills + skillchain + skilltree* (the skillchain lives in the tree, like the COG's flow); rule `01` slimmed to point at it. **(3) Strict gate** — a metaformal self-test observed the gate *admitting* a foreign token at a branch point (the position after `⇒`, legitimately `[`-or-`|`, is ungoverned by confidence-1.0 rules). Fix: opt-in `chaincompiler.bridge.gate(..., strict=True)` + `foreign_tokens(...)` — a closed-class vocabulary check (derived from the learned artifacts) that flags any closed-class token outside the vocab as `syntax_break`; open-class fillers always allowed. Observed GREEN (rejects `❌NOPE❌`, admits the valid chain); frozen as `test_strict_gate.py`. Defaults + the 43 rulecatcher tests untouched. (Full suite **232 passing**.)

### v0.1.37 — 2026-06-17
- **Correction: a COG is a FLOW you WALK, not a function — deleted `run_cog`.** The earlier `cog.py` modeled the COG as a Python orchestrator (`run_cog`) with a `c_admit`/`o_continue` gate that *returned a verdict* — and its tests asserted `admitted is True` where `c_admit = True` was hardcoded (`assert True == True` in a costume; a hallucination). That is the wrong object. The system is **all prompts**; the Python only **guarantees shape** (gate syntax · place names/coords · validate the tree · index for search), used at build time. So `make_cog` now emits the COG as a thing you *travel*: the three **role-AIOS directories** (`C/` `G/` `O/`, each a GBA you `cd` into to learn the role and act) + a shared **`workspace/`** + the **default-workflow flow skill** — a *prompt* (`<domain>-cog`, coord-addressed + validated in the COG's tree) that says *cd C (mint the AC/CoR the work needs → place them in G's tree) → cd G (use them to produce into workspace) → loop C→G → cd O (observe; next cycle's C starts from O's observations)*. There is **no runtime engine**: the agent is the run. `run_cog`/`CogResult` deleted; CLI `cog run` → `cog flow` (prints the flow you walk); `test_cog.py` rewritten as **metaformal self-tests** that OBSERVE the emitted substrate (seats/workspace/flow-skill exist + resolve) rather than assert a stubbed return. Also crystallized the testing methodology itself as the **`metaformal-self-test`** skill (home-level, coord-addressed: `0-metaformal-self-test` / `0.1-gate-rejects-foreign`) — *trigger the real substrate, observe the change, freeze the anecdote; the substrate is the oracle.* It earned its keep immediately: a live gate self-test OBSERVED the Challenger gate **admitting** a foreign token `❌NOPE❌` (a real gap a tautology assert would have hidden). (Full suite **229 passing**.)

### v0.1.36 — 2026-06-17
- **HBA + the COG×HBA variant lattice (`chaincompiler.hba`, `chaincompiler.cog seats=`; DESIGN.md Stages 3–4).** **Stage 3 — the HierarchicalBanditAgent:** a GBA whose `Select`/`Construct` arms delegate to subagents (the anti-melt move — filling a frame excellently needs more domain ACs than fit one window without the geometry flattening, so the *construct-agent* loads that context in its **own** window and returns only the finished skill). Scaffold approach: `make_hba(domain, root, atoms)` emits `.claude/agents/select-agent.md` + `construct-agent.md` (valid subagent defs) + an `01-hba-dispatch.md` rule that **replaces** the inline bandit-loop (`HBA → SelectAgent → (ConstructAgent) → HBA execs`); a real Claude Code agent does the runtime delegation via the Agent tool. Identity (role + dispatch rule + seat defs) is carried as a manifest `_profile` and **survives runtime construct** (fixed `_apply_tree` to preserve `.claude/agents` + the profile across `materialize`'s `rmtree`). CLI `chaincompiler gba hba`. **Stage 4 — the lattice:** `make_cog(..., seats={...})` makes each of `C`/`O`/`G` a GBA or an HBA → the **2³ `PATTERNS`** catalog (`flat` · `G-hba` · `C-hba` · `O-hba` · pairs · `all-hba`); the HBA scaffold lands exactly on the designated seats. **This pattern library is what compoctopus composes.** Ships `test_hba.py` (4) + variant-lattice tests in `test_cog.py`. **The full *downward* algebra (DESIGN §10) is built end-to-end:** GBA → COG-of-GBAs → HBA → variants. (Full suite **230 passing**.)

### v0.1.35 — 2026-06-17
- **COG — a Challenger·Observer·Generator whose three seats are GBAs (`chaincompiler.cog`; DESIGN.md Stage 2).** With the GBA real (v0.1.34), the upward **control stack** (DESIGN §4) gets built: `make_cog(domain, root, atoms)` emits an AIOS with three real GBA seats — `C/` (Challenger), `O/` (Observer), `G/` (Generator) — plus an orchestrator `CLAUDE.md` role block and the `[C→G, G→C, O→C]` protocol as a rule. `run_cog(cog, task)` runs one **in-process** pass: **C·Select** (substantive-term search of G's tree — the stand-in for the LLM's neural-match) decides the arm → **C→G** → **Construct** (mints + persists a new chain into G) or **Exec** (reuses a golden) → **G→C·verify** (the **rulecatcher** gate on the produced sequence — C's back-end) → **O→C·meta** (an injectable Observer that can reject/continue the *strategy* or *final work*). This makes the **two-tier control** real and tested: C admits an artifact at the object level while O can still **veto the strategy** at the meta level (`test_cog.py`, 4). Also `construct_into` now returns the full `BanditChainSystem` (so C can gate its `sequence`), `load_cog` re-opens cold, and CLI `chaincompiler cog new|run`. Seats are in-process here; **subagent dispatch is Stage 3 (HBA)**. (Full suite **224 passing**.)

### v0.1.34 — 2026-06-17
- **GBA — the General BanditAgent as a *persistent* native-CC AIOS (`chaincompiler.gba`; DESIGN.md Stage 1).** The whole stack minted skills into `tempfile.mkdtemp()` and threw them away — a skill-factory with no warehouse and no operator. `make_gba(domain, root, atoms)` fixes that: it emits a real **AIOS directory on disk** — a root `CLAUDE.md` *persona* carrying the **BanditChain loop** (`Task → Recall=Select(search→neural-match) → Decide → Construct|Exec → Reward`), a live `cat`-breadcrumb **SkillTree** (gated AC/CoR/SC bodies), a `kb/`, the `bandit-chain-system` skill loadable in place, and a **persisted, rebuildable FTS5 index** — never `/tmp`. `construct_into(...)` is the Bandit's explore arm made to **persist**: it mints a new chain, **fits it into the live tree, re-materializes, and re-indexes** (the `kb` reward-record and the persona survive the rebuild — `materialize` does `rmtree(root)`, so one `_apply_tree` path preserves the sidecars). `search(...)` is Select's search half (BM25 over the tree; the agent does the neural-match). `load_gba(root)` re-opens one cold from `gba.json`. CLI: `chaincompiler gba new|construct|search`. Ships `test_gba.py` (4: persistence · construct-persists-into-tree · kb/persona survive · cold-reopen). This is **DESIGN.md §10 Stage 1** — an agent goes to the directory and *becomes* the bandit; the warehouse and operator now exist. (Full suite **220 passing**.) Next: Stage 2 — COGs whose seats are GBAs.

### v0.1.33 — 2026-06-17
- **The Archetype Compiler (`packages/archetype`) — the system the music detour was *for*.** `fractran-music` (the verified circle-of-fifths/comma calculation) had been an orphan: a proof of a fact with nothing consuming it. Its consumer is this — an **archetype-as-state-machine** compiler (ARCHETYPE-COMPILER.md spec, now built). An archetype is not a noun but a recursive individuation circuit `⟨Persona, Shadow, Self, Odyssey, Becoming⟩`: `Shadow = DeniedInverse(Persona)`, `Self = Integrate(Persona, Shadow)` (a *purified* Persona that bypasses the Shadow fails **C2**), `Becoming = TypeLift(Self)` (the next archetype's Persona). `arc.compile_archetype("Hero")` infers the missing aspects from one seed, builds the **multi-journey Odyssey** (the spec's main fix: an Odyssey is a *succession* of hero's journeys — a call-out, one automorphism-encounter per pantheon member, and a **post-return** HJ — not a single P→S→Self path), accrues the Aut-web and tests **quining** (orbit-closure), validates **C1–C6**, and emits **Cypher / Prolog / JSON / triples / readable** or the ONE type via `emit_skill` (`<name>/SKILL.md`). Also `compile_chain` (an individuation chain), `compile_world` (a worked example world), the DSL `parse`, and a CLI (`archetype compile Hero --emit all` · `archetype demo`). Ships the **`archetype-compiler` skill** and `test_archetype.py` (11 — the spec's MVP list + the ✦Odyssey-refactor tests). **Grade-honest:** the state-machine mechanics are G0-by-definition; the music↔archetype frame is a G8 resonance; whether the Becoming-cycle **closes exactly or only tempers** (the comma, `fractran-music`) is the explicit open seam, connected at G7/G8 and *not* claimed by `quines()`. (Full suite **216 passing**.)

### v0.1.32 — 2026-06-17
- **P7 — the Claude Code plugin (`▸`).** The repo is now an installable plugin. Added `.claude-plugin/plugin.json` (identity: name `chaincompiler`, MIT, repo/homepage) + `.claude-plugin/marketplace.json` (so `/plugin marketplace add github:sancovp/chaincompiler` resolves, `source: "./"`), a plugin-root `skills/` carrying the **capability** skills (`bandit-chain-system`, `glyphsteer`, `glyphsteer-dense`, `report-missed-skill`), and `.mcp.json` wiring the **Self-Interpreter MCP** (`python3 -m si.server`). One source of truth: the capability skills moved to `skills/` (real dirs — what the plugin loader reads) and are symlinked back into `.claude/skills/` for in-repo dev; the dev-only `chaincompiler` orientation skill stays out of the plugin. Validated by the `plugin-validator` agent: manifests well-formed + consistent, all four skills valid, the loader follows the symlinks on macOS/Linux, and the root `registry.json` (the *skill-tree* federation registry — a different concept) does not conflict. Pending: slash `commands/` + `agents/`, then `git add .claude-plugin/ .mcp.json skills/` + push and an install-verify. (Suite unchanged: **205 passing**.)

### v0.1.31 — 2026-06-17
- **The bandit's headline move: roll up the algebra, close it, make it self-improve (`chaincompiler.bandit`).** The default persona was *named* the ChainSelector but had no construct move of its own — it could only be handed to `construct_language`. `cc.roll_up_algebra(domain, atoms, …)` is that move made real: it mints the domain's **AC(s) + a domain-specialized bandit CoR + SC**, then **CLOSES** the algebra (every artifact is the one type *and* an organizing `SkillTree` validates with zero violations → `system.closed`). The output is a **domain-specific persona AIOS** — a `CLAUDE.md` dir (not a single SKILL.md), shipping `legend.json` (the GlyphSteer GRADE vocab) and a `kb/`, and carrying two standing self-instructions: **build your own KB** (graded per-topic notes) and **improve yourself via GlyphSteer chains** (`🏆`-faceted `Recall`, promote-on-double-🏆, demote-on-❌ — the KB + legend *are* the bandit policy). Then `cc.hierarchicalize(workdir)` applies the **same move over everything the bandit is composed of** (accc · corcc · sccc · glyphsteer · skilltree · si · honeyc · rulecatcher) — a closed chain system per part, assembled into one master `bandit-self` tree: the homoicon, a granular view of the bandit in its own type. Ships the **`bandit-chain-system` skill** (the explicit how-to the bandit loads), `examples/_all/bandit_self.py` (7/7, runs green: roll-up → self-improving persona → 9/9 components closed → self-view validates), and `test_bandit.py`. This answers "have we made skills for everything, and skillchains for chaincompiler, *with* chaincompiler?" — yes: hierarchicalize mints them for every component, using the system itself. (Full suite **205 passing**.)

### v0.1.30 — 2026-06-17
- **The default persona is now the bandit (the `ChainSelector`).** `construct_language` minted a CoR, but you had to *hand it a flavor* (Einstein/Feynman) — and a flavor is a single, already-chosen chain, i.e. a `ChainConstruct` **output**. There was no default for the thing that sits *above* the flavors: the selector that decides whether to construct a chain at all. `corcc.BANDIT` (`= corcc.DEFAULT`) is that persona — a CoR whose moves are the explore/exploit decision: `Task → Recall → Decide(exploit: select a golden chain · explore: construct a new one) → Execute → Reward`. It is compoctopus's `router.py` Bandit (`Link→Chain→Compiler→Bandit`) rendered as a CoR — fitting ChainCompiler's thesis exactly: *the LLM, shaped by the gate, IS the selector*, so the bandit policy is a persona the model reads and performs, not a separate engine. `construct_language(cor_persona=None)` now defaults to it; `examples/_all` mints its default agent with no flavor and asserts the CoR is `BanditChain`. (Full suite 202 passing.)

### v0.1.29 — 2026-06-17
- **`examples/_all` — the everything example (the dogfood).** The repo had ten packages, each with its own passing tests and its own `demo`, but **nothing exercised them together** — the central claim (a *closed algebra over one type*, so every tool's output is the next tool's input) was asserted in prose and never run. `examples/_all/run_all.py` now flows **one domain** (`reviewer`) through **all ten packages** in sequence — `persona → honeyc → gate → construct → tree → steer → custody → interpret` — with **19 assertions across 8 stages**, ending green from a clean `./install.sh`. It produces and consumes only the one type (a `<name>/SKILL.md`) at every seam, so the closure is *demonstrated*, not promised. Shipped with `test_all.py` (CI guard — drift in any package's public API goes red here first) and a `README.md` mapping each stage to its package + what it proves. This is the proof-by-use the system was missing.

### v0.1.28 — 2026-06-17
- **rulecatcher is now vendored — the gate ships with the repo.** It was the one package referenced as an *external dependency* (and the README leaked a local path to it), so a fresh clone could `./install.sh` but then hit `ImportError` the moment the gate ran — the `*CC` constructors, the bridge, and the persona compiler were dead for anyone but the author. `packages/rulecatcher` (zero deps, 43 tests) is now in the monorepo; `install.sh` installs it first, and `chaincompiler demo` runs end-to-end from a clean clone. Removed the external-dependency framing and the local path from the README + `install.sh` + `chaincompiler/pyproject.toml`.

### v0.1.27 — 2026-06-17
- **Landing-page funnel + GitHub links.** Rebuilt `site/index.html` as a long-scroll **benefit funnel** (what each tool *gets you*, not just what it is): a hero, a problem→dream turn, a benefit section per layer (engine · rulecatcher · honeyc · SkillTree · Steward · marketplace), a measured proof bar, then the existing **roadmap + changelog** (still rendered dynamically from `data.json`, now defensive in `app.js`) and a final CTA. A sticky top-nav and footer link straight to **[github.com/sancovp/chaincompiler](https://github.com/sancovp/chaincompiler)** and the Hive Log — the site previously linked to neither. New funnel styling in `site/style.css` (kept the dark theme; the blog is untouched).
- **GlyphSteer gets its own funnel section** — a gold-accented band with the `0.42 → 1.00` retrieval-lift stat, the "two regimes / one tag" cards, and the steer-then-hide promise, deep-linked from the nav.
- **README: demo each thing.** Added **GlyphSteer** (full what-it-is + the sidecar-split + a runnable demo) and **Steward** (the warrant-gated O/F/I/A/P loop) to *The stack, layer by layer*, and a GitHub / live-site / Hive-Log links row under the title.

### v0.1.26 — 2026-06-16

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
| `agent-skilltree` | the organization (published standalone on PyPI; import `skilltree`) | — (own repo) |
| `archetype` | archetype-as-state-machine compiler | 11 |

**182 passing** (`pytest packages/`; SkillTree's own suite now lives in the [`agent-skilltree`](https://pypi.org/project/agent-skilltree/) repo). Anchored by two proofs: `csgn-rulecatcher` (rulecatcher catching a real categorical-notation grammar) and the dense-rune origin docs.

### Not done yet (honestly)

- **`execute` / `search`** — the bandit's other two arms. `construct` is end-to-end; a programmatic `skilltree walk` is sketched, not built.
- **Global install** — nothing auto-loads into real sessions until a tree/language lands in `~/.claude/skills`.

---

## License

**MIT** — see [LICENSE](LICENSE). The pattern is the gift; the code is free to use, fork, and build on.
