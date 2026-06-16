"""chaincompiler — the ChainCompiler. One roof over the cognition-chain stack.

ENGINE (this package): rulecatcher (learn grammar + gate) ⇄ HoneyC (compile) →
prime → SKILL.md packager. The layers ACCC / CORCC / SCCC build on this engine.

TOP DOOR: `construct_language(domain, ...)` mints a domain's AC + CoR + SC in one
call. It lives in `chaincompiler.construct` and is exposed lazily here (importing
the engine must not trigger the layers, which import the engine back).
"""
from __future__ import annotations

__version__ = "0.1.0"

from .bridge import compile_chain, gate, learn
from .prime import build_prime
from .skillpack import skill_markdown, slugify, write_skill

__all__ = [
    "learn", "gate", "compile_chain", "build_prime",
    "write_skill", "skill_markdown", "slugify",
    "construct_language", "LanguageBundle", "__version__",
]


def __getattr__(name: str):
    # Lazy top-door access: `chaincompiler.construct_language` without an import
    # cycle (construct imports accc/corcc/sccc, which import this engine).
    if name in ("construct_language", "LanguageBundle"):
        from . import construct as _c
        return getattr(_c, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
