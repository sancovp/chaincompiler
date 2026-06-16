"""ACCC — Attention-Chain Compiler-Compiler. The atom of the cognition stack.

ACCC → CORCC → SCCC: a CoR step embeds a forged AC; a skill embeds a CoR.
"""
from __future__ import annotations

__version__ = "0.1.0"

from .forge import Language, forge, gate, grammar, package, prime
from .render import attention_block, parse_ac

__all__ = [
    "forge", "gate", "grammar", "prime", "package", "Language",
    "attention_block", "parse_ac", "__version__",
]
