# examples/nutrition — a domain built BY chaincompiler (the v1 recursion)

This is **dietc re-expressed as a chaincompiler-built AIOS**. dietc was meant to be *the worked
example made by the system*, but it shipped as 11 hand-coded Python modules with **0 skills / 0
chains** — the recursion (*chaincompiler makes dietc*) never ran on it. This example runs it, and in
doing so reveals the **template** for any domain built on the stack.

## The split (the law: only code what MUST execute)

| dietc piece | becomes | why |
|---|---|---|
| `vectors`, `gapcap.compute`, `patch.plan`, `safety.check`, `load.*`, `engine.*` | **Python tools** (kept, in `dietc`) | exact arithmetic + IO = must-execute |
| "attend to targets vs current → gaps", "current vs limits → caps", "is it safe?" | **AC skills** (`gap/cap/safety` attention) | how to think (inner frames) |
| "weigh gaps vs caps → pick a module" | **CoR skill** (`nutrition-recommend`) | spoken reasoning → a decision |
| `engine.compile_day` (the pipeline) | **flow-skill** (`compile-day`) | orchestration = a walked flow |
| rendering | honeyc lens | rendering is honeyc's job |

The numbers stay exact: the AC/CoR frames decide **what to compute and how to read it**; the Python
tools **do the math**. A prompt never computes a nutrient value. dietc's **"NOT medical advice"** frame
is preserved in the role + the `90-safety` rule.

## Build it

```
python3 examples/nutrition/build.py
# nutrition AIOS → .../examples/nutrition/aios
#   closed: True  violations: 0  indexed skills: 9
#   rules: ['01-bandit-loop.md', '02-the-law.md', '03-kb-reward.md', '04-self-expansion.md', '90-safety.md']
```

`build.py` calls `make_gba("nutrition", aios/, atoms=[gap, cap, safety])` (→ 3 ACs + the
NutritionBandit CoR + the rollup SC + the loop flow, coord-addressed), then appends the
`nutrition-recommend` CoR and the `compile-day` pipeline flow-skill the same way `make_gba` adds the
loop flow. The emitted `aios/` is a real AIOS dir an agent goes to and becomes.

## Verify (metaformal — the substrate is the oracle)

```
pytest examples/nutrition/test_nutrition_aios.py
```

It does **not** assert a predicted value. It triggers the real build (observe: closed, validated,
`compile-day` coord-addressed, `90-safety` on disk) and the real dietc pipeline on the `PotatoDay`
fixture (a potato-only day → a 1680 kcal gap; the safety check fires). The frozen anecdote lives in
the `metaformal-self-test` skill.

## What it proves

The **AIOS template** for any domain-compiler on the stack: tools in Python, cognition in AC/CoR
skills, the pipeline as a walked flow, gated + coord-addressed + self-expanding. dietc is the first
real instance; the template is the deliverable — the thing chaincompiler then applies to *itself*.
