"""Render a CoR persona into the paragraph the model must say.

§5 convergence: the fill-in skeleton format lives in the base (`prompt_engineering.cognition.cor_skeleton`);
this module renders CORCC's PersonaSpec THROUGH that single source instead of re-implementing it.
"""
from __future__ import annotations

from prompt_engineering.cognition import cor_skeleton

from .notation import PersonaSpec


def must_say_directive(spec: PersonaSpec) -> str:
    moves = ", ".join(m.name for m in spec.moves[:-1])
    return (f"State your reasoning as ONE paragraph that, in order, {len(spec.moves)} moves: "
            f"{moves}, and finally converges on {spec.held.name}.")


def cor_template(spec: PersonaSpec) -> str:
    """A fill-in paragraph skeleton with one clause per move and its cue — rendered via the base's
    `cor_skeleton` (single source of the format). Each Move contributes its first cue phrase."""
    moves = [m.name for m in spec.moves]
    cues = {m.name: m.cues[0] for m in spec.moves}
    return cor_skeleton(moves, cues)
