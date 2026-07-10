---
name: skill2framework
description: Turn an already-built AIOS/package into a framework chapter — narrative blog + deep-dive blog → chapter → {aios}-volume index skill → plugin → folded into the author's SkillTome.
---

# skill2framework — compiled skillchain

> Compiled by `skillchain.py` on 2026-07-10. Orchestrates 10 step(s) composing 6 skill(s).
> **Dependencies (validated present at compile time):** `assemble-chapter`, `deepdive-blog`, `fold-into-tome`, `framework-skill`, `narrative-blog`, `package-plugin`

**Execute the steps below in order.** Carry each step's result forward; where a step references `{var}`, substitute the captured value from the named earlier step.

## Step 1 — invoke skill `narrative-blog`
*WHAT: produce Blog 1 of a framework CHAPTER — the narrative chapter-opener — for an already-built AIOS/package by reconstructing its journey from its own dir (CLAUDE.md, README, dev log) and FILLING framework.JourneyCore, then rendering with render_blog1 (never hand-write the blog). WHEN: when making a framework/chapter from something already built, when you need the story post that opens a chapter, or when the user says blog organ / narrative blog / skill2framework (any of).*

Invoke the **narrative-blog** skill with input: the AIOS name + root; journey source = its CLAUDE.md/README/dev-log; the plugin URL; write blog1.md

→ Capture its result as `blog1`.

## Step 2 — reasoning bridge (CoR / AttentionChain)
Reason explicitly, step by step:

> Blog 1 (the story) exists at {blog1}. The other half of the chapter is the mechanics. Gather the package's impl docs (README architecture sections, design docs, module docstrings) — Blog 2 explains only what they say IS.

State the conclusion, then carry it forward as the input to the next step.

## Step 3 — invoke skill `deepdive-blog`
*WHAT: produce Blog 2 of a framework CHAPTER — the mechanical deep-dive ('how it actually works') — for an already-built AIOS/package by reading its impl docs (README architecture sections, design docs, the code's module docstrings) and assembling a faithful mechanics-only article that links back to Blog 1. WHEN: when producing the deep-dive half of a chapter, when you need the technical how-it-works post Blog 1 links to, or when the user says blog 2 / deep dive / skill2framework (any of).*

Invoke the **deepdive-blog** skill with input: the impl docs; back-link to {blog1}; write blog2.md

→ Capture its result as `blog2`.

## Step 4 — reasoning bridge (CoR / AttentionChain)
Reason explicitly, step by step:

> Both posts exist ({blog1}, {blog2}). They become ONE publishable unit — the chapter — via the deterministic op (framework.assemble_chapter). Decide the skill links to wire (the framework's decomposed skills) and a two-line abstract before running it.

State the conclusion, then carry it forward as the input to the next step.

## Step 5 — invoke skill `assemble-chapter`
*WHAT: assemble a framework CHAPTER from the two rendered blog posts — run framework.assemble_chapter to copy Blog 1 + Blog 2 verbatim into a self-contained chapter dir, wire the relative cross-links + plugin/skill links + CTAs, and write the chapter.md manifest. WHEN: when Blog 1 + Blog 2 exist and need combining into the publishable chapter unit, or when the user says assemble a chapter / skill2framework (any of).*

Invoke the **assemble-chapter** skill with input: blog1={blog1} blog2={blog2}; the chapter dir; plugin URL + skill links + abstract

→ Capture its result as `chapter`.

## Step 6 — reasoning bridge (CoR / AttentionChain)
Reason explicitly, step by step:

> The chapter tells the story and the mechanics; now the AIOS needs its front door. The {aios}-volume skill indexes the AIOS's skills + rules, gives the decision tree, and routes into the AIOS dir — it will link {chapter} and the plugin.

State the conclusion, then carry it forward as the input to the next step.

## Step 7 — invoke skill `framework-skill`
*WHAT: generate the FRAMEWORK SKILL for an already-built AIOS — the {aios}-volume (its SkillVolume face): one skill that indexes the AIOS's skills + rules + how they relate (as a diagram), gives a decision tree for what to do when, and ROUTES the agent into the AIOS dir. WHEN: when producing the index/router face of a framework package, or when the user says framework skill / volume / skill2framework (any of).*

Invoke the **framework-skill** skill with input: the AIOS skills/rules dirs + system doc; chapter={chapter}; write the {aios}-volume SKILL.md

→ Capture its result as `volume_skill`.

## Step 8 — invoke skill `package-plugin`
*WHAT: package a framework as a Claude Code PLUGIN (its operational face) — run framework.package_plugin to assemble plugin.json + skills/{aios}-volume/SKILL.md + the chapter bundled under resources/, with the skill's chapter links repathed to the bundle. WHEN: when a framework skill + chapter exist and need the installable plugin, or when the user says package the framework / plugin / skill2framework (any of).*

Invoke the **package-plugin** skill with input: framework skill={volume_skill}; chapter={chapter}; assemble the plugin dir (framework.package_plugin)

→ Capture its result as `plugin`.

## Step 9 — reasoning bridge (CoR / AttentionChain)
Reason explicitly, step by step:

> The framework package is complete: chapter + volume skill + plugin ({plugin}). The terminal move registers it in the author's SkillTome so it is findable and routable — a code op, idempotent, one row per framework.

State the conclusion, then carry it forward as the input to the next step.

## Step 10 — invoke skill `fold-into-tome`
*WHAT: the TERMINAL stage — fold a finished framework into the author's SkillTome (the top-level holder + search of all their frameworks) by running framework.fold_into_tome, which registers the framework as a row on a tome volume node's generated ## Frameworks table via skilltree's bind op. WHEN: when a framework package is finished and must be registered in the author's tome/volume, or when the user says fold into the tome / nomicon / skill2framework fold (any of).*

Invoke the **fold-into-tome** skill with input: framework skill dir from {volume_skill}; the tome root + volume node; run framework.fold_into_tome, then skilltree validate the tome

## Done
Return the final step's output as the result of this chain.
