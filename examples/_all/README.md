# `examples/_all` — the everything example

One domain — **`reviewer`** (a cognition system that reviews & grades a claim) —
flowed through **every package** in the monorepo, end to end, each stage asserting,
ending in a verifiable round-trip.

This is the **dogfood**: if `./install.sh` worked, this runs green from a clean
clone and proves the whole stack *composes on a single artifact* — not ten isolated
demos, but one thing built by all ten tools in sequence.

```bash
./install.sh                         # once
python3 examples/_all/run_all.py     # → 7 stages, 9 packages
```

## The 7 stages (each produces or consumes the ONE type: a `<name>/SKILL.md`)

| # | stage | package(s) | what it proves |
|---|-------|-----------|----------------|
| 1 | **persona → AIOS** | `chaincompiler.persona` | a glyph-persona program compiles to a legend (5 axes) + a gated chain + a `SKILL.md` |
| 2 | **honeyc** | `honeyc` | a dense-rune chain parses into normalized statements |
| 3 | **gate** | `rulecatcher` (via `chaincompiler.bridge`) | a learned grammar admits a valid chain (0 violations) and flags a malformed one (≥1) |
| 4 | **construct** | `accc` · `corcc` · `sccc` | `construct_language` mints the reviewer **AC + CoR + SC** in one call |
| 5 | **organize** | `skilltree` | the cognition becomes a `cat`-breadcrumb tree — materialized, validated, searchable |
| 6 | **steer** | `glyphsteer` | a glyph facet pins the right chunk; the marker is **stripped from the returned text** (HIDE invariant) |
| 7 | **interpret** | `si` | the self-interpreter walks the tree to its leaves and runs a chain-dialect snippet |

The only monorepo package **not** in the flow is the legacy standalone
`skillchain-compiler` (superseded by `sccc`).

## Why this is the proof that matters

Tests inside each package prove *that package* does what it says. `_all` proves the
**closed algebra**: every operation produces or consumes the same type (a skill dir),
so the output of one tool is legal input to the next — `persona → honeyc → gate →
construct → tree → steer → custody → interpret` round-trips without an adapter at any
seam. That closure is the whole thesis; this file is where you watch it hold.
