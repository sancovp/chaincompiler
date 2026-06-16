from __future__ import annotations

MBR = '[Mbr]: M*Boundary <is_a-🌸\u200d💧 ⇔ |🍯| ⇔ [Mbl]: M*Blanket <is_a-🍹'

from honeyc.ast_nodes import Bounded, Chain, Entity, Glyph, Placeholder, Scope, Transform, TypeAnn
from honeyc.parser import parse_text


def test_parse_entity():
    prog = parse_text("[Mbr]")
    assert isinstance(prog.statements[0], Entity)
    assert prog.statements[0].id == "Mbr"


def test_parse_type_annotation():
    prog = parse_text("[Mbr]: M*Boundary")
    ann = prog.statements[0]
    assert isinstance(ann, TypeAnn)
    assert isinstance(ann.term, Entity)
    assert ann.type_name == "M*Boundary"


def test_parse_bounded_glyph():
    prog = parse_text("|🍯|")
    b = prog.statements[0]
    assert isinstance(b, Bounded)
    assert isinstance(b.term, Glyph)
    assert b.term.name == "Honey"


def test_parse_equivalence_chain():
    prog = parse_text("[A] ⇔ [B] ⇔ [C]")
    chain = prog.statements[0]
    assert isinstance(chain, Chain)
    assert len(chain.terms) == 3
    assert [c.kind for c in chain.connectors] == ["equiv", "equiv"]


def test_parse_reverse_relation():
    prog = parse_text("[Mbr] <is_a-🌸‍💧")
    chain = prog.statements[0]
    assert isinstance(chain, Chain)
    assert chain.connectors[0].kind == "rel"
    assert chain.connectors[0].value == "is_a"


def test_parse_scope_with_placeholder():
    prog = parse_text("[HIVE]:{ [Goal], 📃 }")
    scope = prog.statements[0]
    assert isinstance(scope, Scope)
    assert any(isinstance(c, Placeholder) for c in scope.body)


def test_parse_transform_object():
    prog = parse_text("${[A] ⇒ [B]}")
    assert isinstance(prog.statements[0], Transform)


def test_parse_full_mbr_example():
    prog = parse_text(MBR)
    chain = prog.statements[0]
    assert isinstance(chain, Chain)
    assert [type(t).__name__ for t in chain.terms] == ["TypeAnn", "Glyph", "Bounded", "TypeAnn", "Glyph"]
