# Steward — Design (the Custodian genus, lowest rung)

> Canonical design for the `steward` package. The **non-graph** realization of CCC's
> Custodian genus, built bottom-up in ChainCompiler. The **graph realization (into CCC, as
> Cybernets)** is the committed next-conversation work — see §5.

## 1. The genus

CCC (`DESIGN.md §2.1`) settled that a **Custodian** = *"a loop-runner gated by a warrant."*
It runs the **O/F/I/A/P** loop; the **A-stage is the LOCK** = the warrant-freeze. The genus
has two *sibling* realizations:

- **Cybernet** — the game-being: a Core in neo4j, animated by an LLM through the MCP, gated
  by `required_pattern`. (Built in CCC. Not here.)
- **Steward** — the headless **automation/worker**: produces/admits artifacts, gated by a
  proto-SOMA placement gate. **Simpler. Not a Cybernet. This package.**

> Build bottom-up, **Stewards first** — do *not* start at the maximal/Cybernet layer.

## 2. The hierarchy (built bottom-up)

```
STEWARD        = loop-runner GATED BY a warrant ; PRODUCES one-type ; headless
SPECIALIZER    IS A STEWARD ; the maximal one ; SPECIALIZES ; PRODUCES Cybernets   (in CCC)
THE_SPECIALISTS = SPECIALIZER PRODUCES [specialist] ; each SPECIALIZES one part ∈ {Core, SM, Chain, Compiler}
META_WORKFLOW  IS A Chain the SPECIALIZER CALLS ; PRESENTS_AS "1 LLM" ; INSTANTIATES sequence-of(Steward)
```

Realized here:
- **`Steward`** (`core.py`) — the base: O→F→I→A(lock)→P over the one type (`Artifact` = a
  skill-dir spec). The A-lock is `Warrant.check` (admit/crystallize or reject).
- **specialist Stewards** (`specialists.py`) — `chain_steward` / `sm_steward` /
  `compiler_steward` / `core_steward`: each concentrates on one part-kind (CCC §6 Gear).
- **`meta_steward`** — a Steward whose maker runs a **sequence** of Stewards, threading each
  admitted artifact forward. **Presents as one** (`kind='workflow'`, `presents_as: "1 LLM"`)
  but **runs many**. Homoiconic: it returns a plain `Steward`, so meta-Stewards nest.

## 3. The warrant ladder (the merge axis)

The warrant has a **fidelity tier** (`warrants.py`), so the upgrade path is explicit in code:

| tier | warrant | = CCC | 
|---|---|---|
| `proto_soma` | `shape(regex)` / `non_empty()` | the `required_pattern` gate (today) |
| `grammar` | `glyph_grammar(vocab)` — rulecatcher ok/orthogonal/syntax_break | the warrant **upgrade** |
| `soma` | (CB/CartON geometry closure) | the top of the ladder (not built here) |

The same Steward loop swaps tiers without changing — demonstrated: a Steward gated by
`glyph_grammar` admits a canonical glyph code (`ok`) and admits-with-repair a reversed one
(`orthogonal → canonicalized`). **This is exactly the warrant upgrade the CCC merge wants**
(`DESIGN.md §2.1`: "warrant upgraded from the proto-SOMA regex gate toward SOMA").

## 4. Bijection to CCC (what maps to what when this federates)

| steward (here, off-graph) | CCC (graph) |
|---|---|
| `Steward` (Custodian sibling) | `:Cybernet` (Custodian sibling) |
| `Artifact` (skill-dir, the one type) | a procedure (SM + content) ↔ its external skill pointer |
| `Warrant.check` (the A-lock) | `_evaluate_pattern` / `required_pattern` (the 403 gate) |
| `Warrant.tier` ladder | proto-SOMA regex → rulecatcher → SOMA |
| `chain/sm/compiler/core` stewards | the Gear part-kinds (Chain/SM/Compiler/Core) |
| `meta_steward` (runs many, reads as one) | a Compiler / Core `CORE_RUNS` (SM-of-SMs) |
| O/F/I/A/P loop | the Custodian cognition loop; A = the lock/warrant-freeze |

## 5. ASPIRATIONAL — the CCC realization (NEXT CONVERSATION, committed)

Implement the **same hierarchy into CCC on the graph**: a Steward becomes a headless worker
federated as a `:Cybernet`; the warrant becomes the step gate, upgraded from the regex
`required_pattern` toward rulecatcher/SOMA. The maximal Steward = the specializing Steward
that makes Cybernets; its specialists = Cybernets per part-kind; the meta-workflow = a
Compiler SM that calls a sequence of autonomous workers but reads as one tick. (CCC `DESIGN.md §2.1`
unification path; unblocked by the §11.8 gate fix.)
