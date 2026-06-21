---
name: metaformal-self-test
description: How to verify agent/COG/gate/AIOS behavior WITHOUT calling LLMs or writing tautology asserts — by triggering the real thing in the real substrate and observing the state-change. Use when you're about to "test" something cognitive/agentic, when a test feels like `assert True == True`, or when you need to prove a gate/effect actually works. Read the story; copy the moves.
---

# Metaformal self-test — the way I actually did it (copy this, don't theorize)

> A metaformal self-test does NOT assert a predicted value. It **triggers the real thing in the real
> substrate and observes the state-change.** The observed state IS the proof. If it matches intent →
> green → freeze it (record the run, like below) and never re-litigate. If it surprises you → you just
> found a bug. Don't abstract it — just do what this story did.

## ONE TIME I needed to test whether the Challenger's gate actually works

I had written a `run_cog` "test" that did `assert r.admitted is True` — but `admitted` was hardcoded
`True` in the code. It was `assert True == True` in a costume. A hallucination. Isaac caught it and
said: there are no unit tests for this, only **metaformal self-tests** — trigger it for real, watch
the substrate.

**AND SO I** wrote the smallest possible script that triggers the *real* gate on *real* inputs (one
valid, two adversarial) and **prints what the gate actually emits** — no asserts, just observation —
**EXACTLY LIKE THIS:**

```python
from rulecatcher.db import connect
from chaincompiler.bridge import learn, gate
import tempfile, os
db = os.path.join(tempfile.mkdtemp(), "gate.db")
with connect(db) as cx:
    learn(cx, ["[ac:a] ⇒ [cor:b] ⇒ |C|", "[ac:a] ⇒ [ac:b] ⇒ [cor:c] ⇒ |D|"], scope="cog")
    valid_v,   _ = gate(cx, "[ac:x] ⇒ [cor:y] ⇒ |Z|", scope="cog")   # well-formed
    broken_v,  _ = gate(cx, "[ac:x] [cor:y] |Z|",      scope="cog")   # arrows missing
    foreign_v, _ = gate(cx, "[ac:x] ⇒ ❌NOPE❌ ⇒ |Z|",  scope="cog")   # foreign token
print("valid   :", len(valid_v),   "violations →", "ADMIT" if not valid_v   else "REJECT")
print("missing :", len(broken_v),  "violations →", "ADMIT" if not broken_v  else "REJECT")
print("foreign :", len(foreign_v), "violations →", "ADMIT" if not foreign_v else "REJECT")
```

**AND THEN I observed, verbatim:**

```
valid   : 0 violations → ADMIT
missing : 2 violations → REJECT
foreign : 0 violations → ADMIT      ← SURPRISE. it should have rejected this.
```

The first two were what I intended (the proof is the count I can see — the gate is the oracle, not
me). The third **contradicted my prediction**: the gate ADMITTED a foreign token `❌NOPE❌`. A normal
`assert` would have hidden that forever; the metaformal observation surfaced a real gap (the COG's
`learn(...)` uses only `next_kind` rules → catches missing structure, not foreign-token injection).

## How future-me lifts this (the move, generalized from the story)

1. **Don't assert a predicted value.** Write the smallest script that **triggers the real operation**
   (the gate, a `gba construct`, a DB automation, a materialize) **in the real substrate** (a temp db,
   a real dir, the live runtime).
2. **Print the observed state-change** — the violation count, the file that appeared (`os.path.exists`),
   the row in the DB, the search hit. Look at it.
3. **Compare to intent by eye.** Match → it works, and the printout IS the proof. Surprise → bug found.
4. **Freeze it:** paste the exact script + the exact observed output into a skill like this one
   ("ONE TIME I … AND SO I … EXACTLY LIKE THIS … AND THEN I observed …"), date it, and don't re-run /
   re-litigate it. The warrant going forward is: *observed live once; git history unbroken since.*
5. For a **cognitive/LLM** step (Select/Generate/meta-control), the "trigger" is dispatching a real
   agent (a Sonnet subagent, or me, in-runtime) and the "observed state" is what it left in the dir
   (the constructed SKILL.md, the kb note). Same shape: observe the substrate, freeze the anecdote.

The point: **the substrate is the oracle.** Write down the time it worked, verbatim. That's the test.

## ...AND THEN I fixed the gap the self-test found (the green follow-up)

The RED above (`foreign → ADMIT`) was real. I investigated location-first: the gate is **positional /
rule-triggered**, and `⇒` is *legitimately* followed by `[` OR `|` — a genuine branch point no
confidence-1.0 rule can govern — so foreign tokens *there* pass. Lowering confidence caught it but
**false-positived valid chains** (worse). So the fix wasn't a tweak; it was a feature: an **opt-in
closed-class vocabulary check**, `chaincompiler.bridge.gate(..., strict=True)` — derive the allowed
closed-class tokens from the learned artifacts; any closed-class token outside that set → `syntax_break`
(open-class IDENTIFIER/NUMBER always allowed). **AND THEN I observed the fix, verbatim:**

```
valid   : 0 → ADMIT
foreign : 2 → REJECT   ['❌(SYMBOL)', '❌(SYMBOL)']   ← the gap is closed
missing : 2 → REJECT
```

Frozen as `test_strict_gate.py` (3 metaformal checks). Lesson: a metaformal self-test that goes RED is
not a failure — it's the system telling you what to build. Characterize it (location-first), fix it,
re-observe GREEN, freeze both the finding and the fix.

## ...AND ANOTHER TIME I needed to prove "a domain built by chaincompiler" actually works

I re-expressed dietc (11 hand-coded Python modules, **0 skills**) as a `nutrition` AIOS built BY
chaincompiler (`examples/nutrition/build.py`): `make_gba` with three AC atoms (gap/cap/safety
attention) + a NOT-medical-advice role + a `90-safety` rule, then two flow-skills appended the same
way `make_gba` adds the loop flow — `nutrition-recommend` (CoR) and `compile-day` (the pipeline SC
that *calls* the dietc Python tools; the math stays in Python, the reading is the agent's).

**AND SO I** did NOT assert a predicted gap value. I triggered the **real build** (observe: closed,
0 violations, `compile-day` coord-addressed at `0.4`, the `90-safety` rule on disk) AND the **real
dietc pipeline** the flow narrates, on the PotatoDay fixture — **EXACTLY LIKE THIS:**

```python
state = engine.compile_day(FIX/"potato_day.yaml", profile, modules, items_override=items)
print("gaps:", {k: round(v) for k,v in list(state.gaps.items())[:3]})
print("patches:", [r.module_id for r in state.patches])
print("warnings:", state.warnings[:1])
```

**AND THEN I observed, verbatim:**

```
gaps: {'calories': 1680, 'protein_g': 112, 'fiber_g': 22}
patches: ['green_thing', 'protein_fiber_bar', 'electrolyte_water', ...]
warnings: ['patches add ~30 g fiber in one day; increase fiber gradually.']
```

The substrate produced a real, non-trivial reading (a potato-only day has a huge calorie gap) AND the
safety check actually fired — so the AIOS isn't a hollow shell; it's a real front end over the tools.
Frozen as `examples/nutrition/test_nutrition_aios.py` (2 metaformal observations: the emitted AIOS +
one real computation). The deliverable is the **template** it reveals: tools in Python, cognition in
AC/CoR skills, pipeline as a walked flow, gated + coord-addressed + self-expanding — what chaincompiler
then applies to itself.
