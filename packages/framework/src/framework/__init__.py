"""framework — the chapter rung of the ladder (skill2framework's deterministic glue).

A FRAMEWORK is a chapter: Blog 1 (narrative) + Blog 2 (deep dive) + a plugin +
the {aios}-volume index skill, folded into the author's SkillTome. The LLM
stages are the six `skills/skill2framework/*` prompt-skills; this package is
the deterministic machinery they run:

    journey.JourneyCore + render_blog1   — the Blog-1 model + renderer (fill, never hand-write)
    chapter.assemble_chapter             — blogs → self-contained chapter dir (links/CTAs/manifest)
    plugin.package_plugin                — framework skill + chapter → installable plugin dir
    fold.fold_into_tome                  — the terminal bind (delegates to skilltree.tome.fold)
"""
from .chapter import assemble_chapter
from .fold import fold_into_tome
from .journey import JourneyCore, render_blog1
from .plugin import package_plugin

__all__ = ["JourneyCore", "render_blog1", "assemble_chapter", "package_plugin",
           "fold_into_tome"]
