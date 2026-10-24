"""Regressions for the defects the public repository's two bug sweeps found in glyphsteer (its pull requests #1 and #2).

Each test fails on the code before its fix and passes after it.
"""
from __future__ import annotations

import pytest

from glyphsteer import Chunk, build_index, check_hidden, search
from glyphsteer.encode import indexed_form, returned_form
from glyphsteer.legend import author, merge
from glyphsteer.vocab import SENTIMENT, SEP, Axis, Vocabulary

POS = SENTIMENT.by_name("positive").glyph
URG = SENTIMENT.by_name("urgent").glyph
BARE, EMOJI = "⚠", "⚠️"                   # U+26A0, and U+26A0 U+FE0F: the bare glyph is part of its variant
WARN = Vocabulary([Axis("warnbare", BARE), Axis("warnemoji", EMOJI)])


# ── a query with no word in it finds nothing, and never crashes the index ───────────────────────────────────
@pytest.mark.parametrize("query", ['"', '?"!', '""'])
def test_a_query_with_no_word_finds_nothing(query):
    con = build_index([Chunk("a", "some text", code="")], SENTIMENT)
    assert search(con, query) == []


# ── a glyph that is part of another: matched longest first, never two that overlap ──────────────────────────
def test_a_variant_parses_as_itself_alone():
    assert WARN.parse(EMOJI) == [EMOJI]
    assert WARN.glyphs_in(f"x {EMOJI} y") == [EMOJI]
    assert WARN.code_tags(EMOJI) == ["gsxwarnemoji"]


def test_a_glyph_beside_its_variant_parses_as_both():
    assert WARN.parse(EMOJI + BARE) == [BARE, EMOJI]            # vocabulary order


def test_strip_removes_a_variant_whole():
    out = WARN.strip(f"ok {EMOJI} done")
    assert out == "ok  done"
    assert "️" not in out


def test_the_hide_check_holds_on_a_variant_and_catches_a_leak():
    chunk = Chunk("c", f"ok {EMOJI} done", code="")
    assert check_hidden(chunk, WARN)
    assert returned_form(chunk, WARN) == "ok  done"
    assert WARN.glyphs_in(f"leaked {EMOJI}") == [EMOJI]


def test_to_honeyc_keeps_a_variant_s_place_in_the_code():
    assert WARN.to_honeyc(EMOJI + BARE) == f"{EMOJI}→{BARE}"


# ── strip goes on until nothing is left to remove: removing a glyph can join its neighbours into another ──────
def test_strip_removes_a_glyph_its_own_removal_made():
    vocab = Vocabulary([Axis("warn", EMOJI), Axis("smile", POS)])
    text = BARE + POS + "️"                                  # ⚠ 😊 U+FE0F: drop 😊 and ⚠️ appears
    assert vocab.strip(text) == ""
    assert check_hidden(Chunk("c", text), vocab)


# ── strip removes the whole separator ────────────────────────────────────────────────────────────────────────
def test_strip_removes_the_separator_with_its_space():
    assert SENTIMENT.strip(indexed_form(Chunk("i", "text", code=POS))) == "text"
    assert SENTIMENT.strip(f"text{SEP}{POS}") == "text"


# ── to_honeyc keeps the code's order ─────────────────────────────────────────────────────────────────────────
def test_to_honeyc_keeps_the_code_order():
    assert SENTIMENT.to_honeyc(URG + POS) == f"{URG}→{POS}"
    assert SENTIMENT.to_honeyc(SENTIMENT.code([URG, POS])) == f"{URG}→{POS}"


# ── merge keeps the last author when two names derive one tag ───────────────────────────────────────────────
def test_merge_keeps_the_last_author_on_a_tag_clash():
    merged = merge(author([{"name": "risk", "glyph": "☢️"}]), author([{"name": "Risk!", "glyph": "💀"}]))
    assert [a.name for a in merged.axes] == ["Risk!"]


def test_merge_drops_only_what_clashes_after_a_name_takes_a_new_glyph():
    merged = merge(author([{"name": "risk", "glyph": "☢️"}]), author([{"name": "risk", "glyph": "💀"}]),
                   author([{"name": "danger", "glyph": "☢️"}]))     # ☢️ is free again once risk took 💀
    assert [(a.name, a.glyph) for a in merged.axes] == [("risk", "💀"), ("danger", "☢️")]


def test_merge_forgets_an_evicted_axis_s_glyph():
    merged = merge(author([{"name": "risk", "glyph": "☢️"}]), author([{"name": "Risk!", "glyph": "💀"}]),  # evicts risk
                   author([{"name": "risk", "glyph": "🔥"}]),        # risk returns with 🔥 and evicts Risk! by tag
                   author([{"name": "danger", "glyph": "☢️"}]))     # ☢️ belongs to no one now
    assert [(a.name, a.glyph) for a in merged.axes] == [("risk", "🔥"), ("danger", "☢️")]


# ── lint refuses content foreign to the vocabulary ───────────────────────────────────────────────────────────
def test_lint_refuses_a_foreign_glyph_or_word():
    pytest.importorskip("chaincompiler")
    pytest.importorskip("rulecatcher")
    from glyphsteer.grammar import GlyphGrammar
    with GlyphGrammar(SENTIMENT, scope="test_regressions") as gg:
        assert gg.lint(POS + "\U0001F4A9" + URG).verdict == "syntax_break"
        assert gg.lint(POS + "Zqq").verdict == "syntax_break"
        assert gg.lint(POS + URG).verdict == "ok"


def test_lint_reads_a_variant_s_place_in_the_code():
    pytest.importorskip("chaincompiler")
    pytest.importorskip("rulecatcher")
    from glyphsteer.grammar import GlyphGrammar
    with GlyphGrammar(WARN, scope="test_regressions_warn") as gg:
        lint = gg.lint(EMOJI + BARE)                              # the variant first: out of vocabulary order
        assert lint.verdict == "orthogonal"
        assert lint.fix == BARE + EMOJI
