"""Syntax consistency via rulecatcher: ok / orthogonal / syntax_break over glyph codes."""
import pytest

pytest.importorskip("chaincompiler")
pytest.importorskip("rulecatcher")

from glyphsteer import SENTIMENT
from glyphsteer.grammar import GlyphGrammar

POS = SENTIMENT.by_name("positive").glyph
URG = SENTIMENT.by_name("urgent").glyph
NEG = SENTIMENT.by_name("negative").glyph


@pytest.fixture(scope="module")
def gg():
    g = GlyphGrammar(SENTIMENT, scope="test_glyphsteer")
    yield g
    g.close()


def test_canonical_code_is_ok(gg):
    assert gg.lint(SENTIMENT.code([POS, URG])).verdict == "ok"   # vocab order
    assert gg.consistent(SENTIMENT.code([POS, NEG, URG]))


def test_reversed_code_is_orthogonal_with_canonical_fix(gg):
    lint = gg.lint(URG + POS)                                    # urgent before positive
    assert lint.verdict == "orthogonal"
    assert lint.fix == SENTIMENT.code([POS, URG])                # reorder to vocab order


def test_foreign_token_is_syntax_break(gg):
    assert gg.lint_chain("gsxpositive -> gsxbogus").verdict == "syntax_break"


def test_single_and_empty_codes_ok(gg):
    assert gg.lint(POS).verdict == "ok"
    assert gg.lint("").verdict == "ok"


def test_canonicalize_reorders(gg):
    assert gg.canonicalize(URG + POS) == SENTIMENT.code([POS, URG])


def test_annotate_chunk_canonicalizes_with_grammar(gg):
    from glyphsteer import Chunk, RuleAnnotator, annotate_chunk
    # annotator fires urgent-keyword before positive-keyword in input order
    ann = RuleAnnotator.keyword(SENTIMENT, {URG: ["now"], POS: ["great"]})
    c = annotate_chunk(Chunk("x", "do it now, it's great"), ann, SENTIMENT, grammar=gg)
    assert c.code == SENTIMENT.code([POS, URG])      # stored code is canonical, not input-order


def test_foreign_glyph_in_code_is_syntax_break(gg):
    # unknown content must not be laundered out by code_tags before the gate
    assert gg.lint(POS + "Zqq").verdict == "syntax_break"
    assert gg.lint(POS + "\U0001F4A9").verdict == "syntax_break"
