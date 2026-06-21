---
name: archetype-compiler
description: Compile an archetype as a STATE MACHINE (not a noun) — Persona/Shadow/Self/Odyssey/Becoming — generating the missing aspects from one seed, building the multi-journey Odyssey, validating C1–C6, and emitting Cypher/Prolog/JSON or a loadable SKILL.md. Use when asked to model archetypes, individuation, Jungian stacks, a pantheon, the hero's journey/odyssey, Becoming/type-lift, or "compile the transformation law not the list" for characters/roles/myth.
---

# Archetype Compiler — archetype as state machine

An archetype is **not a noun** (a role label) but a **recursive individuation circuit**:

```
MetaArchetype(A) := ⟨ Persona(A), Shadow(A), Self(A), Odyssey(A), Becoming(A) ⟩
```

- **Persona** — the legible/claimed face (the mask).
- **Shadow** = `DeniedInverse(Persona)` — the virtue turned failure-mode / the projection.
- **Self** = `Integrate(Persona, Shadow)` — holds BOTH, ruled by neither. *A purified
  Persona that bypasses the Shadow is the cardinal error (C2).*
- **Odyssey** — a **succession** of hero's journeys (NOT one): a call-out HJ, one
  automorphism-encounter per pantheon member (A meets B as an image of itself), and a
  **post-return** HJ (arrival ≠ completion). Accrues the Aut-web → quines the pantheon.
- **Becoming** = `TypeLift(Self)` — the integrated Self becomes the next archetype's
  Persona. One Becoming = one hero's journey = one modulation.

This is the ChainCompiler thesis on the psyche: **you don't list archetypes, you
compile the transformation law.**

## The move (do this)

```python
import archetype as arc

a = arc.compile_archetype("Hero", knobs={"substrate": "founder building AI"})
# a.persona / a.shadow / a.self_ / a.becoming   — the four aspects (inferred if unknown)
# a.odyssey                                       — the multi-HJ succession
assert arc.is_valid(a)                            # C1–C6 hold
arc.quines(a.odyssey, arc.CYCLE, "Hero")          # True ⇒ met every member (orbit-closure, discrete)

print(arc.cypher(a))      # graph; also: prolog(a), to_json(a), readable(a), triples(a)
arc.emit_skill(a, out_dir="skills")               # compile to the ONE type: <name>/SKILL.md
```

Other entry points: `arc.compile_chain(["Hero","Guardian","King"])` (an individuation
chain — each Becoming points at the next), `arc.compile_world(arc.CYBERNETIC_CITY)`
(a whole substrate world, §6), and the DSL via `arc.parse(src)`:

```
archetype Hero { substrate:"AI" domain:"startup myth" conflict:"inflation" }
chain IndividuationPath { Hero => Guardian => King => Steward => Sage }
```

CLI: `archetype compile Hero --substrate "example world" --depth 4 --emit all` · `archetype demo`.

## Knobs (= modes)

`domain · substrate · conflict · boundary · integration_mode · scale · tone` — each
colors one archetype differently (a "mode" of the same archetype).

## Discipline & grade honesty

- **Validation is the gate.** `arc.validate(a)` returns C1–C6 violations; empty = well-formed.
  C2 (Self integrates the Shadow) and C6 (Odyssey is plural + accrues edges + post-return)
  are the ones that catch a shallow model.
- **The mechanics are G0-by-definition** (inside the calculus). The **music-theory frame**
  (circle of fifths ↔ Becoming-cycle, modulation ↔ Becoming) is a **G8 organizing
  resonance** — use it to *organize/inspire*, never assert it as structure (ARCHETYPE-COMPILER.md §0).
- **The one open seam:** `quines()` is the *discrete* closure (met all members). Whether
  the Becoming-cycle **closes exactly or only tempers** (the circle-of-fifths comma:
  3¹²≠2¹⁹) is unsettled — that's the music-side question (`fractran-music`), connected at
  G7/G8, NOT proven by `quines()`. Don't claim the cycle closes; say "tempers / open".
