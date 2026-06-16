"""CORCC — Chain-of-Reasoning Compiler-Compiler.

A CoR IS A spoken, paragraphical AC that makes a decision. CORCC is a SYNTAX
compiler: catch grammar → lint (keep the model writing valid CoR) → compile to a
markdown file → package as <name>/SKILL.md. Composes ACCC (inner attention
template). ACCC → CORCC → SCCC.
"""
from __future__ import annotations

__version__ = "0.1.0"

from .forge import (
    Persona,
    cor_chain,
    forge_persona,
    inner_template,
    lint,
    outer_template,
    package,
    prime,
)
from .notation import Move, PersonaSpec

__all__ = [
    "forge_persona", "Persona", "inner_template", "outer_template",
    "lint", "package", "prime", "cor_chain",
    "Move", "PersonaSpec", "__version__",
]
