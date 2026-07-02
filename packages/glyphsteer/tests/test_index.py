"""End-to-end lexical loop (zero deps): annotate → encode → index → facet → return CLEAN.

Proves the whole GlyphSteer pipeline in the regime that needs no embeddings, and that
the glyph steers retrieval (faceting rank-pins) while never leaking into output.
"""
from glyphsteer import (SENTIMENT, Chunk, RuleAnnotator, annotate_chunk,
                        assert_hidden, build_index, facet_only, search)

NEG = SENTIMENT.by_name("negative").glyph
POS = SENTIMENT.by_name("positive").glyph


def _corpus():
    raw = [
        Chunk("ok1", "the deployment pipeline ran and the build passed"),
        Chunk("bug1", "the deployment pipeline crashed, this is broken and terrible"),
        Chunk("ok2", "the build pipeline is excellent and works great"),
    ]
    ann = RuleAnnotator.keyword(SENTIMENT, {
        POS: ["great", "excellent", "passed", "works"],
        NEG: ["broken", "terrible", "crashed", "failed"],
    })
    return [annotate_chunk(c, ann, SENTIMENT) for c in raw]


def test_facet_pins_negative_chunks_only():
    con = build_index(_corpus())
    hits = facet_only(con, NEG)
    assert {h["id"] for h in hits} == {"bug1"}


def test_query_plus_facet_steers_and_returns_clean():
    con = build_index(_corpus())
    # same lexical query "pipeline"; facet picks the negative one
    neg = search(con, "pipeline", facet=NEG)
    assert neg and neg[0]["id"] == "bug1"
    assert_hidden(neg, SENTIMENT)                      # no glyph in returned text
    assert NEG not in neg[0]["text"]


def test_baseline_query_without_facet_returns_all():
    con = build_index(_corpus())
    ids = {h["id"] for h in search(con, "pipeline")}
    assert ids == {"ok1", "ok2", "bug1"}              # facet is what narrows it


def test_punctuation_query_with_quote_is_safe():
    con = build_index(_corpus(), SENTIMENT)
    assert search(con, '"') == []                    # crashed pre-fix (unescaped FTS5 string)
