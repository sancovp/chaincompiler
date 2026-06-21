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


# ── THE DEFAULT persona: the agent IS the bandit ────────────────────────────
# Einstein/Feynman below are *flavors* — each is a single proven chain, i.e. a
# ChainConstruct OUTPUT. The DEFAULT persona is the thing that sits ABOVE the
# flavors and decides whether to construct one at all: the ChainSelector. Given a
# task it picks an arm —
#     ChainSelect    (exploit): reuse a proven / "golden" chain
#     ChainConstruct (explore): assemble a NEW chain
# This is compoctopus's `router.py` Bandit (Link→Chain→Compiler→Bandit) rendered
# as a CoR: in ChainCompiler the LLM, shaped by the gate, IS the selector — so the
# bandit policy is a persona the model reads and performs, not a separate engine.
BANDIT = PersonaSpec(
    name="BanditChain",
    blurb="frame the task, recall a proven chain, choose exploit (select) vs explore (construct), execute it, record the reward",
    moves=(
        Move("Task", ("the task is", "what's being asked", "given the task",
                      "the goal here", "what I need to do")),
        Move("Recall", ("have I done this", "a proven chain", "golden chain",
                        "already have one", "seen this before", "in the registry")),
        Move("Decide", ("exploit", "reuse the existing", "explore", "no chain exists yet",
                        "reward is high enough", "construct a new", "select vs construct",
                        "so I'll select", "so I'll construct")),
        Move("Execute", ("run the chain", "execute it", "apply it", "run it on", "now I run")),
        Move("Reward", ("the result is", "which worked", "record the reward",
                        "update the golden", "so the outcome", "the answer is")),
    ),
)


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

# DEFAULT = the selector; the flavors are what it constructs.
DEFAULT = BANDIT
SEED_PERSONAS = {p.name: p for p in (BANDIT, EINSTEIN, FEYNMAN)}
