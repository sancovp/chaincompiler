<div align="center">

# ChainCompiler — Roadmap

*The path from "a closed algebra over one type" to a self-hosting, self-publishing, federated skill OS.*

<img src="assets/roadmap.svg" alt="ChainCompiler roadmap" width="980"/>

</div>

> This image and the [live site](site/) are **generated** from [`roadmap.json`](roadmap.json) +
> the README changelog by [`scripts/update_site.py`](scripts/update_site.py). Edit the data, run the
> script, everything downstream updates. **This prose mirrors `roadmap.json` — keep them in sync**
> (see [`.claude/rules/00-keeping-roadmap-and-backlog-current.md`](.claude/rules/00-keeping-roadmap-and-backlog-current.md)).

---

## P0 — Foundation &nbsp;`✓ done`

The closed algebra over one type — the **skill dir**. `rulecatcher` (lint) + `honeyc` (compile, +
`dietc` domain proof) + `ChainCompiler` (substrate + `construct_language()`) + `ACCC`/`CORCC`/`SCCC`
(the three layers) + `SkillTree` (cat-breadcrumb organization). **107 tests green.**

## P1 — Project Surface &nbsp;`✓ done`

Visible, publishable, and self-updating: this **roadmap** (SVG regenerated from data), a **website**
that renders it dynamically, a **changelog** in the README, the **`update_site.py`** generator, and a
**deploy workflow** gated on a new changelog entry (`scripts/check_changelog.py`).

## P2 — Exchange &nbsp;`✓ done`

A **YAML/JSON exchange format** so a repo can hold **multiple skill trees at once** under a **master
system**, with a loader + validator. The portable unit of "a whole cognition library."

## P3 — Self-Hosting & Self-Interpreter &nbsp;`✓ done`

The literal **self-interpreter** (`packages/si`) — an SI for the chain dialect (a Python dialect; it
defers to native Python ops rather than re-wrapping them). Shipped as an **SI MCP that is also a
skill**, able to turn **trees and masters into MCPs** — and ChainCompiler **compiles itself**.

## P4 — Marketplace &nbsp;`▸ in progress`

A **publisher marketplace** for the exchange. **Local registry + publish/search ✓** and **opt-in
public + notify hook ✓**. *Aspirational:* a hosted endpoint and cross-user discovery (need a backend).

## P5 — Federation &nbsp;`✓ done`

Each emitted MCP becomes a repo; marketplaces federate. **Repo scaffolder (MCP → node repo) ✓**, the
**marketplace IS a git repo** (`registry.json`) ✓, a **contribution gate** (validate + queue + gated,
maintainer-only promote; untrusted-by-default, fork-safe CI, provenance) ✓, and **child marketplaces
federate under a parent** ✓. *Aspirational tail:* reputation / hosted discovery.

## P6 — Skill OS &nbsp;`▸ in progress`

Organize → observe → improve the global skill namespace; one shared human/agent interface.
**Coordinate addressing over `~/.claude/skills` ✓**, **`report-missed-skill` + the reports store ✓**,
and the **FTS5/BM25 + coord-scoped search arm ✓**. *Next:* usage-tracking analytics (a hook), a
frontend (tree + analytics + problem-marking, launched from the root skill), and the improve loop
(reports → agent → skill-improver / create).

## P7 — Plugin &nbsp;`○ planned`

Bundle the whole thing as **ONE installable Claude Code plugin**: a `plugin.json` bundling the skills +
commands + hooks, the SI MCP + agents, one-command install/distribute, shipping `report-missed-skill`
and the root skill tree by default.

## P8 — GlyphSteer (research) &nbsp;`▸ in progress`

Dual-regime retrieval steering (`packages/glyphsteer`): an LLM annotates a corpus with a **compiled
glyph vocabulary** that steers search **lexically** (rare ASCII tag = maximal-IDF facet) and **densely**
(an emoji's learned direction) and is **hidden at return time** (the sidecar split: indexed-form ≠
returned-form, hard HIDE invariant). Shipped: the **sidecar split ✓**, **one axis / two renderings**
(emoji=dense, ASCII=lexical; FTS5 drops emoji) ✓, the **lexical regime** (MRR 0.417 → 1.000 on the toy
corpus) ✓, the **bilinear anchor reshape** (pure numpy) ✓, the **ONNX/fastembed dense sidecar** (no
torch, `/embed` over HTTP) ✓, and **dense Q1–Q3 measured** (emoji-direction real but model-dependent —
`bge-en` collapses, XLM-R doesn't) ✓. *Aspirational:* dense Q4 on a real corpus + an arXiv short paper.

---

*See the [changelog](README.md#changelog) for what shipped when.*
