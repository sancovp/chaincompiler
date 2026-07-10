---
name: package-plugin
description: "WHAT: package a framework as a Claude Code PLUGIN (its operational face) — run framework.package_plugin to assemble plugin.json + skills/{aios}-volume/SKILL.md + the chapter bundled under resources/, with the skill's chapter links repathed to the bundle. WHEN: when a framework skill + chapter exist and need the installable plugin, or when the user says package the framework / plugin / skill2framework (any of)."
---

# package-plugin — the installable face (stage 5 of skill2framework)

> Ported 2026-07-10 from the proven doc-mirror `package-framework-plugin` prompt-skill
> (score 1.00, FULL_E2E 2026-06-03). DIY adaptation: the mechanical work is the
> DETERMINISTIC op `framework.package_plugin`. Not itself E2E-scored yet.

A framework package is ALWAYS a plugin. The op builds the skeleton, bundles the
chapter, and repaths ONLY the chapter links in the copied skill (never the prose).

## Do
```python
from framework import package_plugin
rep = package_plugin(FRAMEWORK_SKILL_MD, CHAPTER_DIR, out_dir=PLUGIN_DIR,
                     name=f"{AIOS}-volume", author=USER, description=WHAT_ONE_LINE)
assert rep["ok"], rep          # rep["dead_refs"] must be []
```

## Verify (report this)
- `plugin.json` is valid JSON (name/version/author correct).
- The chapter is bundled under `skills/<name>/resources/chapter/`.
- Every repathed `./resources/chapter/*.md` reference RESOLVES (`dead_refs == []`).
- The skill body is otherwise unchanged.
