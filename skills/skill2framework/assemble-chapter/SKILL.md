---
name: assemble-chapter
description: "WHAT: assemble a framework CHAPTER from the two rendered blog posts — run framework.assemble_chapter to copy Blog 1 + Blog 2 verbatim into a self-contained chapter dir, wire the relative cross-links + plugin/skill links + CTAs, and write the chapter.md manifest. WHEN: when Blog 1 + Blog 2 exist and need combining into the publishable chapter unit, or when the user says assemble a chapter / skill2framework (any of)."
---

# assemble-chapter — blogs → the chapter unit (stage 3 of skill2framework)

> Ported 2026-07-10 from the proven doc-mirror `assemble-chapter` prompt-skill
> (score 1.00, FULL_E2E 2026-06-03). DIY adaptation: the mechanical work is now the
> DETERMINISTIC op `framework.assemble_chapter` — the agent supplies the inputs and
> verifies the result, it does not hand-wire links. Not itself E2E-scored yet.

A chapter = Blog 1 + Blog 2, wired with cross-links and CTAs, plus a manifest.
The blogs' prose is NEVER rewritten — the op only appends the link/CTA block.

## Do
```python
from framework import assemble_chapter
rep = assemble_chapter(BLOG1, BLOG2, chapter_dir=CHAPTER_DIR,
                       framework_name=NAME, plugin_url=PLUGIN_URL,
                       skill_links=["Name|url", ...], abstract="<2 lines>")
assert rep["ok"], rep
```

## Verify (report this)
- `blog1.md`/`blog2.md` prose bodies unchanged (diff = pure additions).
- Cross-links are RELATIVE (`./blog1.md` ↔ `./blog2.md`) and resolve.
- Plugin + skill links present; `chapter.md` manifest lists both posts in order.
