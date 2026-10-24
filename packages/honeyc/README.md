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

One reading of every marker the grammar (`src/honeyc/grammar.lark`) defines. **Triples** are the statements `honeyc
norm` prints for the **Example**, leaving out each term's own marker statement (`A entity true`, `A symbol true`,
`🍯 glyph true`) save in the three rows that define them. `tests/test_readme_notation.py` parses every example in this
table and checks that it gives exactly these triples.

| Marker | Reads as | Example | Triples |
|---|---|---|---|
| `[X]` | a named entity | `[A]` | `A entity true` |
| `X` | a bare name: a symbol | `A` | `A symbol true` |
| a glyph | a glyph — a run of characters that are neither structure nor an ASCII name (`symbols.py` names the known ones) | `🍯` | `🍯 glyph true` |
| `X: T` | `X` has type `T` | `[A]: T` | `A has_type T` |
| `\|X\|` | `X` is bounded — stabilized, a handleable object | `\|[A]\|` | `A bounded true` |
| `A ⇔ B` | operational equivalence, both ways | `[A] ⇔ [B]` | `A equiv B` · `B equiv A` |
| `A ⇒ B` | `A` produces `B` | `[A] ⇒ [B]` | `A produces B` |
| `A ⇢ B` | `A` compiles to `B` | `[A] ⇢ [B]` | `A compiles_to B` |
| `A ↦ B` | `A` maps to `B` | `[A] ↦ [B]` | `A maps_to B` |
| `A → B` | `A` points to `B` | `[A] → [B]` | `A points_to B` |
| `A ⟶ B` | `A` transitions to `B` | `[A] ⟶ [B]` | `A transitions_to B` |
| `A ⟼ B` | `A` transforms into `B` at run time | `[A] ⟼ [B]` | `A runtime_transform B` |
| `A -rel-> B` | the relation `rel(A, B)` | `[A] -owns-> [B]` | `A owns B` |
| `A <rel- B` | the same relation `rel(A, B)`, written the other way | `[A] <owns- [B]` | `A owns B` |
| `A <rel> B` | the relation both ways: `rel(A, B)` and `rel(B, A)` | `[A] <owns> [B]` | `A owns B` · `B owns A` |
| `A:{ B, C }` | a scope: `A` contains `B` and `C` (a `,` separates its members) | `[A]:{ [B], [C] }` | `A contains B` · `A contains C` |
| `{ B, C }` | a scope with no name: its owner is `_group` | `{ [B], [C] }` | `_group contains B` · `_group contains C` |
| `📃` | a drilldown placeholder: expand this one level deeper | `[A]:{ 📃 }` | `A placeholder drilldown` |
| `${A ⇒ B}` | the transform from `A` to `B` as a first-class object, named `xf_` and eight hex digits of a hash of its chain | `${[A] ⇒ [B]}` | `xf_… transform true` · `A produces B` · `xf_… source A` · `xf_… target B` · `xf_… operator produces` |
| `A := B` | `A` is assigned `B` | `[A] := [B]` | `A assign B` |

**`-rel->` and `<rel-` are two spellings of one relation.** `[A] -owns-> [B]` and `[A] <owns- [B]` both read
`owns(A, B)`; `<owns>` reads it both ways. A lens that writes the chain back writes each relation the way it was read.

**Backbone rule:** every connector but a relation advances the chain's backbone; a relation hangs its operand as a
*leaf* off the current backbone node. So `[A] -owns-> [B] ⇔ [C]` reads `owns(A, B)` **and** `equiv(A, C)` — `B` does not
become the left operand of the `⇔`.

A bounded term sitting between two backbone links is inferred as a **mediator**: `[A] ⇔ |🍯| ⇔ [B]` reads
`mediates(🍯, A, B)` — `honeyc norm` prints `🍯 mediates A target=B`. A relation an author names `mediates`
(`[A] -mediates-> [B]`) is an ordinary relation, `A mediates B`. `honeyc check` warns of an unbounded term in a
mediator's place and suggests the whole chain as it was written with that term bounded: `[A] ⇔ 🍯 ⇔ [B]` →
`[A] ⇔ |🍯| ⇔ [B]`, which parses back to the chain's statements plus `🍯 bounded true` and the mediation.

## Core example

```txt
[Mbr]: M*Boundary <is_a-🌸‍💧 ⇔ |🍯| ⇔ [Mbl]: M*Blanket <is_a-🍹
```

`honeyc render --as triples` (the statements, each term's own marker left out) →

```txt
Mbr has_type M*Boundary
🍯 bounded true
Mbl has_type M*Blanket
Mbr is_a 🌸‍💧
Mbr equiv 🍯
🍯 equiv Mbr
🍯 equiv Mbl
Mbl equiv 🍯
Mbl is_a 🍹
🍯 mediates Mbr target=Mbl
```

## The lenses

`readable` writes the chain back — each relation in the spelling it was read, each known glyph with its name beside
it (`[🌸‍💧: Nectar]`), so it is for reading; `triples`, `prose`, Prolog (`honeyc prolog`) and Cypher (`honeyc cypher`) are
read from the statements.

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
pytest        # the parser, normalize, the emitters, the lenses, check, this README's notation table, and dietc
```
