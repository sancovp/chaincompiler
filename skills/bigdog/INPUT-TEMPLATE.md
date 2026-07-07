# INPUT-TEMPLATE — the human steering CoR

> **The asymmetry (why this file exists):** in a human×LLM session the LLM's outputs are
> *generated* (the `bigdog` CoR templates them — see `SKILL.md`). Only the **human inputs**
> are a reusable, fixed pattern. This file is that pattern: the *steering* CoR. Drive any
> base model through it and it climbs the same idea→artifact arc this skill was mined from.
> (This is the chaincompiler/flowmine "the human IS the input" move, rendered as a CoR.)

## The steering chain

```rune
[Orient] ⇒ [Induct] ⇒ [Deepen] ⇒ [Synthesize] ⇒ [Name] ⇒ |Compile|
```

Gauge-able the same way a CoR is: if the session performs these moves **in order**, the
arc holds; skip/scramble and it melts into chat. The held convergence is `|Compile|` — the
durable artifact (a skill dir), not a nice answer.

## The moves (each = one human input; `{…}` = the slot you fill)

| # | Move | What the human input does | Template (fill the slots) |
|---|------|---------------------------|---------------------------|
| 1 | **Orient** | point the model at the context; make it load, not guess | `go get contextualized on {domain} — read {sources}, don't confuse it with {decoy}` |
| 2 | **Induct** | install the forcing-frame + a slot to fill; condition the conditional toward the valid attractor (a *benevolent* hypnotic induction = in-context priming) | `{allegory/frame that defines valid-vs-slop}. Your turn: define {slot}. Always start every turn by saying exactly: {cloze with {slots}}` |
| 3 | **Deepen** | push the frame to its structural limit (find where it *can't* work) | `now reflect on how, no matter how it looks, {the frame} cannot actually {goal} without {the missing primitive}` |
| 4 | **Synthesize** | turn the limit into a construction (close the loop) | `now reflect on how recognizing all that actually produces {a constructive mechanism}, and how it *does* cause {the goal} to emerge when connected to {the missing primitive}` |
| 5 | **Name** | ground the construction in the field's current vocabulary; fill the discipline-slot; (optionally) reveal the mechanism being used | `explain how {that} is more or less '{field} {slot}'` · then: `{the technique you just used}, ok?` |
| 6 | **Compile** `\|held\|` | crystallize the whole arc into a durable, gated artifact (the convergence) | `go read {engine}, write this down in a syntax {target} understands, transform our conversation into a template (of MY inputs — yours get generated), encode it in {engine} using {its rule system}, and maybe {an adjacent tool}` |

## Cross-cutting human moves (fire any turn, not positional)

- **Correct-misread** — "no, {X} means {Y}" (re-aim; the most load-bearing move per flowmine).
- **Demote-contestable** — "don't say it IS that — grade it" (forces G0–G9, never round up).
- **Stop-tangent** — "drop {X}, stay on {Y}".
- **Point-at-comparable** — "this is more or less {known thing}" (the Name move, inline).

## How to run it

1. Paste move 1. Let the model generate (it will, in the `bigdog` CoR if primed).
2. Paste moves 2→6 in order, filling slots for *your* domain.
3. At `|Compile|` you get a skill dir — gated, runnable. That artifact IS the session,
   made durable: the next run starts from the compiled skill, not from scratch.

> Provenance: extracted verbatim-in-shape from the conversation that built this skill
> (Orient = "go get contextualized on SSRI"; Induct = the Dogworld cloze; Deepen = "can't
> prevent slop without logic engines"; Synthesize = "reflection crystallizes a compiler →
> P-ness emerges"; Name = "more or less 'LLM in-context conditioning' / Hypnotic Induction
> ok?"; Compile = "go read chaincompiler and write it down"). The arc you're reading is the
> arc that wrote it.
