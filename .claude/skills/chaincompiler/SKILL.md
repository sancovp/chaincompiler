---
name: chaincompiler
description: Orientation when working IN the chaincompiler repo — what the system is, where things live, and the discipline. Use when developing/extending ChainCompiler, ACCC/CORCC/SCCC, skilltree, the SI, the marketplace, or the Skill OS.
---

# ChainCompiler — repo orientation

A compiler-compiler for cognition: a **closed algebra over one type, the skill dir**
(`<name>/SKILL.md`). Every layer produces/consumes only that type.

## Layout

```
README · ROADMAP · FEDERATION · BACKLOG · roadmap.json   # project surface
assets/ · site/ · scripts/ · .github/                    # roadmap SVG, site, generators, deploy
packages/  chaincompiler · accc · corcc · sccc · skilltree · si · honeyc · skillchain-compiler
.claude/rules/                                           # architecture diagrams + the discipline
```
`rulecatcher` is an **external** dep (its own repo at `~/Documents/New project/rulecatcher`).

## The stack (bottom → top)

- **rulecatcher** (lint/gate) + **honeyc** (compile) = the engine.
- **chaincompiler** = substrate (`learn→gate→compile`, `construct_language()`, SKILL.md packager).
- **ACCC → CORCC → SCCC** = attention chains → chains of reasoning → skill chains (each emits a skill dir).
- **skilltree** = organize (cat-breadcrumb trees, coords, forest, exchange, federation, marketplace registry, reports).
- **si** = the self-interpreter MCP (also a skill): execute, `tree_to_mcp`, `scaffold_repo`.

See `.claude/rules/10-architecture-components.md` and `20-architecture-flows.md` for diagrams.

## Discipline (enforced)

When you finish a unit of work, in the SAME change: tick `BACKLOG.md`, update
`roadmap.json` status, add a `## Changelog` entry in `README.md`, and run
`python3 scripts/update_site.py`. The deploy gate fails the push without a new
changelog entry. See `.claude/rules/00-keeping-roadmap-and-backlog-current.md`.

## Tests

`./install.sh` (rulecatcher first, separately), then `pytest` in each `packages/*`.
