# goldenreq — the acceptance gate for goldenization

**The gauge is not the handler.** A *gauge* is an internal self-assessment — the
bandit's 2×🏆 on a constructed chain, a rulecatcher candidate rule, a forged
template, a personapack `activation_grade` claim. A gauge can detect quality; it
may **never** certify itself into golden/adopted/canon. That certification is a
*handler*'s job — an external acceptance authority. `goldenreq` is that gate.

The two-knob / CC loop is acceptable **only if** goldenization goes through this
gate. Before, chainaios's bandit rule told the agent to self-fold a 2×🏆 chain
into golden — self-certification. Now the rule says: **file a goldenization
request; promotion happens only on an accepted verdict.**

## Install

```bash
pip install goldenreq
```

It depends on nothing outside the standard library, and it installs the `goldenreq` command. It is one of the fifteen
packages of [ChainCompiler](https://github.com/sancovp/chaincompiler); to work on it, clone the repository and run
`./install.sh`, which installs all fifteen editable.

## The flow

```
gauge  ──file_request(kind, candidate_id, evidence, requested_promotion, requester)──►  queue (pending)
                                                                                          │
handler ──accept(request_id, by, reason) ──► fires the promotion effect ──► golden / grade-bump / …
        └─reject(request_id, by, reason) ──► NO effect; reason recorded (a hard negative)
```

- **Requests carry receipts.** `evidence` is the graded KB notes / cert ids /
  forge reports behind the claim. An unevidenced ask is a weak ask.
- **Verdicts are the seed corpus** for the learned acceptance model that will
  one day staff this gate automatically. **Rejections (with reasons) are its
  hard negatives.** No trace → no handler → not annealable, only believable.

## Kinds → effects

| kind | gauge upstream | effect on accept |
|---|---|---|
| `chain-golden` | a bandit chain earned 🏆 twice | append an `ACCEPTED-BY` marker into the GBA KB note (never rewrites agent notes) |
| `pack-grade-bump` | a personapack PackEntry | **pure** helper returns the new `activation_grade`; personapack applies it |
| `rule-adopt` | a rulecatcher candidate | **stub** → points at `rulecatcher.engine.adopt_rules` (no fake integration) |
| `template-promote` | a forged language/template | **stub** → no canonical-template promotion API to call yet |

## Record shape

The verdict record mirrors `base/acceptance`'s `acceptance.schema.Verdict`
(read via `git show acceptance-handler:…`) so the verdicts JSONL is drop-in for
that reader — **by shape, not by import** (no cross-branch coupling). The
field-by-field mapping is documented at the top of `verdict.py`.

## CLI

```
goldenreq list                          # the handler's inbox (pending requests)
goldenreq accept <id> --by human:alice  # rule accept → fire the effect
goldenreq reject <id> --by human:alice --reason "…"   # rule reject (reason required)
```
