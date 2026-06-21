# DietC → a chaincompiler-built AIOS  (the v1 recursion) — BUILD PLAN

> **Resumable after compaction.** This is the plan to execute decision **(b)**: re-express dietc as a
> domain **built BY chaincompiler** (a `nutrition` GBA/AIOS), instead of the current hand-coded Python
> package. It runs the original recursion: *chaincompiler makes dietc → finishing it reveals the AIOS
> template → chaincompiler becomes one.* Read this, then build. Don't re-derive — the analysis is here.

## 0. Why
dietc was supposed to be **the worked example made by the system**. Audit (2026-06-17): it's 11 hand-coded
Python modules, **0 skills / 0 chains** — the recursion never ran on it. Now the machinery exists
(`make_gba`, `roll_up_algebra`, `construct_into`, the flow-skill pattern, coords, the strict gate,
metaformal self-tests), so we build dietc the right way and it becomes the reference for "a domain made
by chaincompiler."

## 1. The split — functions vs instructions (the law: only code what MUST execute)
dietc's **real computation + IO stays Python TOOLS** (a chain *calls* them; never turn arithmetic into a
prompt). dietc's **orchestration + "how to think" become skills/chains** (prompts the agent walks).

| dietc piece (current) | becomes | why |
|---|---|---|
| `vectors.positive_gap/positive_cap`, `NutrientVector` | **Python tool** (keep) | exact arithmetic = must-execute |
| `gapcap.compute`, `patch.plan` (+ `_score`), `safety.check` | **Python tool** (keep) | real computation/scoring |
| `load.*` (yaml→models), `models.*`, `engine.build_day_state` | **Python tool** (keep) | IO + typed state |
| `engine.compile_day` (the **pipeline**) | **flow-skill** (the AIOS default workflow) | orchestration = a walked flow |
| "weigh gaps vs caps → recommend a module" (the patch *decision*) | **CoR skill** | spoken reasoning → a decision |
| "attend to targets vs current → gaps", "current vs limits → caps", "is this safe?" | **AC skills** | how to think (inner frames) |
| `rune.render_via_honeyc`, `render.render_prose` | **honeyc lens** (already on honeyc) | rendering = honeyc's job |

**Guardrail:** the numbers must stay exact — the AC/CoR frames *decide what to compute and how to read
it*; the Python tools *do the math*. Keep dietc's **"NOT medical advice"** safety framing in the CoR + a
safety AC. Never compute a gap/cap in a prompt.

## 2. Target structure (a `nutrition` AIOS built by the bandit)
```
nutrition/                              ← a GBA/AIOS (make_gba), the dietc domain
  CLAUDE.md                             role block: "you are the nutrition bandit" (+ NOT medical advice)
  .claude/rules/                        the loop + the law + kb + self-expansion + a SAFETY rule
  .claude/skills/   (coord-addressed, the tree)
    0-nutrition/SKILL.md                root SC (the domain)
    0.x-nutrition-loop                  default workflow (BanditChain) — already auto-added by make_gba
    <gap-attn>     (AC)  [Targets] ⇒ [Current] ⇒ |Gaps|
    <cap-attn>     (AC)  [Current] ⇒ [Limits] ⇒ |Caps|
    <safety-attn>  (AC)  [Item] ⇒ [Interactions] ⇒ |Safe?|
    <recommend>    (CoR) weigh gaps vs caps, pick the module that fills most gap w/o breaching caps → decide
    <compile-day>  (SC)  the PIPELINE flow: load → day-state → gapcap → patch → safety → render
  kb/                                   reward record
  tools  → the dietc Python (vectors/gapcap/patch/safety/load/engine) stay importable; the chain calls them
```

## 3. Build steps (execute in order)
1. `make_gba("nutrition", <root>, atoms=["[Targets] ⇒ [Current] ⇒ |Gaps|"])` — scaffold the AIOS
   (gets CLAUDE.md role + rules + loop flow-skill + tree + index, coord-addressed, validated).
2. `construct_into` the AC frames: `gap-attn`, `cap-attn`, `safety-attn` (place them in the tree by coord).
3. Add the **`recommend` CoR** (the patch decision) and the **`compile-day` SC** (the pipeline flow-skill):
   the SC body = walk `load → build_day_state → gapcap.compute → patch.plan → safety.check → render`,
   each step **calling the dietc Python tool** (cite the function). Gate every skill (strict where it's a
   closed DSL). Everything lands in the tree (coords resolve).
4. Add a **`90-safety.md` rule** in `.claude/rules`: "NOT medical advice; always run `safety.check`
   before recommending; surface caps breaches."
5. Keep `packages/honeyc/src/dietc/*` Python as the **tool layer** (don't delete — the chain calls it).
   Optionally thin `dietc/cli.py` to note "the AIOS is the front end now; these are its tools."

## 4. Acceptance — a metaformal self-test (the substrate is the oracle)
Don't assert a predicted value. **Trigger the real pipeline through the built AIOS and OBSERVE a real
gap/cap number land in the workspace/output.** GREEN when:
- the `nutrition` AIOS exists (CLAUDE.md + tree + coords + `compile-day` SC in the tree, validated);
- walking `compile-day` on a real day+profile (the dietc Python tools doing the math) produces a real
  `DayState`/gap-cap result you can read (e.g. a known fixture → a known gap vector);
- the safety check actually runs (observe it flag a capped nutrient).
Freeze it as a `metaformal-self-test` anecdote leaf ("ONE TIME I compiled a day through the nutrition
AIOS… AND THEN I observed gaps={…}"), + a `test_nutrition_aios.py` that observes the emitted AIOS + one
real computation. **Then** dietc is the reference "domain built by chaincompiler."

## 5. What this proves (the recursion)
Finishing this reveals the **AIOS template** for any domain-compiler built on the stack (tools in Python,
cognition in skills, pipeline as a flow, gated + coord-addressed + self-expanding) — which is the thing
chaincompiler then applies to *itself*. dietc is the first real instance; the template is the deliverable.
