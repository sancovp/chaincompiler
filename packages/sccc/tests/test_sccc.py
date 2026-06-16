"""SCCC tests: forging the sequence grammar, lint, resolution, rollup packaging."""
from __future__ import annotations

from pathlib import Path

import accc
import corcc
from corcc.notation import EINSTEIN

from sccc import forge, lint, package, parse_sequence, resolve_steps
from sccc.notation import SEED_SEQUENCES

_STUB = "---\nname: summarize\ndescription: condense\n---\n\nSummarize it.\n"


def _setup(tmp_path: Path):
    db = str(tmp_path / "cc.db")
    skills = tmp_path / "skills"
    accc.forge("debug-attention", ["[Symptom] ⇒ [Repro] ⇒ |Localize|"], db=db)
    ac = accc.package("debug-attention", "[Symptom] ⇒ [Repro] ⇒ |Localize|", out_dir=str(skills))
    persona = corcc.forge_persona(EINSTEIN, db=db)
    cor = corcc.package(persona, out_dir=str(skills))
    (skills / "summarize").mkdir(parents=True, exist_ok=True)
    (skills / "summarize" / "SKILL.md").write_text(_STUB)
    seq = f"[ac:{ac.parent.name}] ⇒ [cor:{cor.parent.name}] ⇒ [skill:summarize] ⇒ |Answer|"
    return db, str(skills), seq


def test_parse_sequence_extracts_typed_steps():
    steps, held = parse_sequence("[ac:foo] ⇒ [cor:bar] ⇒ [skill:baz] ⇒ |Result|")
    assert [(s.kind, s.ref) for s in steps] == [("ac", "foo"), ("cor", "bar"), ("skill", "baz")]
    assert held == "Result"


def test_closure_a_skillchain_can_chain_another_skillchain(tmp_path: Path):
    """Everything is a skill dir, so an SC can reference an SC. The algebra closes."""
    db, skills, seq = _setup(tmp_path)
    # SC#1 compiled INTO the skills dir → it is itself an indexable skill dir.
    forge("inner", [seq], db=db)
    sc1 = package("inner", seq, out_dir=skills, skills_dir=skills)
    assert sc1.exists()
    # SC#2 references SC#1 as a plain skill (closure) + another skill.
    seq2 = f"[skill:{sc1.parent.name}] ⇒ [skill:summarize] ⇒ |Done|"
    _rows, missing = resolve_steps(seq2, skills_dir=skills)
    assert missing == []
    sc2 = package("outer", seq2, out_dir=skills, skills_dir=skills)
    assert sc1.parent.name in sc2.read_text()      # SC#2 rolls up SC#1


def test_forge_and_lint_sequence(tmp_path: Path):
    db, skills, seq = _setup(tmp_path)
    scl = forge("demo", SEED_SEQUENCES, db=db)
    assert scl.rule_count > 0
    assert lint(scl, seq)[0] == []                       # well-formed
    assert lint(scl, "[ac:foo] [skill:baz] ⇒ |R|")[0]    # malformed (dropped ⇒)


def test_resolve_steps_finds_forged_packages(tmp_path: Path):
    _db, skills, seq = _setup(tmp_path)
    rows, missing = resolve_steps(seq, skills_dir=skills)
    assert missing == []
    assert all(status == "ok" for _, _, _, status, _ in rows)


def test_package_rolls_up_into_one_skill(tmp_path: Path):
    _db, skills, seq = _setup(tmp_path)
    out = tmp_path / "dist"
    sc_path = package("debug-then-explain", seq, out_dir=str(out), skills_dir=skills)
    text = sc_path.read_text()
    assert sc_path.name == "SKILL.md"
    assert "debug-attention" in text          # AC step referenced
    assert "thinklikeeinstein" in text        # CoR step referenced
    assert "summarize" in text                # regular skill referenced


def test_package_refuses_when_step_missing(tmp_path: Path):
    db, skills, _seq = _setup(tmp_path)
    bad_seq = "[skill:does-not-exist] ⇒ |R|"
    try:
        package("broken", bad_seq, out_dir=str(tmp_path / "d"), skills_dir=skills)
        assert False, "should refuse to compile with a missing step"
    except ValueError:
        pass
