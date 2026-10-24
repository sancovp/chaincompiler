"""The directive a CoR carries says what the paragraph does (the public repository's bug sweeps, pull requests #1 and #2).

It fails on the code before the fix and passes after it.
"""
from __future__ import annotations

from pathlib import Path

from corcc import forge_persona, package, prime
from corcc.notation import BANDIT
from corcc.paragraph import must_say_directive

DIRECTIVE = "State your reasoning as ONE paragraph that performs, in order, 5 moves: "


def test_the_directive_has_its_verb():
    assert must_say_directive(BANDIT).startswith(DIRECTIVE)


def test_every_door_that_writes_the_directive_writes_it_whole(tmp_path: Path):
    persona = forge_persona(BANDIT, db=str(tmp_path / "rules.db"))
    skill = Path(package(persona, out_dir=str(tmp_path / "skills")))
    assert DIRECTIVE in skill.read_text(encoding="utf-8")
    assert DIRECTIVE in prime(persona)
