"""The keystone: the sidecar split + the HIDE invariant.

indexed-form carries the glyph code; returned-form is provably glyph-free.
"""
from glyphsteer import (SENTIMENT, Chunk, RuleAnnotator, annotate_chunk,
                        check_hidden, indexed_form, returned_form)


def _ann():
    return RuleAnnotator.keyword(SENTIMENT, {
        SENTIMENT.by_name("positive").glyph: ["great", "love", "excellent"],
        SENTIMENT.by_name("urgent").glyph: ["now", "urgent", "asap"],
    })


def test_sidecar_split_indexed_has_code_returned_is_clean():
    c = annotate_chunk(Chunk("1", "This is a great fix, ship it now"), _ann(), SENTIMENT)
    assert c.code != ""                                    # something fired
    idx = indexed_form(c)
    for g in SENTIMENT.parse(c.code):
        assert g in idx                                   # code lives in indexed-form
    ret = returned_form(c, SENTIMENT)
    assert ret == "This is a great fix, ship it now"      # clean text returned verbatim


def test_hide_invariant_no_glyph_survives_return():
    for text in ["great urgent love now", "neutral sentence", "ASAP excellent work"]:
        c = annotate_chunk(Chunk("x", text), _ann(), SENTIMENT)
        assert check_hidden(c, SENTIMENT)                  # THE invariant
        assert SENTIMENT.glyphs_in(returned_form(c, SENTIMENT)) == []


def test_preexisting_stray_glyph_is_stripped_into_sidecar_only():
    # a chunk that already contains a glyph must not leak it on return
    dirty = "good job " + SENTIMENT.by_name("positive").glyph
    c = annotate_chunk(Chunk("d", dirty), _ann(), SENTIMENT)
    assert check_hidden(c, SENTIMENT)
    assert SENTIMENT.by_name("positive").glyph not in returned_form(c, SENTIMENT)
