from __future__ import annotations

MBR = '[Mbr]: M*Boundary <is_a-🌸\u200d💧 ⇔ |🍯| ⇔ [Mbl]: M*Blanket <is_a-🍹'

from honeyc.emit_cypher import emit_cypher
from honeyc.emit_prolog import emit_prolog
from honeyc.normalize import normalize
from honeyc.parser import parse_text


def _statements(text: str):
    return normalize(parse_text(text))


def test_emit_prolog_mbr():
    pl = emit_prolog(_statements(MBR))
    assert "entity(mbr)." in pl
    assert "type(mbr, mstar_boundary)." in pl
    assert "is_a(mbr, nectar)." in pl
    assert "bounded(honey)." in pl
    assert "equiv(mbr, honey)." in pl
    assert "mediates(honey, mbr, mbl)." in pl
    # base rules present
    assert "linked(A, B)" in pl
    assert "bounded_bridge(X, A, B)" in pl


def test_emit_cypher_mbr():
    cy = emit_cypher(_statements(MBR))
    assert 'MERGE (n0:Entity {id:"Mbr"})' in cy
    assert "-[:IS_A]->" in cy
    assert "-[:EQUIV]->" in cy
    assert "SET" in cy and "bounded = true" in cy
    assert "-[:MEDIATES" in cy
    assert "-[:HAS_TYPE]->" in cy
