# PersonaCC — Persona Compiler-Compiler

The **persona** compiler of the cognition-chain stack: `ACCC → CORCC → PersonaCC`.

## The ratified definition

> **A persona = a specific set of DESCRIPTION BLOCKS + a set of ACs + at least one
> CoR that USES them.**

ACCC forges an **attention chain** (inner, silent — *how to think*). CORCC forges a
**chain-of-reasoning** (outer, spoken — the persona-melt gauge). PersonaCC forges
the whole **persona**: the description blocks that say who the agent is, the
attention chains it thinks along, and the one-or-more CoRs that use them. Its
source language is the 2023 SDNA-template block grammar (`[KIND] … [/KIND]`).

## The bundle (`notation.py`)

```python
Block(kind="role", body="You are …")          # kind is a FREE string — new kinds are legal
PersonaBundle(
    name="…",
    blocks=(Block(...), …),                    # description blocks (may be empty)
    acs=("[Focus] ⇒ [Focus] ⇒ |Held|", …),     # attention chains (accc notation)
    cors=(persona_spec, …),                    # ≥1 corcc.PersonaSpec (the reasoning core)
    blurb="…",
)
```

`PersonaSpec` is really the **COR SPEC** (a half-persona — the spoken move-chain);
PersonaCC builds the full persona *above* it. New block kinds are legal by design
(the template-template rule): the grammar never closes over a fixed enum.

## The *CC shape (`forge.py`)

- **`forge_bundle(bundle, db=…)`** — forge each AC via ACCC, each CoR via CORCC;
  run the notation lint + the uses-them gate. Returns a `ForgedBundle`.
- **`lint(bundle)`** — notation/structure lint: every AC is a well-formed rune
  chain, every CoR chain parses, ≥1 CoR, blocks well-formed.
- **`uses_them(bundle, strict=False)`** — the check that makes "…that USES them"
  mechanical: every CoR move name must be a focus in a bundle AC **or** the CoR's
  own derived chain. The escape hatch (a CoR's own derived chain always contains
  its own moves) means a well-formed bundle never hard-fails in the default mode —
  uncovered moves surface as **warnings** ("declared but not wired to an AC").
  `strict=True` drops the escape hatch: an uncovered move is a **violation**.
  (Weakened to a warning by default because the seed/proof bundles' real attention
  atoms legitimately don't re-list every CoR move.)
- **`package(bundle, out_dir)`** — compile to `<name>/SKILL.md` (blocks as
  sections + the AC set + each CoR's PRIME) via `chaincompiler.write_skill`.
- **`seat(bundle)`** — return exactly the kwargs
  `chainaios.make_gba(domain, root, **seat(bundle))` accepts:
  `{atoms, blurb, role_block, persona}`. Only `cors[0]` is seated today; seating
  additional CoRs is future work.

## TOTAL SYNTAXIFICATION (the doctrine)

One notation all the way down: **every persona block can be made with AC syntax, and
natural language never appears free — only as a component the specific AC syntax
licenses** (e.g. a condition gloss inside a focus). Blocks therefore carry a **grade**
(`Block.grade`): `prose` (soup — free NL, tolerated *only* for migration) → `chain`
(code — real chain syntax). Detection is honest — for the default `rune` language it
uses accc's **real parser** (`parse_ac`), not a regex; a body is a chain iff it parses.
The **melt-gauge** that CORCC runs on a CoR (forge the language, gate the text, drift =
melting) now runs on the whole persona: `forge.lint_blocks(bundle)` gates every
chain-graded block (a hard issue if it melts) and warns on every prose block
("unsyntactified block: <kind>"). A malformed chain-block fires the same gate a melting
CoR does. The endpoint: the melt-gauge covers the entire persona, not just its CoRs.

**TYPE ⊥ SYNTAX.** A block is a triple — (type-`kind`, `lang`, `body` string): the
label is orthogonal to the language is orthogonal to the string. The typed content is
canonical; **every string is a *render*** of it in some chain language, and
re-rendering one typed corpus across languages IS the de-lore/masking mechanism —
myth-lang and research-lang are two render targets of the same typed persona. A
language is lintable once its melt-gauge is registered (`register_lang_gate(name, fn)`;
`LANG_GATES` holds `rune` by default); until then its blocks grade `prose` ("no gate
registered for lang=<x>"). To emit a conformant string, the LLM needs only the type
label + which syntax.

## The library

`personapack` is the LIBRARY of pre-bound `PersonaBundle`s (Bodhisattva, Aegis,
SamayaReviewer, …), each with an honest activation grade and a receipt.
