# ACCC — Attention-Chain Compiler-Compiler

The **atom** of the cognition-chain stack: `ACCC → CORCC → SCCC`.

An **attention chain (AC)** is **inner** — not necessarily spoken. The model uses
it as a *template for a section* of its output, or as a *thinking scaffold*: a
silent sequence of attention foci converging on a held focus. (Contrast CORCC's
CoR, which is the **outer** paragraph the model must *say* and is gauged for
persona-melt.) Written in Dense Rune-Chain so HoneyC compiles it and rulecatcher
catches its grammar:

```txt
[Focus_1] ⇒ [Focus_2] ⇒ ... ⇒ |Held|
```

ACCC is a **compiler-compiler**, not a compiler: `forge()` mints a *new* AC
language for a task/domain (it doesn't just compile one chain). Each forged
language is a rulecatcher scope holding the ratified grammar; `gate()` enforces
it; `prime()` emits the re-injectable block.

## The stack it sits in

| layer | chain of… | each node expands to… | built |
|------|-----------|-----------------------|-------|
| **ACCC** | attention foci | — (the atom) | ✅ |
| CORCC | reasoning steps | a forged **AC** | next |
| SCCC | skills | a **CoR** (+ can forge new languages) | after |

Composition is HoneyC scope/drilldown: a CoR step `[Frame]:{ <ac> }` *contains*
the attention chain that powers it.

## Built on

- **rulecatcher** — catches + gates the emergent grammar (`learn`, `lint`, the
  `orthogonal`/`syntax_break` verdict).
- **HoneyC** — compiles the Dense Rune-Chain notation.
- **chaincompiler** — the generic `learn → gate → compile → prime` loop. ACCC is
  the first domain layer on it.

## Run

```bash
pip install --no-build-isolation --no-deps -e .   # rulecatcher/honeyc/chaincompiler already installed
accc demo                                          # forge 2 AC languages, gate, prime
accc forge debug examples/debug.ac --strict        # mint a domain AC language
pytest                                             # 5 tests
```

## What the demo shows

1. **forge** `generic` (shape-only) and `debug` (strict, vocabulary-pinned) — two
   distinct attention-chain languages, induced from examples.
2. **prime** the debug language → grammar + a compiled attention block.
3. **gate** a valid debug AC → `clean ✓`.
4. **gate** an off-domain chain (`[Goal] ⇒ …` in the debug language) → rejected
   with verdict **`orthogonal`** (valid identifier, wrong vocabulary → steerable),
   fix: insert `Symptom`.

## API (what CORCC will consume)

```python
from accc import forge, gate, prime, attention_block, parse_ac

lang = forge("debug", debug_examples, db=".accc.db", strict=True)
violations, fixes = gate(lang, "[Symptom] ⇒ [Repro] ⇒ |Localize|")
block = attention_block("debug", "[Symptom] ⇒ [Repro] ⇒ |Localize|")
foci, held = parse_ac("[Symptom] ⇒ [Repro] ⇒ |Localize|")
```
