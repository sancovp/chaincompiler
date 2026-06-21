"""archetype — the Archetype Compiler. An archetype is a state machine, not a noun.

    MetaArchetype(A) := ⟨ Persona(A), Shadow(A), Self(A), Odyssey(A), Becoming(A) ⟩

Compiles a seed + knobs into the full individuation circuit (generating the missing
aspects), builds the multi-HJ Odyssey, validates C1–C6, and emits through lenses —
including the ONE TYPE, a `<name>/SKILL.md`. The ChainCompiler thesis on the psyche:
compile the transformation law, don't list the archetypes. Spec: ARCHETYPE-COMPILER.md.
"""
from __future__ import annotations

__version__ = "0.1.0"

from .model import HJ, KNOBS, MetaArchetype, Seed
from .stdlib import CYBERNETIC_CITY, CYCLE, PANTHEON, next_in_cycle, seed_for
from .infer import infer, denied_inverse, integrate, type_lift
from .odyssey import generate_odyssey, aut_web, quines
from .validate import validate, is_valid
from .emit import readable, triples, prolog, cypher, to_json, emit, emit_skill
from .compile import compile_archetype, compile_chain, compile_world
from .parser import Stmt, parse

__all__ = [
    "MetaArchetype", "HJ", "Seed", "KNOBS",
    "CYCLE", "PANTHEON", "CYBERNETIC_CITY", "seed_for", "next_in_cycle",
    "infer", "denied_inverse", "integrate", "type_lift",
    "generate_odyssey", "aut_web", "quines",
    "validate", "is_valid",
    "readable", "triples", "prolog", "cypher", "to_json", "emit", "emit_skill",
    "compile_archetype", "compile_chain", "compile_world",
    "Stmt", "parse", "__version__",
]
