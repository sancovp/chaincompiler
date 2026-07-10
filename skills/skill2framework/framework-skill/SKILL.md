---
name: framework-skill
description: "WHAT: generate the FRAMEWORK SKILL for an already-built AIOS — the {aios}-volume (its SkillVolume face): one skill that indexes the AIOS's skills + rules + how they relate (as a diagram), gives a decision tree for what to do when, and ROUTES the agent into the AIOS dir. WHEN: when producing the index/router face of a framework package, or when the user says framework skill / volume / skill2framework (any of)."
---

# framework-skill — the {aios}-volume index/router (stage 4 of skill2framework)

> Ported 2026-07-10 from the proven doc-mirror `generate-framework-skill` prompt-skill
> (score 1.00, FULL_E2E 2026-06-03). Vocabulary update: the generated skill is named
> **`{aios}-volume`** (a SkillVolume — the per-AIOS pattern book; "{aios}-nomicon" is
> the legacy name). Not itself E2E-scored yet.

The framework skill is an INDEX + DECISION-TREE ROUTER that sits on top of an AIOS:
it shows the tree of skills + rules + how they relate (a diagram), tells the agent
what to do when, and routes into the AIOS dir. It links the chapter + the plugin.

## Steps
1. **Index the AIOS**: read every skill (name + WHAT/WHEN), the rules, the system
   doc; build the skill tree + the rules table + the relationship DIAGRAM
   (reproduce/distill the AIOS's own diagram; ASCII or mermaid).
2. **Write the decision tree**: situation → the skill to use; copy-pasteable, not prose.
3. **Write `SKILL.md`** (frontmatter `name: {aios}-volume`; keyword-dense WHAT/WHEN):
   what-this-framework-is ¶ (point at the chapter + plugin) → the index + diagram →
   the decision tree → ROUTING (explicit paths into the AIOS's skills/rules) → links.
4. **Report**: confirm EVERY skill found is indexed (list them), a diagram exists,
   a decision tree exists, routing paths are real.

## Hard constraints
Index + router only — point at the AIOS's skills (canonical reference), never
duplicate their content. Ground everything in the actual files; invent nothing.
