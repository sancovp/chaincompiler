"""Regression tests for the 2026-07 bug sweep — each test pins one fixed defect."""
from __future__ import annotations

from honeyc.check import check_program
from honeyc.emit_cypher import emit_cypher
from honeyc.emit_prolog import emit_prolog
from honeyc.normalize import normalize
from honeyc.parser import parse_text
from honeyc.render import render


# -- readable rel connectors must be valid, re-parseable notation ---------------
def test_readable_forward_rel_round_trips():
    out = render(parse_text("[A] -owns-> [B]"), "readable")
    assert "-owns->" in out
    reparsed = parse_text(out)          # must not raise
    assert normalize(reparsed) == normalize(parse_text("[A] -owns-> [B]"))


def test_readable_reverse_rel_round_trips():
    out = render(parse_text("[Mbr] <is_a-[Nectar]"), "readable")
    assert "<is_a-" in out
    reparsed = parse_text(out)          # must not raise
    assert ("Mbr", "is_a", "Nectar") in {
        (s.subject, s.predicate, s.object) for s in normalize(reparsed)
    }


# -- a user relation named `mediates` must not crash the emitters ---------------
def test_user_mediates_rel_does_not_crash_emitters():
    program = parse_text("[A] -mediates-> [B]")
    statements = normalize(program)
    assert ("A", "mediates", "B") in {(s.subject, s.predicate, s.object) for s in statements}
    render(program, "triples")          # KeyError: 'target' before the fix
    render(program, "prose")
    emit_prolog(statements)
    emit_cypher(statements)


# -- the generated Prolog closure must be guarded against the equiv symmetry ----
def test_prolog_linked_rule_has_cycle_guard():
    out = emit_prolog(normalize(parse_text("[A] ⇔ [B] ⇔ [C]")))
    assert "memberchk" in out           # visited-list closure, not bare recursion
    assert "X \\= B" not in out         # the old unbound-killing guard is gone


# -- check_program must descend into Assignment and Transform -------------------
def test_check_descends_into_assignment():
    issues = check_program(parse_text("[A] := [B]"))
    assert {i.message for i in issues} >= {
        "entity [A] has no type annotation.",
        "entity [B] has no type annotation.",
    }


def test_check_descends_into_transform():
    issues = check_program(parse_text("${[A] ⇔ 🍯 ⇔ [B]}"))
    assert any("not bounded" in i.message for i in issues if i.severity == "warning")
