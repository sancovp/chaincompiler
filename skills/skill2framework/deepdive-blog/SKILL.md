---
name: deepdive-blog
description: "WHAT: produce Blog 2 of a framework CHAPTER — the mechanical deep-dive ('how it actually works') — for an already-built AIOS/package by reading its impl docs (README architecture sections, design docs, the code's module docstrings) and assembling a faithful mechanics-only article that links back to Blog 1. WHEN: when producing the deep-dive half of a chapter, when you need the technical how-it-works post Blog 1 links to, or when the user says blog 2 / deep dive / skill2framework (any of)."
---

# deepdive-blog — Blog 2, the mechanical deep dive (stage 2 of skill2framework)

> Ported 2026-07-10 from the proven doc-mirror `deepdive-blog-from-impl-docs`
> prompt-skill (score 1.00, FULL_E2E 2026-06-03). DIY adaptation: the impl docs are
> the package's OWN docs (README architecture sections, design docs, module
> docstrings/diagrams). This port has not itself been E2E-scored yet.

Blog 1 is the narrative; Blog 2 is the mechanics. You explain ONLY what the impl
docs say the system IS — not vision, not guesses.

## Inputs (given at dispatch)
- AIOS/package name + root; the impl docs to read FULLY
- Back-link to Blog 1; output path

## Structure (assemble, don't reverse-engineer)
- `# <name> — How It Works (Deep Dive)` + a link back to Blog 1
- `## The architecture` — layers/components (reproduce the docs' diagrams VERBATIM)
- `## How it runs` — the runtime cycle
- `## Where things live` — the file geometry
- `## The invariants` — the rules/gates the system holds itself to (if stated)
- Cite the specific doc each section came from.

## Hard constraints
Mechanics ONLY from the impl docs. Reproduce diagrams verbatim; fabricate none.
Report per-section GROUNDED/INFERRED; prose roughness is fine, fidelity is not optional.
