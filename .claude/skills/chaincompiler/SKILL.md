---
name: chaincompiler
description: Orientation when working IN the chaincompiler repo — what the system is, where things live, and the discipline. Use when developing or extending ChainCompiler, ACCC/CORCC/SCCC, chainaios, the persona compilers, goldenreq, glyphsteer, the SI, the marketplace, or the Skill OS.
---

# ChainCompiler — repo orientation

A compiler-compiler for cognition: a **closed algebra over one type, the skill dir**
(`<name>/SKILL.md`). Every layer produces or consumes only that type.
**Read `DESIGN.md` first** — it is the design, one section per part; this skill is the map to it.

## Layout

```
DESIGN.md                                             # the design — read it first
README · ROADMAP · BACKLOG · roadmap.json             # public face + changelog · phases · tasks
FEDERATION · REBUILD-SPEC · DIETC-AIOS-REBUILD        # reference detail (a plan and two records)
packages/  rulecatcher · honeyc · skillchain-compiler # the engine
           chaincompiler                              # the base
           accc · corcc · sccc                        # the chain tier
           chainaios                                  # the agent tier (installs the chaincompiler CLI)
           personacc · personapack · goldenreq · glyphsteer · archetype · framework · si
skills/ · .mcp.json · .claude-plugin/                 # the plugin payload
personas/ · examples/ · chains/                       # worked agents · end-to-end examples · skillchain specs
assets/ · site/ · scripts/ · .github/                 # generated roadmap + site, generators, workflows
.claude/rules/                                        # the tree law · the autoload fact · the diagrams · the mint flow
```

SkillTree is not in this repo: it is `agent-skilltree` on PyPI (import `skilltree`). `./install.sh`
installs every package editable plus the PyPI dependencies.

## The stack, bottom → top (`DESIGN.md` §2)

- **APE** (`agent-prompt-engineering`, PyPI) under everything — the prompt engine, the grammar seam, `write_skill`.
- **rulecatcher** (the gate) + **honeyc** (the compiler) = the engine.
- **chaincompiler** = the base: forge · gate · grammar · package · prime · the glyph-persona front end.
- **ACCC → CORCC → SCCC** = attention chains → chains of reasoning → skill chains (each emits a skill dir).
- **chainaios** = the agent tier: `construct_language`, `roll_up_algebra` (closure), `hierarchicalize`,
  and the agent shapes GBA · COG · HBA (`DESIGN.md` §7–§8).
- Beside the tiers: **personacc/personapack** (personas), **goldenreq** (nothing promotes itself),
  **glyphsteer** (retrieval steering), **archetype**, **framework** (the chapter rung), **si** (the
  self-interpreter MCP).

Diagrams: `.claude/rules/21-architecture-diagrams.md` (the stack, the algebra, the package graph and every flow).

## Discipline (enforced)

When you finish a unit of work, in the SAME change: rewrite `DESIGN.md` where the design changed, tick
`BACKLOG.md`, update `roadmap.json` if a phase moved, add a `## Changelog` entry in `README.md`, and run
`python3 scripts/update_site.py`. The deploy gate fails the push without a new changelog entry. See
`.claude/rules/00-keeping-roadmap-and-backlog-current.md`; minting a chain follows
`.claude/rules/22-seq-mint-attention-chain.md`.

## Tests (`DESIGN.md` §19)

`./install.sh`, then `pytest packages`, `pytest examples/_all/test_all.py`,
`python examples/_all/bandit_self.py`, `pytest examples/nutrition`, `lint-imports`.
