# HoneyC

A compiler and CLI for **Dense Rune-Chain Notation** — a compact symbolic
notation for entities, relations, types, scopes, transforms, bounded mediator
objects, placeholders, and agent-executable chains.

HoneyC turns dense rune text into an AST, normalized semantic triples, Prolog
facts, Neo4j Cypher, and human-readable lenses, and it validates chains with
rewrite suggestions.

```txt
RuneText → AST → Semantic Triples → Prolog → Cypher → Rendered Lenses
```

This is the back-end compiler in a larger system: a **rule-catcher** learns an
emergent notation's grammar from examples; HoneyC compiles a ratified grammar
into IR + lenses; domain compilers (e.g. DietC, or cognition-chain compilers for
attention-chains / CoRs / skillchains) sit on top.

## Install

```bash
python3 -m pip install --no-build-isolation -e .
```

## CLI

```bash
honeyc parse   examples/mbr.rune
honeyc norm    examples/mbr.rune
honeyc prolog  examples/mbr.rune
honeyc cypher  examples/mbr.rune
honeyc render  examples/mbr.rune --as readable    # also: --as triples | --as prose
honeyc check   examples/mbr.rune
```

## Core notation

| Form | Meaning |
|------|---------|
| `[X]` | named entity |
| `[X]: T` | entity `X` has type `T` |
| `\|X\|` | `X` is bounded / stabilized / a handleable object |
| `A ⇔ B` | operational equivalence (both directions) |
| `A ⇒ B` | `A` produces `B` |
| `A ⇢ B` | `A` compiles to `B` |
| `A → B` / `A ↦ B` | points-to / maps-to |
| `A -rel-> B` / `A <rel- B` / `A <rel> B` | forward / reverse / bidirectional relation |
| `A:{ B, C, 📃 }` | scope: `A` contains `B`, `C`, and an expandable placeholder |
| `📃` | drilldown placeholder (expand one level deeper) |
| `${A ⇒ B}` | the transform from `A` to `B` as a first-class object |

**Backbone rule:** equivalence/production connectors advance the chain backbone;
relation markers (`<is_a-` etc.) hang their operand as a *leaf* off the current
backbone node. So `[Mbr] <is_a-🌸‍💧 ⇔ |🍯|` means `is_a(Mbr, Nectar)` **and**
`equiv(Mbr, Honey)` — Nectar does not become the left operand of the `⇔`.

A bounded term sitting between two backbone links is inferred as a **mediator**:
`[Mbr] ⇔ |🍯| ⇔ [Mbl]` ⟹ `mediates(🍯, Mbr, Mbl)`.

## Core example

```txt
[Mbr]: M*Boundary <is_a-🌸‍💧 ⇔ |🍯| ⇔ [Mbl]: M*Blanket <is_a-🍹
```

`honeyc norm` →

```txt
Mbr has_type M*Boundary
Mbr is_a 🌸‍💧
🍯 bounded true
Mbr equiv 🍯
🍯 equiv Mbl
Mbl has_type M*Blanket
Mbl is_a 🍹
🍯 mediates Mbr target=Mbl
```

## Pipeline

```txt
parser.py     RuneText ⇢ Lark tree ⇢ AST dataclasses (ast_nodes.py)
normalize.py  AST ⇢ flat Statement triples
emit_prolog.py / emit_cypher.py   triples ⇢ facts / graph
render.py     AST/triples ⇢ readable | triples | prose
check.py      AST ⇢ warnings + suggested rewrites
```

## Extending

- **New connector/glyph:** add a terminal to `grammar.lark`, a handler in
  `parser.py`, a predicate in `normalize._CONNECTOR_PREDICATE`, and a label in
  the emitters / `symbols.py`.
- **New renderer lens:** add a mode to `render.render`.
- **New domain compiler:** consume `honeyc.normalize` output and add your own
  ontology/engine on top (this is how DietC is built).

## MVP limitations

- Cypher is emitted as text (no live Neo4j driver); Prolog is emitted as text
  (no embedded SWI-Prolog).
- The third bundled example (`transform_chain.rune`) parses but exercises only
  partial transform-object semantics.
- Unicode tokenization is permissive by design — validation happens in `check`.

## Tests

```bash
pytest        # 19 tests: parser, normalize, emitters, render, check
```
