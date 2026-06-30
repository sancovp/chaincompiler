"""chaincompiler — the ChainCompiler BASE: the generic compiler-compiler (META-APE spec §3).

This package imports only DOWN (APE + honeyc + rulecatcher). It is the machine the *CC are MADE FROM:
  - forge   : the generic "forge a language" core (Language / forge / gate_language / grammar / package_skill)
  - bridge  : the HoneyC compile seam + the rulecatcher grammar seam (learn / gate, re-exported from APE)
  - prime   : build_prime — the re-injectable prime block
  - skillpack / persona : SKILL.md packaging + the glyph-persona-program compiler

ACCC / CORCC / SCCC build ON this base (they import CC). CC NEVER imports the *CC. The Bandit AIOS
application that orchestrates AC+CoR+SC (construct_language / GBA / HBA / COG) lives ABOVE the *CC in the
`chainaios` package — it was extracted out of here precisely so this base no longer imports the *CC.
"""
from __future__ import annotations

__version__ = "0.1.0"

from .bridge import compile_chain, gate, learn
from .prime import build_prime
from .skillpack import skill_markdown, slugify, write_skill
# the generic compiler-compiler core — the machine the *CC are MADE FROM (spec §3). Imports only APE.
from .forge import Language, forge, gate_language, grammar, package_skill
# re-export the APE cognition helper the *CC need, so they route through CC (not around it to APE):
from prompt_engineering import cor_skeleton

__all__ = [
    "learn", "gate", "compile_chain", "build_prime",
    "write_skill", "skill_markdown", "slugify",
    # the forge core (ACCC/CORCC/SCCC import these DOWN from here):
    "Language", "forge", "gate_language", "grammar", "package_skill", "cor_skeleton",
    "__version__",
]
