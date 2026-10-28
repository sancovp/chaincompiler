"""Render a CoR persona into the paragraph the model must say.

§5 convergence: the fill-in skeleton format lives in the base (`cor_skeleton`); this module renders CORCC's
PersonaSpec THROUGH that single source (routed via CC, which re-exports it) instead of re-implementing it.
"""
from __future__ import annotations

from chaincompiler import cor_skeleton   # made FROM CC (CC re-exports APE's cor_skeleton)

from .notation import PersonaSpec


def must_say_directive(spec: PersonaSpec) -> str:
    moves = ", ".join(m.name for m in spec.moves[:-1])
    return (f"State your reasoning as ONE paragraph that performs, in order, {len(spec.moves)} moves: "
            f"{moves}, and finally converges on {spec.held.name}.")


def cor_template(spec: PersonaSpec) -> str:
    """A fill-in paragraph skeleton with one clause per move and its cue — rendered via the base's
    `cor_skeleton` (single source of the format). Each Move contributes its first cue phrase; a move that carries
    none (a persona recovered without its cues) is cued by its own name, `cor_skeleton`'s default."""
    moves = [m.name for m in spec.moves]
    cues = {m.name: m.cues[0] for m in spec.moves if m.cues}
    return cor_skeleton(moves, cues)
