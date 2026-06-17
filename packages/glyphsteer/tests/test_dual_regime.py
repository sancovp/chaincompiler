"""The central finding as a regression: one axis, two renderings.

FTS5 drops emoji → the lexical facet must be the ASCII tag, not the glyph. The dense
marker stays the emoji (it goes into the embedding input). This test pins both.
"""
import sqlite3

from glyphsteer import SENTIMENT, Chunk, build_index, facet_only, indexed_form
from glyphsteer.vocab import default_tag, is_fts_token


def test_default_tag_is_single_fts_token():
    assert default_tag("negative") == "gsxnegative"
    assert is_fts_token("gsxnegative")
    assert not is_fts_token("gsx negative")        # space splits it
    assert SENTIMENT.by_name("negative").tag == "gsxnegative"


def test_fts5_drops_emoji_but_indexes_the_tag():
    # the finding, asserted directly against sqlite
    con = sqlite3.connect(":memory:")
    con.execute("CREATE VIRTUAL TABLE t USING fts5(c)")
    emoji = SENTIMENT.by_name("negative").glyph
    con.execute("INSERT INTO t(c) VALUES (?)", (emoji,))
    con.execute("INSERT INTO t(c) VALUES (?)", ("gsxnegative",))
    n_emoji = con.execute("SELECT count(*) FROM t WHERE t MATCH ?", (f'"{emoji}"',)).fetchone()[0]
    n_tag = con.execute("SELECT count(*) FROM t WHERE t MATCH ?", ("gsxnegative",)).fetchone()[0]
    assert n_emoji == 0      # emoji NOT lexically indexable
    assert n_tag == 1        # ASCII sentinel IS


def test_facet_by_glyph_resolves_to_tag_internally():
    neg = SENTIMENT.by_name("negative").glyph
    c = Chunk("x", "the build broke", code=neg)
    con = build_index([c])
    # caller passes the GLYPH; index translates to the tag under the hood
    assert {h["id"] for h in facet_only(con, neg)} == {"x"}


def test_indexed_form_carries_emoji_for_the_dense_regime():
    neg = SENTIMENT.by_name("negative").glyph
    c = Chunk("x", "the build broke", code=neg)
    assert neg in indexed_form(c)      # the emoji rides into the embedding input
