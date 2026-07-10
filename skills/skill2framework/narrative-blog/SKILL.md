---
name: narrative-blog
description: "WHAT: produce Blog 1 of a framework CHAPTER — the narrative chapter-opener — for an already-built AIOS/package by reconstructing its journey from its own dir (CLAUDE.md, README, dev log) and FILLING framework.JourneyCore, then rendering with render_blog1 (never hand-write the blog). WHEN: when making a framework/chapter from something already built, when you need the story post that opens a chapter, or when the user says blog organ / narrative blog / skill2framework (any of)."
---

# narrative-blog — Blog 1, the narrative opener (stage 1 of skill2framework)

> Ported 2026-07-10 from the proven doc-mirror `narrative-blog-from-aios` prompt-skill
> (score 1.00, FULL_E2E 2026-06-03). DIY adaptation: the journey source is the AIOS's
> OWN dir (CLAUDE.md + README + any dev log), and the renderer is `framework.journey`
> (no external renderer dependency). This port has not itself been E2E-scored yet.

Your ONE job: turn the AIOS's real journey into **Blog 1** by FILLING the
`JourneyCore` model and letting `render_blog1` produce the markdown. You do NOT
hand-write the blog — fill the model, run the renderer (deterministic output).

## Inputs (given at dispatch)
- AIOS/package name + root dir
- Journey source: the dir's `CLAUDE.md`, `README.md`, changelog/dev-log — read them FULLY
- Plugin / code URL
- Output path for the rendered markdown

## Step 1 — reconstruct the journey (grounded, never invented)
From the journey source, extract the Hero arc AS ACTUALLY LIVED:
`status_quo` (the painful before) · `obstacle` (the blocker + the moment seen) ·
`overcome` (the shift + what was built) · `accomplishment` (the after, feeling + proof) ·
`the_boon` (the ONE transferable reframe) · `demo_description` · `why_this_matters` ·
`universal_application` · `hook` (AUTHORED — one clean opening sentence you write).

**IS vs VISION discipline:** narrate only what the source supports. Do not invent
capabilities or results. Mark each field GROUNDED (cite where) vs INFERRED in your report.

## Step 2 — fill + render (the whole mechanism)
```python
from framework import JourneyCore, render_blog1
core = JourneyCore(journey_name="...", domain="...", hook="...",
                   status_quo="...", obstacle="...", overcome="...",
                   accomplishment="...", the_boon="...", demo_description="...",
                   why_this_matters="...", universal_application="...",
                   github_url="...", plugin_url="...")
open(OUTPUT, "w").write(render_blog1(core))
```
If the import fails, REPORT THE EXACT ERROR — never hand-write the blog as a workaround.

## Step 3 — report
The path written + the full markdown + the per-field GROUNDED/INFERRED check.
