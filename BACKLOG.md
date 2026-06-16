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
