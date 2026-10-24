"""Regressions for the defects the public repository's two bug sweeps found in honeyc (its pull requests #1 and #2).

Each test fails on the code before its fix and passes after it.
"""
from __future__ import annotations

import shutil
import subprocess

import pytest
from click.testing import CliRunner

from honeyc.check import check_program
from honeyc.cli import main as honeyc_cli
from honeyc.emit_cypher import emit_cypher
from honeyc.emit_prolog import emit_prolog
from honeyc.normalize import normalize
from honeyc.parser import parse_text
from honeyc.render import render

_MARKERS = {"entity", "symbol", "glyph"}


def triples(text: str) -> set[tuple[str, str, str]]:
    return {(s.subject, s.predicate, s.object) for s in normalize(parse_text(text)) if s.predicate not in _MARKERS}


# ── the readable lens writes back the relation spelling it read, and what it writes parses to the same triples ──
@pytest.mark.parametrize("source, spelling", [
    ("[A] -owns-> [B]", "-owns->"),
    ("[A] <owns- [B]", "<owns-"),
    ("[A] <owns> [B]", "<owns>"),
])
def test_the_readable_lens_writes_back_the_relation_it_read(source, spelling):
    out = render(parse_text(source), "readable")
    assert spelling in out
    assert triples(out) == triples(source)


# ── a relation the user names `mediates` reaches every door that reads an inferred mediator's target ─────────
def test_a_relation_named_mediates_passes_every_door(tmp_path):
    program = parse_text("[A] -mediates-> [B]")
    statements = normalize(program)
    assert ("A", "mediates", "B") in triples("[A] -mediates-> [B]")
    assert "A mediates B" in render(program, "triples")
    render(program, "prose")
    assert "mediates(a, b)." in emit_prolog(statements)
    assert "-[:MEDIATES]->" in emit_cypher(statements)
    rune = tmp_path / "m.rune"
    rune.write_text("[A] -mediates-> [B]\n", encoding="utf-8")
    result = CliRunner().invoke(honeyc_cli, ["norm", str(rune)])
    assert result.exit_code == 0, result.output
    assert "A mediates B" in result.output


def test_an_inferred_mediator_keeps_its_target_at_every_door(tmp_path):
    program = parse_text("[A] ⇔ |🍯| ⇔ [B]")
    statements = normalize(program)
    assert "🍯 mediates A target=B" in render(program, "triples")
    assert "mediates(honey, a, b)." in emit_prolog(statements)
    assert "MEDIATES_TARGET" in emit_cypher(statements)
    rune = tmp_path / "b.rune"
    rune.write_text("[A] ⇔ |🍯| ⇔ [B]\n", encoding="utf-8")
    assert "🍯 mediates A target=B" in CliRunner().invoke(honeyc_cli, ["norm", str(rune)]).output


# ── check descends into an assignment and a transform ────────────────────────────────────────────────────────
def test_check_descends_into_an_assignment():
    messages = {i.message for i in check_program(parse_text("[A] := [B]"))}
    assert {"entity [A] has no type annotation.", "entity [B] has no type annotation."} <= messages


def test_check_descends_into_a_transform():
    issues = check_program(parse_text("${[A] ⇔ 🍯 ⇔ [B]}"))
    assert any("not bounded" in i.message for i in issues if i.severity == "warning")


# ── the generated Prolog closure terminates and is complete ──────────────────────────────────────────────────
def test_the_prolog_closure_carries_a_visited_list():
    out = emit_prolog(normalize(parse_text("[A] ⇔ [B] ⇔ [C]")))
    assert "memberchk" in out
    assert "X \\= B" not in out


@pytest.mark.skipif(shutil.which("swipl") is None, reason="runs the generated program in SWI-Prolog")
def test_the_prolog_closure_terminates_and_enumerates(tmp_path):
    program = tmp_path / "p.pl"
    program.write_text(emit_prolog(normalize(parse_text("[A] ⇔ [B] ⇔ [C]"))), encoding="utf-8")

    def ask(goal: str) -> str:
        return subprocess.run(["swipl", "-q", "-g", goal, "-t", "halt", str(program)],
                              capture_output=True, text=True, timeout=10).stdout.strip()

    assert ask("(linked(a, zz) -> writeln(yes) ; writeln(no))") == "no"
    assert ask("findall(Z, linked(a, Z), L), sort(L, S), writeln(S)") == "[a,b,c]"


# ── the base rules' predicates are declared, so a query fails cleanly on a program that has none of their facts ──
def test_the_prolog_program_declares_the_base_rules_predicates():
    first = emit_prolog(normalize(parse_text("[A] ⇒ [B]"))).splitlines()[0]
    assert first == ":- dynamic equiv/2, mediates/3, bounded/1, placeholder/2."


@pytest.mark.skipif(shutil.which("swipl") is None, reason="runs the generated program in SWI-Prolog")
def test_a_false_query_fails_on_a_program_with_no_equivalence(tmp_path):
    program = tmp_path / "p.pl"
    program.write_text(emit_prolog(normalize(parse_text("[A] ⇒ [B]"))), encoding="utf-8")
    run = subprocess.run(["swipl", "-q", "-g", "(linked(a, zz) -> writeln(yes) ; writeln(no))", "-t", "halt",
                          str(program)], capture_output=True, text=True, timeout=10)
    assert (run.stdout.strip(), "Unknown procedure" in run.stderr) == ("no", False)


# ── a transform's id names its chain, never the spelling of a relation in it ──────────────────────────────────
def test_a_transform_s_id_does_not_depend_on_a_relation_s_spelling():
    def xf(text: str) -> list[str]:
        return [s.subject for s in normalize(parse_text(text)) if s.predicate == "transform"]
    assert xf("${[A] ⇒ [B]}") == ["xf_617195b3"]                       # the id it had before the spelling was kept
    assert xf("${[A] -owns-> [B]}") == xf("${[A] <owns- [B]}") == ["xf_35a5eceb"]
