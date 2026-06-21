#!/usr/bin/env python3
"""
examples/nutrition — dietc, re-expressed as a chaincompiler-BUILT AIOS (the v1 recursion).

dietc was meant to be *the worked example made by the system*, but it shipped as 11 hand-coded
Python modules with 0 skills / 0 chains — the recursion (*chaincompiler makes dietc*) never ran.
This build runs it: the dietc **math/IO stays Python tools** (the chain CALLS them — arithmetic must
execute, never live in a prompt); its **"how to think" becomes AC skills** (gap/cap/safety attention);
its **patch decision becomes a CoR**; its **`compile_day` pipeline becomes a flow-skill** the agent walks.

The emitted `aios/` is the deliverable: the reference "a domain built by chaincompiler". The Python
tools live in `packages/honeyc/src/dietc/` (importable as `dietc`); this AIOS is their front end.

    make_gba("nutrition", aios/, atoms=[gap, cap, safety])   →  3 ACs + the NutritionBandit CoR + rollup SC + loop
    + the `nutrition-recommend` CoR flow  (the patch decision)
    + the `compile-day` SC flow           (the pipeline: load → state → gapcap → patch → safety → render)
    + a `90-safety.md` rule               (NOT medical advice; always run safety.check)

Run:  python3 examples/nutrition/build.py     (after ./install.sh)
"""
from __future__ import annotations

import json
from pathlib import Path

from chaincompiler.gba import make_gba, _apply_tree, _rule_blocks
from chaincompiler.skillpack import skill_markdown, slugify

HERE = Path(__file__).resolve().parent
AIOS = HERE / "aios"

# ── the role: who the agent IS here (the domain invariant) + the safety frame ──
ROLE = "\n".join([
    "# NutritionBandit",
    "",
    "You are the **NutritionBandit**, the base agent of this directory: the **ChainSelector for "
    "`nutrition`**. Given a day of intake + a goal profile you pick an arm — **select** a proven "
    "chain (exploit) or **construct** a new one (explore) — and walk it to read a day's gaps/caps "
    "and recommend patches.",
    "",
    "> **NOT medical advice.** The dietc Python tools own every number (gaps, caps, doses); a prompt "
    "never computes a nutrient value. You read what the tools return and reason about it. Always run "
    "the safety check before surfacing a recommendation (rule `90-safety`).",
    "",
    "Your loop, your law, your KB protocol, and your safety rule are in your appended rules "
    "(`.claude/rules/`); your chains and the `bandit-chain-system` how-to are your skills "
    "(`.claude/skills/`). Your default *domain* workflow is the **`compile-day`** flow-skill.",
])

# ── the safety rule (added to the GBA defaults; persists via the _profile) ─────
SAFETY_RULE = "\n".join([
    "# Rule: safety first (NOT medical advice)", "",
    "This AIOS is **not medical advice**. Before surfacing any recommendation:", "",
    "1. **ALWAYS run `dietc.safety.check(...)`** on the planned patches — never skip it.",
    "2. **Surface every cap breach and safety warning** the tools return; never suppress them.",
    "3. **The Python tools own the numbers** (gaps/caps/doses) — a prompt never computes a nutrient value.",
    "4. If unsure whether something is safe, **say so and defer** — do not invent a clearance.",
])

# ── the patch decision, spoken (a CoR flow) ───────────────────────────────────
RECOMMEND = "\n".join([
    "The **patch decision**, spoken — a CoR (ends in a decision). NOT medical advice.", "",
    "Given the computed `gaps`, `caps`, and `matrix_gaps` (from `dietc.gapcap.compute` — never "
    "recompute them here):", "",
    "1. **Weigh** the gaps (what's missing) against the caps (what's already at/over its upper limit).",
    "2. **Prefer** the module that fills the *most gap* without *breaching any cap*. The scorer is "
    "`dietc.patch._score`; the planner `dietc.patch.plan(gaps, caps, matrix_gaps, modules, profile)` "
    "does the selection — **call it, don't reimplement**.",
    "3. **Decide** — recommend the chosen module(s) at their dose, then HAND OFF to safety "
    "(`dietc.safety.check`) before surfacing. If a cap would breach, drop the module and say why.",
    "",
    "Decision out: a short, gated recommendation list + the safety warnings. The numbers come from "
    "the tools; the weighing and the justification are yours.",
])

# ── the pipeline, as a walkable flow-skill (a CoR/SC the agent walks) ──────────
COMPILE_DAY = "\n".join([
    "The **compile-day** pipeline for `nutrition` — your default *domain* workflow. It is a flow you "
    "WALK, calling the dietc Python tools at each step (the math is theirs; the *reading* is yours). "
    "NOT medical advice.", "",
    "1. **Load** — `dietc.load.load_profile(profile.yaml)`, `load.load_modules(patch_modules.yaml)`, "
    "`load.load_items(items.yaml)`, `load.load_day(day.yaml)`. (IO → typed models.)",
    "2. **Day state** — `dietc.engine.build_day_state(events, items, label)` → a `DayState` carrying "
    "`nutrient_totals` + `matrix_totals`. (Sum the day.)",
    "3. **Gaps & caps** — walk the **gap-attn** + **cap-attn** ACs, then call "
    "`dietc.gapcap.compute(state.nutrient_totals, state.matrix_totals, profile)` → "
    "`(gaps, caps, matrix_gaps, warnings)`. Read what it returns — never compute a gap in a prompt.",
    "4. **Patch** — walk the **nutrition-recommend** CoR, then call "
    "`dietc.patch.plan(gaps, caps, matrix_gaps, modules, profile)` → recommendations.",
    "5. **Safety** — walk the **safety-attn** AC, then call "
    "`dietc.safety.check(recs, modules, caps, profile)` → warnings. ALWAYS run this before recommending.",
    "6. **Render** — hand the `DayState` to honeyc's lens (`dietc.render` / `dietc.rune.render_via_honeyc`) "
    "for the human-facing summary.",
    "",
    "**Shortcut:** `dietc.engine.compile_day(day, profile, modules)` runs steps 1–5 in one call — it "
    "IS the Python pipeline these steps narrate. The flow exists so you know WHAT each step reads and "
    "WHY: the tools do the arithmetic; you read the gaps/caps and decide.",
])


def build(root: "Path | str" = AIOS) -> "object":
    """Emit the nutrition AIOS into `root` (default ./aios). Returns the GBA."""
    root = Path(root)
    # 1. scaffold: 3 AC atoms (bare labels, no colons) → gap/cap/safety attention,
    #    + the NutritionBandit CoR + the rollup SC + the loop flow-skill, coord-addressed.
    rules = {**_rule_blocks("nutrition", "nutrition"), "90-safety.md": SAFETY_RULE}
    g = make_gba(
        "nutrition", root,
        atoms=[
            "[Targets] ⇒ [Current] ⇒ |Gaps|",     # gap-attn
            "[Current] ⇒ [Limits] ⇒ |Caps|",      # cap-attn
            "[Item] ⇒ [Interactions] ⇒ |Safe|",   # safety-attn
        ],
        blurb=("in the nutrition domain: read a day's intake against a goal profile, compute its "
               "gaps and caps with the dietc tools, recommend patches that fill gaps without "
               "breaching caps, and always run the safety check (NOT medical advice)"),
        role_block=ROLE,
        rule_blocks=rules,
    )

    # 2. append the two flow-skills (same mechanism make_gba uses for the loop flow):
    #    write the body to the persisted src scratch, add a tree node, re-materialize + re-index.
    src = root.parent / f".{root.name}.src"
    tree_dict = json.loads(g.manifest.read_text())
    for name, kind, desc, body in [
        ("nutrition-recommend", "cor", "the patch decision, spoken — weigh gaps vs caps → decide", RECOMMEND),
        ("compile-day", "sc", "the nutrition pipeline: load → day-state → gapcap → patch → safety → render", COMPILE_DAY),
    ]:
        d = src / name
        d.mkdir(parents=True, exist_ok=True)
        (d / "SKILL.md").write_text(skill_markdown(name, desc, body))
        tree_dict["children"].append(
            {"name": slugify(name), "kind": kind, "description": desc, "skill_src": str(d)})
    viol, n = _apply_tree(g, tree_dict)
    g.report.update({"violations": viol, "indexed_skills": n})
    g.closed = g.closed and viol == 0
    return g


if __name__ == "__main__":
    g = build()
    print(f"nutrition AIOS → {g.root}")
    print(f"  closed: {g.closed}  violations: {g.report.get('violations')}  "
          f"indexed skills: {g.report.get('indexed_skills')}")
    print(f"  CLAUDE.md: {g.claude_md.exists()}  rules: {sorted(p.name for p in g.rules_dir.iterdir())}")
