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
packages/  rulecatcher · chaincompiler · accc · corcc · sccc · skilltree · si · honeyc · skillchain-compiler · glyphsteer · steward
.claude/rules/                                           # architecture diagrams + the discipline
```
`rulecatcher` (the gate) is vendored at `packages/rulecatcher` — zero deps; `./install.sh` wires everything.

## The stack (bottom → top)

- **rulecatcher** (lint/gate) + **honeyc** (compile) = the engine.
- **chaincompiler** = substrate (`learn→gate→compile`, `construct_language()`, SKILL.md packager).
- **ACCC → CORCC → SCCC** = attention chains → chains of reasoning → skill chains (each emits a skill dir).
- **skilltree** = organize (cat-breadcrumb trees, coords, forest, exchange, federation, marketplace registry, reports).
- **si** = the self-interpreter MCP (also a skill): execute, `tree_to_mcp`, `scaffold_repo`.
- **persona** (`chaincompiler.persona`, CLI `cc persona FILE`) = the front-end that compiles a
  glyph-persona-program (BizziBee-style: `[VarDefs]` legend + `⚙️` workflow + `[ROLE]` wrapper)
  into `<cogid>/SKILL.md` + `legend.json` + a rulecatcher-gated chain. Example:
  `packages/chaincompiler/examples/bizzibee.txt`. (Executing the ⚙️ workflow via the SI = aspirational.)
- **glyphsteer** (`packages/glyphsteer`) = dual-regime retrieval steering (lexical tag facet +
  dense emoji direction), legend authoring, grading; `grammar.py` gates codes via rulecatcher.
  See the `glyphsteer` / `glyphsteer-dense` skills.

See `.claude/rules/10-architecture-components.md` and `20-architecture-flows.md` for diagrams.

## Discipline (enforced)

When you finish a unit of work, in the SAME change: tick `BACKLOG.md`, update
`roadmap.json` status, add a `## Changelog` entry in `README.md`, and run
`python3 scripts/update_site.py`. The deploy gate fails the push without a new
changelog entry. See `.claude/rules/00-keeping-roadmap-and-backlog-current.md`.

## Tests

`./install.sh` (rulecatcher first, separately), then `pytest` in each `packages/*`.
