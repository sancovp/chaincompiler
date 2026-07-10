from __future__ import annotations

MBR = '[Mbr]: M*Boundary <is_a-🌸\u200d💧 ⇔ |🍯| ⇔ [Mbl]: M*Blanket <is_a-🍹'

from honeyc.check import check_program
from honeyc.parser import parse_text
from honeyc.render import render


def test_render_triples_mbr():
    out = render(parse_text(MBR), "triples")
    assert "Mbr has_type M*Boundary" in out
    assert "Mbr is_a 🌸‍💧" in out
    assert "🍯 bounded true" in out
    assert "Mbr equiv 🍯" in out


def test_render_readable_mbr():
    out = render(parse_text(MBR), "readable")
    assert "[Mbr: M*Boundary]" in out
    assert "|🍯: Honey|" in out
    assert "⇔" in out


def test_render_prose_mbr():
    out = render(parse_text(MBR), "prose")
    assert "Mbr is an entity of type M*Boundary." in out
    assert "Nectar-level" in out


def test_render_readable_scope_with_chain_members():
    # a scope whose body contains chains must render the chains, not their repr
    src = "[Box]:{ [A] ⇒ [B], [C] ⇔ [D] }"
    out = render(parse_text(src), "readable")
    assert "Chain(" not in out
    assert "[A] ⇒ [B]" in out
    assert "[C] ⇔ [D]" in out


def test_check_warns_unbounded_mediator():
    # honey is the mediator but NOT bounded -> warning + rewrite suggestion
    issues = check_program(parse_text("[A] ⇔ 🍯 ⇔ [B]"))
    warns = [i for i in issues if i.severity == "warning"]
    assert warns
    assert any("not bounded" in w.message for w in warns)
    assert any(w.suggested_rewrite and "|🍯: Honey|" in w.suggested_rewrite for w in warns)


def test_check_clean_when_bounded():
    issues = check_program(parse_text("[A] ⇔ |🍯| ⇔ [B]"))
    assert not [i for i in issues if i.severity == "warning"]


def test_render_readable_rel_roundtrips():
    # rel connectors must render as valid chain syntax (`<name-`), so readable re-parses
    out = render(parse_text("[A] -has-> [B]"), "readable")
    assert render(parse_text(out), "triples") == render(parse_text("[A] -has-> [B]"), "triples")
