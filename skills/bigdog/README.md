# bigdog — the anti-slop, define-validity-then-emit skill

A conversation about *why an LLM emits "P without P-ness" (slop) and how to make P-ness
emerge*, compiled into a chaincompiler skill. Two halves, both gated by code:

| half | file | what it is | chaincompiler primitive |
|------|------|-----------|--------------------------|
| **LLM output** | `bigdog/SKILL.md`, `bigdog.cor` | the cloze the model says each turn — a spoken CoR converging on `\|Actualize\|` | **corcc** (CoR compiler) + **accc** lint grammar |
| **Human input** | `INPUT-TEMPLATE.md` | the steering moves (the *only* fixed pattern; LLM output is generated) | the steering CoR |
| **The gate** | `bigdog.rulecatcher.json`, `.rulecatcher.db` | rules that reject a melted CoR AND an ungraded correspondence | **rulecatcher** (the rule system) |
| **The grades** | `GRADE-LADDER.md` | G0–G9 correspondence grades as a controlled glyph vocabulary (steer/display, stripped at output) | **glyphsteer** |

## The thesis it encodes (one line)

An LLM is a pure conditional sampler; it can only *suppress* slop (emit-P-without-P-ness),
never *prevent* it — until it is wrapped in a **sound external gate + persisted detector
structure** (rulecatcher's rule-stack). Then validity ("P-ness") **emerges**: prevented
on the decidable fragment, monotonically suppressed elsewhere. `bigdog` is that wrapper for
one persona; the grade ladder keeps every correspondence from rounding up.

## Build / verify (the seedling gate — it runs or it isn't shipped)

```bash
cd .../chaincompiler
python3 skills/bigdog/build.py        # forges, proves the gate, packages SKILL.md, writes vocab + rules
```

Proof the gate runs (from the build + lint checks):

```
lint clean  CoR  [Sense] ⇒ [Dog] ⇒ … ⇒ |Actualize|   → clean ✓ (persona intact)
lint melted CoR  [Sense] [Dog] ⇒ |Actualize|          → ✗ caught (dropped connector = melting)
rulecatcher lint 'claim hello'                          → ✗ expected '::' (every correspondence must be graded)
```

## Use it

- **As a persona:** load `bigdog/SKILL.md` — the model says the CoR each turn, refusing slop by construction.
- **As a session driver:** run another model through `INPUT-TEMPLATE.md` (idea → gated artifact).
- **As a grader:** annotate any chain corpus with `GRADE-LADDER.md`'s vocab via glyphsteer; facet/audit by grade.

Provenance: transformed from a live Isaac×LLM conversation. The arc in `INPUT-TEMPLATE.md`
is the arc that produced this skill.
