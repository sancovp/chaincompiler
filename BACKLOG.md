# Backlog

The living task list. High-level phases live in [ROADMAP.md](ROADMAP.md) (generated
from [`roadmap.json`](roadmap.json)); this is the concrete, checkable to-do under them.

> Convention: `[ ]` todo · `[~]` in progress · `[x]` done. Keep it current — every
> PR that finishes an item checks it here and adds a changelog entry in the README.

---

## P6 — Skill OS  `▸`

- [x] `report-missed-skill` + reports store (`skilltree.reports`, CLI, shipped skill, installed live)
- [x] Coordinate addressing (`assign_coords`, `materialize(coords=True)`, coord-named symlinks)
- [ ] **Analytics** — a Claude Code hook (PostToolUse on the Skill tool) that logs each skill invocation into the reports store → usage counts + powers "expected but not used"
- [ ] **Frontend** — a dashboard (reuse the site infra) showing the tree + usage analytics + open reports, with problem-marking; launched from the canonical root skill
- [ ] **Improve loop** — an agent that reads the open report queue (`skilltree reports`), runs Anthropic's skill-improver or creates the missing skill, then `resolve`s the report
- [x] **Discover ⇄ cohere ⇄ emit** (`skilltree.cohere`) — the filesystem→tree inverse of `materialize` + the decoherence gate. `discover` reads the live `.claude` dirs back into a tree; `cohere` reports drift (bare_forest/stale_breadcrumb/coord_drift/stray/missing); `emit` re-coheres in place (and `--root-forest` relocates flat leaves into a nested tree). CLI exits non-zero on drift → cron-notifiable. The operational form of rule 01. (`test_cohere.py`, 4 metaformal)
- [x] **Auto-load mechanism VERIFIED + skilltree fixed to it** (rule `02-the-autoload-mechanism`) — proved against the live runtime: Read-into-a-project-dir injects its `CLAUDE.md`+rules+skills (one layer; descendants don't load; the trigger is the Read TOOL, not `cat`). Fixes: **(1)** breadcrumbs say `Read` not `cat` (emitter + all parsers: materialize/cohere/forest/exchange/validate/si); **(2)** `emit` lossless + journaled + **symlink-aware** (de-symlink → copy resolved content + journal; `unemit` = exact byte-identical undo); **(3)** descent-trigger pinned (nested `SKILL.md` fires on Read). Dogfooded on the real 8-skill dev forest (4 real + 4 symlinks) → only the root remains, COHERENT, round-trip identical. Caught a real symlink bug the sandboxes missed. (`test_cohere.py` now 8 metaformal)
- [x] **Decoherence cron (capability)** — `write_notifications`/`watch` + CLI `skilltree notify|watch` rewrite a self-managed top-level rule `00-system-notifications` (`~/.claude/rules`): nominal ⇄ 🔴/🟡 + "To fix → run the `skilltree` skill". Read-only on the tree; leaks the verdict into every session. Home-installable `skilltree` skill = the fix target. (`test_notifications.py`, 4 metaformal)
- [ ] **Start the live cron on `~/.claude`** — run `skilltree watch ~/.claude` as a background process so the real user-level forest is watched. *Pending: the author's go (writes a real always-on rule; treeifying `~/.claude/skills` via `emit --root` is destructive on the live ~70-skill library, so the FIX is run by hand, not auto).*
- [ ] **Tree-ify the dev `.claude/skills`** — `emit --root-forest` now does this losslessly (dogfood-proven, round-trips). Remaining = a LAYOUT decision (the author's call): emitting at the repo root scatters node-dirs across it (`archetype-compiler/`, `skilltree/`, …); want a dedicated home (e.g. nest under one `cc-skills/` dir) before keeping the tree rather than `unemit`-ing it.
- [ ] **Organize, full** — metadata/schema enforcement (domain/subdomain, name compression) over `~/.claude/skills`, on top of coords
- [x] **Search arm** — `skilltree.search` (SQLite FTS5/BM25 + **coordinate-scoped subtree** filtering) + `si_search` MCP tool + `skilltree search` CLI
- [ ] **Search: dense/vector layer** — *later, evidence-driven*. Add embeddings (e.g. `all-MiniLM-L6-v2`, brute-force cosine) fused via **RRF (k=60)** ONLY when logged BM25 misses are semantic (synonym/paraphrase), not lexical. Overkill at small scale.
- [ ] **Search: anchor-based dynamic embedding geometry** — the author to teach the mechanism next: a dynamically-reshaped embedding space driven by *anchors* (not a static embedding). Ask the author to explain the anchor scheme before building; likely ties to the coordinate worldview. The real plan for the dense layer above.
- [ ] **Re-materialize the live tree** — `cc_tree_test` (+ its `~/.claude/skills` symlinks) predates `compose_summary`; re-`materialize(coords=True)` + re-link so the live tree carries its branch summaries.
- [x] **Search: internal-node summaries** — `compose_summary`: every branch gets a *deterministic, template-composed* subtree summary (coord + children + reachable descendants) baked into its body, so branches are retrievable by descendant terms. RAPTOR's win, no LLM. (Optional later: LLM-written abstractive summaries when the template isn't rich enough.)
- [ ] **MCTS over the tree** — for skill *composition* (SCCC choosing what to chain), NOT for lookup (LATS 2310.04406). Defer until composition needs it.

> **Research (2026-06-16, 3 scouts):** hybrid BM25+dense = standard (RRF, Cormack 2009; BEIR 2104.08663 — BM25 strong baseline). Tree-RAG helps via summaries (RAPTOR 2401.18059), coord/prefix scoping is a legit sublinear *filter* (Retreever 2502.07971; probabilistic label trees 2009.11218). Agent memory: "Hermes memory" = Nous Hermes agent (flat MEMORY.md + **SQLite FTS5** — we're a superset); category established (Voyager, H-MEM 2507.22925, MemGPT 2310.08560). **Differentiated bit = the human-meaningful coordinate as address + provenance + retrieval-scope.** Verdict: FTS5+coord-scope now ✓; vectors/MCTS later by evidence.

## P7 — Plugin  `▸`

- [x] `.claude-plugin/plugin.json` + `.claude-plugin/marketplace.json` manifests
- [x] Bundle the capability skills (`skills/`) + the SI MCP (`.mcp.json`)
- [x] Ship `report-missed-skill` (the root skill tree default)
- [ ] Include slash `commands/` + `agents/` in the plugin
- [ ] One-command install / distribute — **commit `.claude-plugin/`, `.mcp.json`, `skills/`** then `/plugin marketplace add github:sancovp/chaincompiler` and install-verify
- [x] `skills/report-missed-skill` is a real file again (v0.1.57) — both entries had dangled since SkillTree left `packages/`; the dev surface links to it inside the folder

## P8 — GlyphSteer (research)  `▸`

- [ ] Dense Q4 on a real corpus, and the short paper on it (aspirational — `roadmap.json` P8's last item)

## P4 — Marketplace  `▸`  (aspirational tails)

- [ ] Hosted marketplace endpoint (needs a backend; repo-as-registry covers the rest)
- [ ] Cross-user discovery

## P5 — Federation  `✓`  (aspirational tail)

- [ ] Reputation / staking trust tier (needs a community, not just code)

## Cross-cutting / loose ends

- [ ] **Tree-ify the real library** — the ~70 FLAT skills in `~/.claude/skills` all auto-load every session; turn them into one tree so a session loads one root and `cat`s to the exact skill (the real payoff of SkillTree). *The author's call — it reorganizes the live library.*
- [ ] Bump GitHub Actions to Node 24 (deprecation warning; deadline Sept 2026)
- [x] LICENSE (MIT)
- [x] **Two style ACs minted through the accc door** (2026-08-12) — `adam-curtis-narration-style` + `explain-something-fractally` (`skills/`), forged from example corpora in `packages/accc/examples/*.ac`, exemplars gated clean. Found + fixed en route: `install.sh` omitted `glyphsteer` from its editable-package list (and `numpy`, its dep) — `roll_up_algebra`'s persona AIOS silently fell to the no-legend fallback and `test_persona_aios_has_kb_and_glyphsteer_instructions` failed on a fresh install.
- [x] **The two styles re-forged as FULL rolled-up chain systems** (2026-08-12, superseding the thin single-chain ACs above in place — the author's correction: topic-label foci do not reproduce a cognition; the foci must be the OPERATIONS the style performs). Each is now `roll_up_algebra` output, `closed=True`: 2 operation-grade ACs + a bespoke `PersonaSpec` CoR (the melt-gauge with the style's cue phrases) + the SC rollup at `skills/<domain>/` + a persona AIOS under `personas/` (new top-level dir, `persona_root=`). Suites 36/36 across accc/corcc/sccc/chainaios.
- [x] **The `*CC` default descriptions emitted unparseable frontmatter** (2026-08-12) — APE's `write_skill` does not YAML-escape descriptions, and all three defaults (`accc.package` "…(how to think): attend…", `corcc.package` "…(ends in a decision): …", `sccc.package` "Skillchain: …") contained `": "` → `mapping values are not allowed here`. Fixed repo-side (colon → em-dash in the three defaults) + regression test `test_default_description_yields_parseable_frontmatter`.
- [ ] **`write_skill` frontmatter is not YAML-escaped** (upstream, `agent-prompt-engineering`/skillpack) — a description containing `": "` produces an unparseable SKILL.md frontmatter. The repo-side default-description fix above removes the known emitters, but the real fix = quote/escape the scalar in APE's `skill_markdown` (any caller-supplied description with `": "` still breaks).
- [x] **Two already-shipped skills carried the `": "` frontmatter break** (found by the 2026-08-12 GAN review's 20-file sweep, fixed same day) — `skills/forge-skillchain/SKILL.md` + `.claude/skills/skilltree/SKILL.md` both failed `yaml.safe_load`; colon → em-dash. (Claude Code's loader tolerated them — strict YAML consumers would not.)
- [ ] **AC vocabulary gating has no measured teeth on real corpora** (2026-08-12) — `strict=True` did NOT reject off-style same-shape probes forged from the v0.1.48 style corpora (single-atom: 6 rules, probe CLEAN; mixed 3-chain: 30 rules, probe CLEAN). Whether `next_token` pins ever adopt on small/varied corpora needs a rulecatcher/APE `learn` semantics read (min-support/confidence thresholds) before any AC gate is claimed to enforce style. Related: `roll_up_algebra` cannot even pass `strict=` down to `accc.forge` (bandit.py:190 hardcodes the default) — API gap.
- [x] **The Adam-Curtis narrator maximized as a GBA AIOS** (2026-08-12, after the author's ChatGPT-comparison challenge) — `personas/systemic-archive-narrator/`: the `Systemic-Archive-Narrator` persona (7-move melt-gauge — FragmentIntake → ActorIncentiveMap → CausalGraph → FeedbackDetect → EpistemicAudit → NarrateInRegister → |RevisableModel|) seated over a live coordinate-addressed tree of SIX chain systems — the top style system (investigation + arc + register ACs) plus five `construct_into` sidechains EACH with its own persona seat (Source-Critic · Incentive-Mapper · Causal-Cartographer · Loop-Finder · Anti-Magic-Auditor). All six `closed=True`; 17 skills indexed; scoped search routes correctly. This is the SDNA-profile depth done through the doors instead of as a blob.
- [x] **CHAINFORGE — the diagram-construction cognition as a GBA AIOS** (2026-08-12, second of the SDNA-depth builds) — `personas/chainforge/`: the `Chainforge` persona (8-move melt-gauge — RequirementParse → EntityExtraction → RelationTyping → BoundaryLayering → FlowTopology → GraphValidation → Render → |LegibilityAudit|, cues carrying the axioms — never begin by drawing, an arrow is not generic association, topology before styling, feedback as a visible loop) over SEVEN closed systems: the top (master `diagram-compilation` AC + the `never-begin-by-drawing` prime-heuristic AC) plus six `construct_into` sidechains each with its own seat (Node-Typer · Edge-Typer · Boundary-Keeper · Topology-Selector · Graph-Auditor · Legibility-Auditor). 18 skills indexed; seat-routing proven on four probes.
- [x] **⭐ THE FOREST-OF-LORDS DEBT IS CLOSED — rule 01's named upstream change, built + gated** (2026-08-12). Rule `01-everything-is-a-tree.md` carried it: *"`roll_up_algebra` emits a single-lord tree… the construct must be able to emit **lordable sub-domains** (each a branch with its own `CLAUDE.md` + subtree). This is the upstream change that makes the recursion structural, not cosmetic."* Built in `gba.py`: `_node_dict` persists a `_lord` (name · blurb · moves) in the manifest for any sub-domain a caller SEATED a bespoke persona on; `_write_lords` re-emits that branch's own `CLAUDE.md` after every materialize (which rmtree's the root, so a hand-written one could never survive). **The warrant is respected** — a sub-domain that took the default bandit gets NO lord (rule 01: grow lords on warrant, never one-per-leaf); the gate caught the over-eager first version. **PROVEN by live descent, not asserted:** reading into `personas/chainforge/graph-validation-cor/` seats the agent AS the Graph-Auditor (its `CLAUDE.md` + its scoped `0.7` skill inject). 13 lords now stand across the two GBAs. Test: `test_a_constructed_seat_is_a_LORD_you_can_descend_into` (37/37).
- [x] **Rule 01's debt list is current** (v0.1.57) — the closed single-lord debt is gone from it; its one open debt (this repo's flat `.claude/skills/`) stands.
- [ ] **SkillTree writes frontmatter descriptions unquoted** (upstream) — a description containing `": "` makes unparseable frontmatter. Since v0.1.57 every description ChainCompiler generates is colon-free (the capability generator, the roll-up's tree descriptions, bigdog) and all 113 `SKILL.md` in this repo parse; the quoting itself belongs in SkillTree and APE.
- [x] **The version line is one again** (ruled 2026-10-23): one source home, published to `sancovp/chaincompiler` with a version and a changelog entry per release; the first publish from the source home waits only on the folder's universal scan (no person's name, no machine path).
- [x] **`DESIGN.md` written** (v0.1.57) — the one design, a section per part; every known defect in it is marked ⚠ OWED and listed below. The code's `DESIGN.md §…` and `META-APE spec §…` citations now point at its sections.
- [x] **The examples run again** (v0.1.57) — `examples/_all` (16/16), `bandit_self` (7/7) and `examples/nutrition` (2/2) had broken when the agent tier moved to `chainaios` and `gba.json` went portable; `si` walks a portable tree to its leaves (new depth-two test).
- [ ] **The plugin install brings the Python packages** — today it copies the skills and registers the MCP but installs nothing; then prove the plugin install in a clean Claude Code (DESIGN §16).
- [ ] **One version line** — stamp the release version into `plugin.json`, `marketplace.json` and every package's `pyproject.toml` (DESIGN §18).
- [ ] **CI runs the checks** — the public repo's workflows run no tests; run `pytest packages`, the examples and `lint-imports` on every push (DESIGN §19).
- [ ] **The GBA ships `bandit-chain-system` as package data** — it copies the skill from the source checkout, which a non-editable install lacks (DESIGN §8).
- [ ] **personapack's evidence is checkable from a release** — the forge script and the receipts behind `proven-in-forge` and `tested-with-receipt` live in the author's private repositories (DESIGN §6).
- [ ] **Lift the archetype spec into the repo** — `ARCHETYPE-COMPILER.md` and its correspondence map are cited throughout `packages/archetype` and live outside it (DESIGN §12).
- [ ] **Widen the import contract** to the packages beside the tiers (DESIGN §2).
- [ ] **Break the lazy import cycle** between `chaincompiler.persona` and `glyphsteer.grammar` (DESIGN §2).
- [x] **Generated agents agree with the design** (v0.1.57) — every GBA and HBA rule now files a goldenization request instead of promoting its own chains, and every generated instruction descends by Read, not `cat`; the two committed personas regenerated from the fixed generator.
- [x] **A GBA never rebuilds over a missing body** (v0.1.57) — `construct_into` and `_apply_tree` refuse instead of writing stubs; the two personas' root sources are tracked (they had been ignored as `dist/`), and both rebuild byte for byte from a clean checkout.
- [x] **The plugin version moves with its payload** (v0.1.57 → plugin 0.2.2), and its description lists what it ships.
- [x] **The GBA's default rule blocks are public** (v0.1.62) — `chainaios.default_rule_blocks(domain)`, so an agent
  that adds a rule block of its own (CompiloApe's user binding) extends the four instead of losing them; the HBA and
  the nutrition example use it (DESIGN §8).
- [x] **`chaincompiler gba check`** (v0.1.62) — `check_gba` reads `closed` again on disk after the fact: bodies
  present, the materialized tree the manifest's and valid, no `SKILL.md` outside the tree, every frontmatter parsing;
  non-zero exit on any failure (DESIGN §7 · §8).
- [ ] **`gba check` compares each materialized body with its source** — it lists a skill outside the tree, but a body
  edited by hand inside the tree still passes (DESIGN §8).
- [x] **A compiled skillchain no longer carries its compile date** (v0.1.62) — two compiles of one sequence on two days
  gave two files; now the same sequence gives the same bytes, and the five committed rollups are compiled again
  without it.
- [ ] **Keep a GBA's root folder in place across a rebuild** — `_apply_tree` lets `materialize` delete the root and
  write a new one, so a shell standing in the folder loses its working directory (found by a live model running
  `gba construct .` then `gba search .` in one command line) (DESIGN §8).
- [x] **Port the public repository's two bug sweeps** (v0.1.64) — the fourteen defects its branches `fix/bug-sweep`
  (pull request #1) and `fix/confirmed-bug-sweep` (#2) found in honeyc, dietc, glyphsteer and corcc are fixed here at
  every door the same input reaches — `honeyc norm` for the `mediates` crash, and `si_search` and
  `chaincompiler gba search` for a query with no word — each with a regression test that fails without its fix; where
  the two sweeps fixed one defect two ways, the fix the design states is kept (DESIGN §3 · §11 · §18). Every committed
  CoR the chain compilers wrote is compiled again through its generator — ChainCompiler's own, CompiloApe's tower and
  agent-rts's WoomEngineer system.
- [ ] **bigdog's build writes its build time into the rule scope it exports** — `skills/bigdog/build.py` exports
  rulecatcher's scope with each decision's `created_at`, so two builds of the same inputs differ in those stamps alone;
  the export should carry none, as the compiled skillchain carries no compile date since v0.1.62 (DESIGN §16).
- [x] **No distribution takes another project's PyPI name** (v0.1.64, the author's ruling) — `accc`, `archetype` and
  `si` publish as `chaincompiler-accc`, `chaincompiler-archetype` and `chaincompiler-si`, `skillchain` as
  `skillchain-compiler`, and every build file names them so; import names unchanged (DESIGN §18).
- [ ] **Publish the fifteen packages to PyPI under their names, each a manifest unit** (the author's ruling) — holds
  the fourteen names still free there; needs scalable-publishing to state how a package inside a unit's folder gets its
  own PyPI release (its `DESIGN.md` §4: every package we own on PyPI is a manifest unit), `rulecatcher`, uploaded by
  hand, among them (DESIGN §18).
- [ ] **SCCC resolves a step to the package, never to the organizing tree's node copy** — its index takes every
  `SKILL.md` under the skills folder, so after a re-mint into a folder holding the roll-up's tree a step can resolve to
  `<domain>-tree/…/<step>/SKILL.md` and the rollup describes it by that node's placeholder ("attend (woom)" for
  agent-rts's WoomEngineer steps 4 and 5); pin it with a test that mints twice into one folder (DESIGN §5).
- [ ] **A merged snapshot import makes a rule's status and history agree** — `import_scope_snapshot` without
  `replace_scope_state` upserts each rule through `upsert_candidate_rule`, which keeps the stored status on a conflict
  (right for a rule learned again), and then imports the snapshot's decisions; so a rule adopted in the snapshot and
  pending in the target stays pending under a history that says it was adopted. State which status a merge keeps for a
  rule both scopes hold, apply it, and pin it with a test that merges a snapshot whose rule was decided (DESIGN §3).
- [ ] **SkillTree's search raises on a query with no word in it, or an operator word** (upstream) — `skilltree.search`
  hands a query's words to FTS5 unquoted (`'"'` → `unterminated string`, `NOT` → `syntax error near "NOT"`).
  ChainCompiler's doors to it, `si_search` and `chaincompiler gba search`, send it the query's words alone, lowercased;
  SkillTree's own `skilltree search` still raises — quote each word there (DESIGN §10).
- [x] **One reading of the notation's markers** (v0.1.64) — honeyc's README table gives every marker the grammar
  defines its reading, an example and the triples it gives, `-rel->` and `<rel-` as two spellings of `rel(A, B)`;
  `tests/test_readme_notation.py` checks each row against the code and each grammar marker against the table, and the
  README's core example against what it prints; the readable lens writes back the spelling it read; `check`'s rewrite
  keeps the chain's connectors; dietc's rune writes its cap watch as a relation the grammar reads (DESIGN §3).
- [x] **Glyph matching takes the longest glyph first** (v0.1.64) — glyphsteer's one matcher, `Vocabulary._matches`,
  reads left to right and takes at each place the longest glyph that starts there, never two that overlap; parsing,
  stripping, the hide check, `to_honeyc` and the grammar's order check all read through it, so a vocabulary holding
  `⚠` and `⚠️` parses, strips and hide-checks each whole; glyphsteer's README, `implementation_plan.md` and rules
  state it (DESIGN §11).
- [x] **Fold what the author keeps out of the public repository** (v0.1.64) — the steward package is its own project
  (`not-unified/steward`), and the internal design, the public repository's history from before its rewrite (a
  verified bundle) and the two files of that history held in no other form are in `not-unified/chaincompiler-internal`;
  the standalone folder that held the design and the package is deleted, every file confirmed folded byte for byte
  (DESIGN §18).
- [ ] **Close the public repository's branches once their work is in the source home** — the two bug sweeps and the
  backup of the history from before the rewrite (DESIGN §18).

## Gate — set-valued / closed-class vocabulary check  `✓` (found by a metaformal self-test, fixed 2026-06-17)

- [x] **Found:** the gate couldn't reject foreign tokens at *branch points*. rulecatcher learns
  single-expected continuation rules thresholded at `min_confidence`; a position with two legitimate
  continuations (after `⇒` comes `[` *or* `|`) never reaches confidence → ungoverned → a foreign token
  there (`[ac:x] ⇒ ❌NOPE❌ ⇒ |Z|`) passed. (conf-lowering caught it but false-positived valid chains.)
- [x] **Fixed (opt-in):** `chaincompiler.bridge.gate(..., strict=True)` + `foreign_tokens(...)` — derive
  the allowed closed-class vocab (SYMBOL/OPERATOR/DELIM/SEPARATOR/KEYWORD) from the learned artifacts;
  any closed-class token outside it → `syntax_break` (open-class IDENTIFIER/NUMBER always allowed).
  Default behavior + the 43 rulecatcher tests untouched. **Observed GREEN:** strict gate REJECTS
  `❌NOPE❌` (2), ADMITS the valid chain (0). Frozen: `test_strict_gate.py` (3) + the `metaformal-self-test`
  gate anecdote.
- [ ] **Later:** make the `*CC` constructors / GBA `construct` use `strict=True` by default (a behavior
  change — needs its own metaformal pass to confirm it doesn't reject legitimate domain chains).

## Recursion — dietc rebuilt as a chaincompiler-built AIOS  `✓` (2026-06-18)

- [x] **`examples/nutrition`** — dietc (11 hand-coded Python modules, **0 skills**) re-expressed as a
  `nutrition` GBA/AIOS *built by* chaincompiler (`build.py`): `make_gba` + 3 AC atoms (gap/cap/safety)
  + `nutrition-recommend` CoR + `compile-day` pipeline flow-skill (calls the dietc Python tools) +
  a `90-safety` rule (NOT medical advice). Split = the law (math/IO stay Python tools; how-to-think
  → AC/CoR; pipeline → walked flow). Verified by a metaformal self-test (`test_nutrition_aios.py`):
  real build (closed, 0 viol, coord-addressed) + a real day compiled through the tools (PotatoDay →
  1680 kcal gap; safety fired). Reveals the **AIOS template** chaincompiler applies to itself. Plan:
  `DIETC-AIOS-REBUILD.md`. Anecdote frozen in the `metaformal-self-test` skill.
- [ ] **Later:** thin `dietc/cli.py` to note "the AIOS is the front end now; these are its tools"
  (optional cosmetic; the Python tool layer is untouched + still tested).

## Done (shipped)

P0 Foundation · P1 Project Surface (live site) · P2 Exchange · P3 Self-Hosting & SI ·
P5 Federation · the public repo + CI + Pages · coordinate addressing · the
`report-missed-skill` keystone.

## P9 — Tome: the chapter rung (`skill2framework` + `framework`)  (2026-07-10)

- [x] **`packages/framework`** — the deterministic glue: `JourneyCore`+`render_blog1` (fill,
  never hand-write), `assemble_chapter`, `package_plugin`, `fold_into_tome` (delegates to
  `skilltree.tome.fold`, `agent-skilltree>=0.3.0`). 5 tests.
- [x] **`skills/skill2framework/*`** — the 6 stage prompt-skills (DIY port of the proven
  doc-mirror set): narrative-blog, deepdive-blog, assemble-chapter, framework-skill
  (emits the `{aios}-volume`), package-plugin, fold-into-tome.
- [x] **`chains/skill2framework.chain`** + the compiled rollup skill (skill steps + CoR bridges).
- [x] Deterministic spine E2E: blog → chapter → plugin → fold → `skilltree validate` green.
- [x] First REAL chapter through the full chain: dogfood on the **skilltree** unit,
  2026-07-10 — all 6 stages ran (agent LLM stages + the deterministic ops), scratch-only;
  blog1 grounded (authored hook, IS-only), plugin `dead_refs == []`, scratch-tome
  `skilltree validate` green. Surfaced + fixed: the chapter links block now uses
  `## Chapter links` (blog1 already carries `## Links` when the core has URLs).
- [ ] Wire the tome into the marketplace/federation render (P4/P5 reconcile — Move 3).
