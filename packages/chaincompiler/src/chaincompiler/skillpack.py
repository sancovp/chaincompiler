"""chaincompiler.skillpack — the skill-packager, now living in the BASE.

MOVED DOWN to `prompt_engineering.skillpack` (REBUILD-SPEC.md §7 — single source of truth, D1). This
module now just re-exports it, so `from chaincompiler.skillpack import write_skill` and
`from chaincompiler import write_skill, slugify, skill_markdown` stay byte-stable for existing consumers
(archetype, the *CC tests).
"""
from __future__ import annotations

from prompt_engineering.skillpack import slugify, skill_markdown, write_skill

__all__ = ["slugify", "skill_markdown", "write_skill"]
