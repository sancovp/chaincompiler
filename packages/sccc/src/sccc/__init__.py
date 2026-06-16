"""SCCC — Skillchain Compiler-Compiler. The highest composite: AC + CoR + skills.

Same *CC shape (catch → lint → compile → package as SKILL.md). Built on the
`skillchain` module. ACCC → CORCC → SCCC.
"""
from __future__ import annotations

__version__ = "0.1.0"

from .forge import SCLanguage, StepRef, forge, lint, package, parse_sequence, resolve_steps

__all__ = [
    "forge", "lint", "package", "parse_sequence", "resolve_steps",
    "SCLanguage", "StepRef", "__version__",
]
