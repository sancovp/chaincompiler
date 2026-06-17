"""steward — the Custodian genus (lowest rung), the non-graph realization.

A Custodian = a loop-runner gated by a warrant (CCC DESIGN.md §2.1). The **Steward** is
its headless/automation sibling (the Cybernet is the graph game-being sibling — built next,
in CCC). A Steward runs O/F/I/A/P and produces the one type (a skill-dir artifact); the
**A-stage is the LOCK** (warrant-freeze: admit/crystallize or reject).

Hierarchy (bottom-up): Steward → specialist Stewards (chain/sm/compiler/core) → MetaSteward
(a Steward that runs a sequence of Stewards — presents as one, runs many; homoiconic).
"""
from __future__ import annotations

__version__ = "0.1.0"

from .core import Artifact, Steward, StewardResult, Task, Verdict, Warrant, crystallize
from .specialists import (chain_steward, compiler_steward, core_steward, meta_steward,
                          sm_steward)
from .warrants import always, glyph_grammar, non_empty, shape

__all__ = [
    "Artifact", "Task", "Verdict", "Warrant", "Steward", "StewardResult", "crystallize",
    "chain_steward", "sm_steward", "compiler_steward", "core_steward", "meta_steward",
    "always", "shape", "non_empty", "glyph_grammar",
    "__version__",
]
