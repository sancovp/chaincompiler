"""Regression tests for the 2026-07 bug sweep — each test pins one fixed defect."""
from __future__ import annotations

import pytest

from glyphsteer import Chunk, build_index, search
from glyphsteer.legend import author, merge
from glyphsteer.vocab import SENTIMENT, Axis, Vocabulary


# -- FTS5 fallback query must escape embedded quotes ----------------------------
def test_punctuation_query_with_quote_does_not_crash():
    con = build_index([Chunk("a", "some text", code="")], SENTIMENT)
    assert search(con, '"') == []       # OperationalError before the fix
    assert search(con, '?"!') == []


# -- overlapping glyphs (prefix pairs) must not phantom-match or mutilate text ---
def _overlapping_vocab() -> Vocabulary:
    # U+26A0 (bare) vs U+26A0 U+FE0F (VS16): the bare glyph is a prefix of the other
    return Vocabulary([Axis("warnbare", "⚠"), Axis("warnemoji", "⚠️")])


def test_parse_matches_longest_glyph_only():
    v = _overlapping_vocab()
    assert v.parse("⚠️") == ["⚠️"]     # not both


def test_strip_removes_whole_glyph_not_its_prefix():
    v = _overlapping_vocab()
    out = v.strip("ok ⚠️ done")
    assert "️" not in out          # no orphaned variation selector


def test_strip_removes_separator_including_its_space():
    from glyphsteer.encode import indexed_form
    pos = SENTIMENT.by_name("positive").glyph
    form = indexed_form(Chunk("i", "text", code=pos))
    assert SENTIMENT.strip(form) == "text"


# -- merge must survive a derived-tag collision (docstring: skips, never raises) -
def test_merge_survives_tag_collision():
    a = author([{"name": "risk", "glyph": "☢️"}])
    b = author([{"name": "Risk!", "glyph": "\U0001F480"}])   # same derived tag `gsxrisk`
    v = merge(a, b)                     # ValueError: duplicate tag before the fix
    assert [ax.name for ax in v.axes] == ["Risk!"]           # last author wins


# -- to_honeyc must preserve the CODE's order (a chain is order-significant) -----
def test_to_honeyc_preserves_code_order():
    urg = SENTIMENT.by_name("urgent").glyph
    pos = SENTIMENT.by_name("positive").glyph
    code = urg + pos                    # urgent first, positive second
    assert SENTIMENT.to_honeyc(code) == f"{urg}→{pos}"


# -- lint() must reject foreign content (the documented syntax_break gate) -------
def test_lint_rejects_foreign_glyphs_and_tokens():
    pytest.importorskip("chaincompiler")
    pytest.importorskip("rulecatcher")
    from glyphsteer.grammar import GlyphGrammar

    pos = SENTIMENT.by_name("positive").glyph
    urg = SENTIMENT.by_name("urgent").glyph
    with GlyphGrammar(SENTIMENT, scope="test_regressions") as gg:
        assert gg.lint(pos + "\U0001F4A9" + urg).verdict == "syntax_break"
        assert gg.lint(pos + "Zqq" + urg).verdict == "syntax_break"
        assert gg.lint(pos + urg).verdict == "ok"            # clean codes still pass
