---
name: fold-into-tome
description: "WHAT: the TERMINAL stage — fold a finished framework into the author's SkillTome (the top-level holder + search of all their frameworks) by running framework.fold_into_tome, which registers the framework as a row on a tome volume node's generated ## Frameworks table via skilltree's bind op. WHEN: when a framework package is finished and must be registered in the author's tome/volume, or when the user says fold into the tome / nomicon / skill2framework fold (any of)."
---

# fold-into-tome — register the framework in the SkillTome (stage 6, terminal)

> Ported 2026-07-10 from the proven doc-mirror `fold-into-nomicon` prompt-skill
> (score 1.00, FULL_E2E 2026-06-03). THE BIG CHANGE: folding is now a CODE OP —
> `skilltree.tome.fold` (agent-skilltree ≥ 0.3.0) owns the `## Frameworks` table
> (generated from the tree manifest, idempotent, one row per framework) — an LLM no
> longer hand-edits the table. ("nomicon" = the legacy name for SkillVolume/SkillTome.)

The SkillTome is the framework-of-frameworks: a SkillTree whose volume nodes HOLD
frameworks as tome-table rows. An agent equips the tome to search "which of the
author's frameworks fits this task?" and route into it.

## Do
```python
from framework import fold_into_tome
rep = fold_into_tome(FRAMEWORK_SKILL_DIR, volume=VOLUME_NODE, tome_root=TOME_ROOT,
                     what_for=ONE_LINE_SUMMARY)      # relative=True by default (repo-portable)
assert rep["ok"], rep
```
If the tome tree does not exist yet, materialize it first (`skilltree` — a root
node + a volume branch), then fold.

## Verify (report this)
- The row is present EXACTLY ONCE (re-folding updates, never duplicates — check `rep["updated"]`/`rep["rows"]`).
- `skilltree validate <tome_root>` is green (the tome-table round-trip: manifest
  rows in the table, every target resolves).
- The round-trip in words: tome → (search the table) → the {aios}-volume skill →
  (routes into) → the AIOS. Confirm each hop resolves.
