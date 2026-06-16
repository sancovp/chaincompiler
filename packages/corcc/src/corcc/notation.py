"""CoR personas: ordered reasoning MOVES with cue-markers.

A CoR (Chain of Reasoning) is the OUTER half of a persona. Unlike an attention
chain (inner, silent, a template for a section/thinking), a CoR is something the
model MUST SAY, as a paragraph. Because it is spoken, it is gauge-able: if the
emitted prose performs the required moves IN ORDER, the persona is intact; if it
skips or scrambles them, the persona has melted.

Each persona is an ordered tuple of Moves. Each Move carries cue-markers — the
surface phrases that count as evidence the move was performed. The LAST move is
the convergence (the held conclusion the paragraph must reach).
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Move:
    name: str
    cues: tuple[str, ...]


@dataclass(frozen=True)
class PersonaSpec:
    name: str
    moves: tuple[Move, ...]          # ordered; last move = the held convergence
    blurb: str = ""

    @property
    def held(self) -> Move:
        return self.moves[-1]


# The worked example: think like Einstein.
EINSTEIN = PersonaSpec(
    name="ThinkLikeEinstein",
    blurb="fix the invariant, run a thought experiment, strip to simplest form, reframe the question",
    moves=(
        Move("Invariants", ("invariant", "stays fixed", "regardless of frame",
                            "holds in every frame", "what cannot change")),
        Move("ThoughtExperiment", ("imagine", "suppose", "thought experiment",
                                   "ride alongside", "gedanken", "picture")),
        Move("Simplicity", ("simplest", "strip", "essence", "as simple as possible", "bare")),
        Move("Reframe", ("reframe", "the real question", "actually about",
                         "so the question becomes", "reframes")),
    ),
)

# A second persona, to show CORCC mints languages, not one hard-coded shape.
FEYNMAN = PersonaSpec(
    name="ThinkLikeFeynman",
    blurb="restate plainly, give a concrete example, find where it breaks, then explain simply",
    moves=(
        Move("Plainly", ("in plain terms", "put simply", "what this really says")),
        Move("ConcreteExample", ("for example", "concretely", "take a case", "imagine a")),
        Move("WhereItBreaks", ("breaks down", "fails when", "the catch", "where it goes wrong")),
        Move("ExplainSimply", ("so simply put", "the punchline", "bottom line", "in short")),
    ),
)

SEED_PERSONAS = {p.name: p for p in (EINSTEIN, FEYNMAN)}
