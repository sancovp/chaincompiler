<div align="center">

# ChainCompiler — Roadmap

*The path from "a closed algebra over one type" to a self-hosting, self-publishing marketplace.*

<img src="assets/roadmap.svg" alt="ChainCompiler roadmap" width="980"/>

</div>

> This image and the [live site](site/) are **generated** from [`roadmap.json`](roadmap.json) +
> the README changelog by [`scripts/update_site.py`](scripts/update_site.py). Edit the data, run the
> script, everything downstream updates.

---

## P0 — Foundation &nbsp;`✓ done`

The closed algebra over one type — the **skill dir**. `rulecatcher` (lint) + `honeyc` (compile) +
`ChainCompiler` (substrate) + `ACCC`/`CORCC`/`SCCC` (the three layers) + `SkillTree` (organization).
**107 tests green**, plus the `csgn-rulecatcher` and dense-rune proofs.

## P1 — Project Surface &nbsp;`▸ in progress`

Make it visible, publishable, and self-updating: this **roadmap** (SVG regenerated from data), a
**website** that renders it dynamically, a **changelog** in the README, the **`update_site.py`**
generator, and a **deploy workflow** gated on a changelog entry.

## P2 — Exchange &nbsp;`○ planned`

A **YAML/JSON exchange format** so a repo can hold **multiple skill trees at once** under a **master
system**, with a loader + validator. The portable unit of "a whole cognition library."

## P3 — Self-Hosting & Self-Interpreter &nbsp;`○ planned`

The literal **self-interpreter** — an SI for the chain dialect (a Python dialect; it defers to native
Python ops rather than re-wrapping them). Shipped as an **SI MCP that is also a skill**, able to turn
**trees and masters into MCPs** — and ChainCompiler **compiles itself**.

## P4 — Marketplace &nbsp;`○ planned`

A **publisher marketplace** for the exchange: **programmatic publish**, **opt-in public on use**, and a
notify-and-grow loop — whenever anyone uses it (and marks it public), it publishes and the system grows.

---

*See the [changelog](README.md#changelog) for what shipped when.*
