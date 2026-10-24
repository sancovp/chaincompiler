"""PersonaCC — Persona Compiler-Compiler. The syntax compiler for a PERSONA.

THE RATIFIED DEFINITION: a persona = a set of DESCRIPTION BLOCKS + a set of ACs +
at least one CoR that USES them. PersonaCC compiles that bundle: catch the
notation → lint (form + "uses them") → compile to a markdown body → package as
`<name>/SKILL.md` → SEAT into `chainaios.make_gba(persona=…)`. Composes ACCC (the
attention chains) + CORCC (the chains of reasoning). ACCC → CORCC → PersonaCC.
"""
from __future__ import annotations

__version__ = "0.1.1"

from .notation import Block, PersonaBundle
from .forge import (
    ForgedBundle,
    LANG_GATES,
    forge_bundle,
    lint,
    lint_blocks,
    package,
    register_lang_gate,
    render_blocks,
    role_block,
    seat,
    uses_them,
)

__all__ = [
    "Block", "PersonaBundle", "ForgedBundle",
    "forge_bundle", "lint", "lint_blocks", "uses_them", "package", "seat",
    "render_blocks", "role_block", "register_lang_gate", "LANG_GATES", "__version__",
]
