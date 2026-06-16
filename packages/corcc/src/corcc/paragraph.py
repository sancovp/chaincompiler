"""Render a CoR persona into the paragraph the model must say."""
from __future__ import annotations

from .notation import PersonaSpec


def must_say_directive(spec: PersonaSpec) -> str:
    moves = ", ".join(m.name for m in spec.moves[:-1])
    return (f"State your reasoning as ONE paragraph that, in order, {len(spec.moves)} moves: "
            f"{moves}, and finally converges on {spec.held.name}.")


def cor_template(spec: PersonaSpec) -> str:
    """A fill-in paragraph skeleton with one clause per move and its cue."""
    clauses = []
    for move in spec.moves[:-1]:
        clauses.append(f"[{move.name}: …{move.cues[0]}…]")
    held = spec.held
    clauses.append(f"[{held.name}: …{held.cues[0]}…]")
    return " → ".join(clauses)
