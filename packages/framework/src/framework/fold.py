"""fold.py — the terminal stage: fold a framework into the author's SkillTome.

Delegates to skilltree's Move-1 bind op (`skilltree.tome.fold`, agent-skilltree
>= 0.3.0): the tome is a SkillTree whose volume nodes carry `frameworks` rows in
the manifest, rendered as the generated `## Frameworks` table. Folding is a CODE
op — idempotent, one row per framework, the manifest is the source of truth —
not an LLM hand-editing a table. ("nomicon" is the legacy alias for the
SkillVolume/SkillTome this folds into.)
"""
from __future__ import annotations

from pathlib import Path

from skilltree.tome import fold as _tome_fold


def fold_into_tome(framework_skill_dir: str | Path, *, volume: str,
                   tome_root: str | Path, what_for: str | None = None,
                   name: str | None = None, relative: bool = True) -> dict:
    """Register a framework's skill dir as a row on a tome volume node.

    framework_skill_dir  the framework skill dir (holds SKILL.md — the {aios}-volume)
    volume               the volume node in the tome tree (name or coord)
    tome_root            the materialized tome SkillTree root (holds skilltree.json)
    relative             default True: rows are stored holder-relative so a
                         repo-committed tome validates/projects from any checkout
    """
    return _tome_fold(framework_skill_dir, into=volume, tree_root=tome_root,
                      what_for=what_for, name=name, relative=relative)
