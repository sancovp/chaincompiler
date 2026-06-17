# RuleCatcher

`rulecatcher` is a small SQLite-backed CLI for catching emergent syntax rules from symbolic text.

The first version is intentionally simple:

1. Read one or more text files.
2. Learn repeated next-token expectations from history.
3. Store those expectations as candidate rules with evidence and confidence.
4. Let a human adopt or reject the rules.
5. Lint future text against the adopted rule stack.
6. Suggest normalizations when the stack predicts a different next token.

This is not a full parser or reasoning engine. It is the first runtime loop for:

```txt
observe pattern
-> propose rule
-> adopt/reject
-> stack rule
-> lint future text
-> normalize drift
```

## Why SQLite

The system needs durable internal state for:

- candidate rules
- rule evidence
- adoption status
- decision history
- source artifacts
- stack history

That becomes database-shaped quickly, so the MVP uses SQLite as the source of truth.

## Commands

```bash
rulecatcher catch examples/runes.txt
cat examples/runes.txt | rulecatcher catch - --label shell-demo
rulecatcher review
rulecatcher review --scope syntax --rule-type next_kind
rulecatcher review --scope syntax --json
rulecatcher adopt 1 --actor silas --reason "stable core syntax"
rulecatcher reject 7 --source review-loop --reason "too noisy"
rulecatcher stack --scope global
rulecatcher explain 3 --json
rulecatcher explain --scope alpha --rule-type next_token --prefix-token state --prefix-token '=>' --expected-token open
rulecatcher report --scope alpha --json
rulecatcher export-scope --scope alpha > alpha.rulecatcher.json
rulecatcher import-scope alpha.rulecatcher.json --scope beta --replace-scope --json
rulecatcher compare scope:alpha scope:beta --json
rulecatcher compare alpha.rulecatcher.json scope:alpha
rulecatcher triage --scope global
rulecatcher triage --scope global --focus all
rulecatcher triage --scope global --all
rulecatcher triage --scope alpha --recommendation review --json
rulecatcher apply-triage --scope alpha --recommendation adopt --dry-run --json
rulecatcher apply-triage --scope alpha --recommendation adopt --focus core --actor silas
rulecatcher apply-triage --scope alpha --recommendation adopt --actor silas
rulecatcher history --scope global --json
rulecatcher govern --scope global
rulecatcher govern --scope alpha --recommendation review --json
rulecatcher graph --scope global --format mermaid
rulecatcher graph --scope syntax --layer rules --rule-type next_kind --format table
rulecatcher graph --scope alpha --layer metasystem --format dot
rulecatcher graph --scope alpha --layer metasystem --json
rulecatcher conflicts --scope syntax --json
rulecatcher lint examples/runes_broken.txt
printf 'state => closed\n' | rulecatcher lint - --label incoming-check
printf 'door closed\n' | rulecatcher lint - --scope syntax --json
rulecatcher normalize examples/runes_broken.txt
rulecatcher normalize examples/runes_broken.txt --in-place
printf 'state => closed\nmode => safe\n' | rulecatcher session --scope alpha --label live --format jsonl
printf 'door => open\nwindow => closed\n' | rulecatcher session --scope beta --label learn-beta --learn --format jsonl
printf 'state => open\nstate => open\nstate => open\n' | rulecatcher session --scope alpha --label teach --learn --triage --format jsonl
printf 'state => open\nstate => open\nstate => open\n' | rulecatcher session --scope alpha --label auto --learn --triage --apply-triage adopt --format jsonl
```

All commands accept `--db` to choose a database path. The default is `.rulecatcher.db` in the current working directory.
Commands that read or apply rules also accept `--scope`, so multiple emergent
DSLs can live in one database without contaminating each other.
Use `catch --replace-scope` when you want to discard a scope and rebuild it
from a new artifact set instead of accumulating more history.

## Rule Types in the MVP

The MVP learns two rule families:

- `next_token`: for a repeated prefix history, expect a specific next token
- `next_kind`: for a repeated syntax-class prefix, expect a specific token class

Example:

```txt
state => open
state => open
state => open
```

This can induce a rule like:

```txt
["state", "=>"] -> "open"
```

If future text says:

```txt
state => closed
```

then `lint` can flag the drift and `normalize` can suggest `open`.

Class rules are what let the tool generalize beyond exact strings. If it sees
enough examples of:

```txt
identifier => identifier
```

it can learn reusable syntax expectations like:

```txt
[<IDENTIFIER>] -> <OPERATOR>
[<IDENTIFIER>, <OPERATOR>] -> <IDENTIFIER>
```

That means novel text such as `door closed` can be flagged as structurally
broken even if `door` and `closed` never appeared in the corpus.

## Keyword-Aware Tokenization

By default the tokenizer classifies every word as `<IDENTIFIER>`. For notations
where certain words are structural keywords (e.g. `state`, `as` in a state-graph
DSL), that conflation hides grammar: a declaration like `state x ...` and a
transition like `name --> ...` share the `[<BOS>, IDENTIFIER]` prefix and pull
the line-initial rule's confidence down.

Pass `--keyword` (repeatable) to `catch` to lift chosen words into their own
`<KEYWORD>` class:

```bash
rulecatcher catch grammar.txt --scope dsl --keyword state --keyword as
```

The keyword set is persisted per scope, so `lint`, `normalize`, and
`session --learn` reconstruct the same token classes automatically — you only
declare keywords at `catch` time. Omitting `--keyword` on a later `catch`
reuses the scope's stored keywords; the default (no keywords ever set) is
unchanged from prior behaviour.

## Example

See [examples/runes.txt](examples/runes.txt) and [examples/runes_broken.txt](examples/runes_broken.txt).

## Installation

For normal development:

```bash
python3 -m pip install --no-build-isolation -e .
```

The `--no-build-isolation` form matters in offline or restricted environments
where `pip` cannot download build dependencies.

You can also run the module directly:

```bash
python3 -m rulecatcher --help
```

## Machine Use

Most governance commands now support `--json`, which is the preferred mode when
another LLM or automation wants to consume the tool programmatically.

High-value machine surfaces:

- `review --json`
- `stack --json`
- `explain --json`
- `report --json`
- `import-scope --json`
- `compare --json`
- `triage --json`
- `apply-triage --json`
- `history --json`
- `govern --json`
- `conflicts --json`
- `graph --json`
- `lint --json`
- `normalize --json`
- `session --format jsonl`

This lets another model consume stable rule objects, explicit graph nodes and
edges, lint violations, normalization suggestions, and conflict groups without
scraping human-oriented text.

## Scope Report

`rulecatcher report` is the one-call orientation surface for a live scope.

Example:

```bash
rulecatcher report --scope alpha --json
rulecatcher report --scope alpha
```

The report aggregates:

- scope summary counts
- active adopted stack
- pending triage pressure
- health attention on adopted rules
- conflict groups
- recent decision history
- derived next-action items

This is the shell surface for asking: "what matters in this scope right now,
and what should I do next?"

## Rule Explain

`rulecatcher explain` answers the question "why this rule?" in one call.

It can resolve a rule by local id:

```bash
rulecatcher explain 3 --json
```

Or by stable signature:

```bash
rulecatcher explain --scope alpha --rule-type next_token --prefix-token state --prefix-token '=>' --expected-token open
```

The explanation payload includes:

- the canonical rule object
- rule health and recommendation
- supporting evidence rows
- decision history for the same rule signature
- competing rules with the same prefix
- observed transition alternatives for that prefix

This is the shell surface for asking: "what made this rule appear, how stable
is it, and what else could have happened here?"

## Structural Repair Hints

When a generalized `next_kind` rule catches a novel structural syntax break,
`rulecatcher normalize` now surfaces grounded concrete token hints from the
rule's observed evidence instead of only the abstract expected class.

For example, if a scope learned that identifiers are usually followed by `=>`,
then input like:

```txt
door closed
```

can yield a suggestion such as:

```txt
consider inserting one of ['=>'] before 'closed'
```

These hints are intentionally advisory. They help another LLM repair syntax
using observed evidence, but they do not pretend that a class-rule violation is
always safe to auto-rewrite.

## Portability

`rulecatcher export-scope` and `rulecatcher import-scope` make a learned
language stack portable.

The snapshot includes:

- artifacts bound to the scope
- observed transitions
- candidate and adopted rules with evidence
- rule health counters
- decision history

This gives another LLM a shareable JSON bundle for replaying a scope elsewhere.
Use `import-scope --replace-scope` when you want the target scope to be rebuilt
from the snapshot instead of merged into the existing local state.

## Evolution Compare

`rulecatcher compare` lets another LLM inspect how one language state differs
from another.

It accepts two references:

- a local scope name such as `alpha` or `scope:alpha`
- an exported snapshot path such as `alpha.rulecatcher.json` or `snapshot:alpha.rulecatcher.json`

Example:

```bash
rulecatcher compare scope:alpha scope:beta --json
rulecatcher compare alpha-before.rulecatcher.json scope:alpha
```

The comparison payload is signature-based rather than id-based, so it survives
export/import and can report:

- rules added, removed, or changed
- observed transition deltas
- decision-history additions and removals
- artifact-path changes across corpora

This is the shell surface for asking: "what language did I have before, what
language do I have now, and what actually changed?"

## Candidate Triage

`rulecatcher triage` closes the gap between "a pattern exists" and "should this
become part of the language stack?"

It only inspects pending rules and turns them into explicit proposals with
recommendations:

- `adopt`: strong candidate with no known conflict
- `review`: candidate needs a deliberate decision because the evidence is mixed
  or it conflicts with the active stack
- `reject`: candidate is currently weaker than a competing pending rule for the
  same prefix

By default, triage only emits the frontier proposals and then auto-focuses on
core rules that are not mostly BOS/EOL boundary framing. Use `--focus all` when
you want the full proposal set, including boundary-heavy rules. `--focus core`
forces only the core subset.

This is the surface another LLM can use to ask: "you seem to be inventing this
rule; do you want to keep it?"

## Batch Application

`rulecatcher apply-triage` lets another LLM move from recommendation to action
without issuing one `adopt` or `reject` call per rule.

It selects the same filtered proposal set that `triage` would expose, then
applies the chosen recommendation family through the normal decision pathway so
history still records provenance and rationale. Use `--dry-run` to preview the
exact proposal set before mutating the stack. It respects the same focus policy
as `triage`, so the default application path also prefers core rules over
boundary-only boilerplate.

## Decision History

`rulecatcher history` makes the evolution of the language stack inspectable.

Every explicit `adopt` or `reject` decision is now persisted with optional
`actor`, `source`, and `reason` metadata. When adopting a rule automatically
displaces an older adopted rule for the same prefix, that displacement is also
recorded as an automatic history event.

This lets another LLM answer questions like:

- "why is this rule in the stack?"
- "what replaced the previous rule?"
- "was this change deliberate or automatic?"

## Rule Health

`rulecatcher govern` turns accumulated lint outcomes into a health surface for
the active rule stack.

Recommendation heuristics in this version:

- `untested`: the rule has never been evaluated during linting or live sessions
- `tentative`: the rule has only clean hits so far, but not enough repetitions
  to call it stable
- `healthy`: the rule has at least three clean hits and no violations
- `watch`: the rule has started drifting and should be monitored
- `review`: the rule is breaking often enough that the stack should probably be
  reconsidered

This is the governance surface that answers: "the history predicted this next,
but reality did something else; is that rule still worth keeping?"

## Live Sessions

`rulecatcher session` is the stream-oriented surface for real-time use.

It reads stdin line by line and emits one event per input line plus a final
summary event. With `--learn`, the full stream is also folded back into the
scope as a new learnable artifact after the line events are emitted. With
`--triage`, the stream also emits a pending-rule proposal event so newly caught
patterns can be surfaced immediately. With `--apply-triage`, a session can also
batch-apply selected recommendation families directly after triage. Use
`--triage-focus` when you want to force `core` or `all` proposal visibility in
live runs.

## Notes

- The tokenizer is intentionally light and dependency-free.
- This version optimizes for the governance loop, not perfect language generalization.
- Graph and hypergraph projections can be layered on later from the SQLite store.

## Metasystem-Transition Graph

`rulecatcher graph` now builds an explicit graph object first, then renders it
for the shell.

Example:

```bash
rulecatcher graph --format mermaid
rulecatcher graph --scope syntax --layer rules --rule-type next_kind --format table
rulecatcher graph --scope alpha --layer metasystem --format dot
rulecatcher graph --scope alpha --layer metasystem --json
```

Available layers:

- `observed`: raw prefix-to-next-token transitions
- `rules`: explicit stacked rule geometry
- `metasystem`: observed transitions plus rules, decision history, and rule health

The `--json` surface now includes `graph.nodes`, `graph.edges`, and `summary`,
so another LLM can traverse the learned syntax geometry directly instead of
reconstructing it from flat rows. `--format dot` gives a shell-friendly export
path for Graphviz or other downstream tooling.
