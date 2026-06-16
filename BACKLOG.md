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
- [ ] **Organize, full** — metadata/schema enforcement (domain/subdomain, name compression) over `~/.claude/skills`, on top of coords
- [x] **Search arm** — `skilltree.search` (SQLite FTS5/BM25 + **coordinate-scoped subtree** filtering) + `si_search` MCP tool + `skilltree search` CLI
- [ ] **Search: dense/vector layer** — *later, evidence-driven*. Add embeddings (e.g. `all-MiniLM-L6-v2`, brute-force cosine) fused via **RRF (k=60)** ONLY when logged BM25 misses are semantic (synonym/paraphrase), not lexical. Overkill at small scale.
- [ ] **Search: anchor-based dynamic embedding geometry** — Isaac to teach the mechanism next convo: a dynamically-reshaped embedding space driven by *anchors* (not a static embedding). Ask him to explain the anchor scheme before building; likely ties to the coordinate/CB worldview. The real plan for the dense layer above.
- [ ] **Re-materialize the live tree** — `cc_tree_test` (+ its `~/.claude/skills` symlinks) predates `compose_summary`; re-`materialize(coords=True)` + re-link so the live tree carries its branch summaries.
- [x] **Search: internal-node summaries** — `compose_summary`: every branch gets a *deterministic, template-composed* subtree summary (coord + children + reachable descendants) baked into its body, so branches are retrievable by descendant terms. RAPTOR's win, no LLM. (Optional later: LLM-written abstractive summaries when the template isn't rich enough.)
- [ ] **MCTS over the tree** — for skill *composition* (SCCC choosing what to chain), NOT for lookup (LATS 2310.04406). Defer until composition needs it.

> **Research (2026-06-16, 3 scouts):** hybrid BM25+dense = standard (RRF, Cormack 2009; BEIR 2104.08663 — BM25 strong baseline). Tree-RAG helps via summaries (RAPTOR 2401.18059), coord/prefix scoping is a legit sublinear *filter* (Retreever 2502.07971; probabilistic label trees 2009.11218). Agent memory: "Hermes memory" = Nous Hermes agent (flat MEMORY.md + **SQLite FTS5** — we're a superset); category established (Voyager, H-MEM 2507.22925, MemGPT 2310.08560). **Differentiated bit = the human-meaningful coordinate as address + provenance + retrieval-scope.** Verdict: FTS5+coord-scope now ✓; vectors/MCTS later by evidence.

## P7 — Plugin  `○`

- [ ] `plugin.json` bundling the skills + commands + hooks
- [ ] Include the SI MCP + agents in the plugin
- [ ] One-command install / distribute
- [ ] Ship `report-missed-skill` + the root skill tree by default

## P4 — Marketplace  `▸`  (aspirational tails)

- [ ] Hosted marketplace endpoint (needs a backend; repo-as-registry covers the rest)
- [ ] Cross-user discovery

## P5 — Federation  `✓`  (aspirational tail)

- [ ] Reputation / staking trust tier (needs a community, not just code)

## Cross-cutting / loose ends

- [ ] **Tree-ify the real library** — the ~70 FLAT skills in `~/.claude/skills` all auto-load every session; turn them into one tree so a session loads one root and `cat`s to the exact skill (the real payoff of SkillTree). *Isaac's call — it reorganizes the live library.*
- [ ] Bump GitHub Actions to Node 24 (deprecation warning; deadline Sept 2026)
- [x] LICENSE (MIT)

## Done (shipped)

P0 Foundation · P1 Project Surface (live site) · P2 Exchange · P3 Self-Hosting & SI ·
P5 Federation · the public repo + CI + Pages · coordinate addressing · the
`report-missed-skill` keystone.
