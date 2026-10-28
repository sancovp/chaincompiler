"""Regressions in what a CoR's package writes: the directive it carries says what the paragraph does (the public
repository's bug sweeps, pull requests #1 and #2), and a move with no cue phrase is cued by its name (personapack's
recovered personas).

Each fails on the code before its fix and passes after it.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from corcc import forge_persona, package, prime
from corcc.notation import BANDIT, Move, PersonaSpec
from corcc.paragraph import cor_template, must_say_directive

DIRECTIVE = "State your reasoning as ONE paragraph that performs, in order, 5 moves: "


def test_the_directive_has_its_verb():
    assert must_say_directive(BANDIT).startswith(DIRECTIVE)


def test_a_move_with_no_cue_is_cued_by_its_name(tmp_path: Path):
    # a persona recovered without its cue phrases (personapack's SamayaReviewer) packages, its skeleton naming each
    # cue-less move by the move's own name — the base's `cor_skeleton` default
    spec = PersonaSpec(name="Reviewer", moves=(Move("Enumerate", ()), Move("Trace", ("follow the call",)),
                                                Move("Validate", ())))
    assert cor_template(spec) == "[Enumerate: …Enumerate…] → [Trace: …follow the call…] → [Validate: …Validate…]"
    skill = Path(package(forge_persona(spec, db=str(tmp_path / "rules.db")), out_dir=str(tmp_path / "skills")))
    assert "[Enumerate: …Enumerate…]" in skill.read_text(encoding="utf-8")


def test_a_move_whose_cues_is_a_bare_string_is_refused():
    # `("one phrase")` without its comma is a string, and its first letter would be the move's cue
    with pytest.raises(TypeError, match="not a tuple of cue phrases"):
        Move("Execute", ("produce the action, now sealed"))
    assert Move("Execute", ["produce the action"]).cues == ("produce the action",)


def test_every_door_that_writes_the_directive_writes_it_whole(tmp_path: Path):
    persona = forge_persona(BANDIT, db=str(tmp_path / "rules.db"))
    skill = Path(package(persona, out_dir=str(tmp_path / "skills")))
    assert DIRECTIVE in skill.read_text(encoding="utf-8")
    assert DIRECTIVE in prime(persona)
