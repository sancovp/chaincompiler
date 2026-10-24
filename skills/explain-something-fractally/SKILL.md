---
name: explain-something-fractally
description: Skillchain — ac:fractal-top-pass → ac:fractal-per-part-pass → cor:fractal-explainer → FractalExplanation
---

# explain-something-fractally — compiled skillchain

> Compiled by `skillchain.py`. Orchestrates 3 step(s) composing 3 skill(s).
> **Dependencies (validated present at compile time):** `fractal-explainer`, `fractal-per-part-pass`, `fractal-top-pass`

**Execute the steps below in order.** Carry each step's result forward; where a step references `{var}`, substitute the captured value from the named earlier step.

## Step 1 — invoke skill `fractal-top-pass`
*ExplainSomethingFractally top-pass AC — the LFP roll-up outer loop — give the one-breath Overview, enumerate EVERY part (the expected-complete set), define each part, roll up to the least fixed point → hold Compose (the whole reads as one figured-out thing).*

Invoke the **fractal-top-pass** skill (no extra input)

## Step 2 — invoke skill `fractal-per-part-pass`
*ExplainSomethingFractally per-part AC — the fractal move — take one Part, define its what/when/how/utility, ask whether it needs its own pass → hold RecurseOrClose (re-enter this same chain on the part, or close it; the explanation is done only when every branch has closed — the fixed point).*

Invoke the **fractal-per-part-pass** skill (no extra input)

## Step 3 — invoke skill `fractal-explainer`
*Chain-of-reasoning (spoken, ends in a decision) — explain anything as an LFP roll-up — overview, enumerate the parts, define each part (what/when/how/utility), recurse into any part that needs its own pass until the fixed point closes, then compose the whole granularly.*

Invoke the **fractal-explainer** skill (no extra input)

## Done
Return the final step's output as the result of this chain.
