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
- [ ] **Start the live cron on `~/.claude`** — run `skilltree watch ~/.claude` as a background process so the real user-level forest is watched. *Pending: Isaac's go (writes a real always-on rule; treeifying `~/.claude/skills` via `emit --root` is destructive on the live ~70-skill library, so the FIX is run by hand, not auto).*
- [ ] **Tree-ify the dev `.claude/skills`** — `emit --root-forest` now does this losslessly (dogfood-proven, round-trips). Remaining = a LAYOUT decision (Isaac's call): emitting at the repo root scatters node-dirs across it (`archetype-compiler/`, `skilltree/`, …); want a dedicated home (e.g. nest under one `cc-skills/` dir) before keeping the tree rather than `unemit`-ing it.
- [ ] **Organize, full** — metadata/schema enforcement (domain/subdomain, name compression) over `~/.claude/skills`, on top of coords
- [x] **Search arm** — `skilltree.search` (SQLite FTS5/BM25 + **coordinate-scoped subtree** filtering) + `si_search` MCP tool + `skilltree search` CLI
- [ ] **Search: dense/vector layer** — *later, evidence-driven*. Add embeddings (e.g. `all-MiniLM-L6-v2`, brute-force cosine) fused via **RRF (k=60)** ONLY when logged BM25 misses are semantic (synonym/paraphrase), not lexical. Overkill at small scale.
- [ ] **Search: anchor-based dynamic embedding geometry** — Isaac to teach the mechanism next convo: a dynamically-reshaped embedding space driven by *anchors* (not a static embedding). Ask him to explain the anchor scheme before building; likely ties to the coordinate worldview. The real plan for the dense layer above.
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
- [ ] Optional: real-copy `skills/report-missed-skill` (drop the symlink) for Windows/`core.symlinks=false` safety

## P4 — Marketplace  `▸`  (aspirational tails)

- [ ] Hosted marketplace endpoint (needs a backend; repo-as-registry covers the rest)
- [ ] Cross-user discovery

## P5 — Federation  `✓`  (aspirational tail)

- [ ] Reputation / staking trust tier (needs a community, not just code)

## Cross-cutting / loose ends

- [ ] **Tree-ify the real library** — the ~70 FLAT skills in `~/.claude/skills` all auto-load every session; turn them into one tree so a session loads one root and `cat`s to the exact skill (the real payoff of SkillTree). *Isaac's call — it reorganizes the live library.*
- [ ] Bump GitHub Actions to Node 24 (deprecation warning; deadline Sept 2026)
- [x] LICENSE (MIT)

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
- [ ] First REAL chapter through the full chain (the LLM stages, agent-run) — the my-way
  originals are proven; this DIY port earns its own score on first use.
- [ ] Wire the tome into the marketplace/federation render (P4/P5 reconcile — Move 3).
