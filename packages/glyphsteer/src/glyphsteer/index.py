"""The lexical index — FTS5/BM25 with the glyph axes as ASCII-sentinel facets.

This is the zero-dependency half of GlyphSteer and it proves the whole pipeline:
annotate → encode (sidecar) → index → facet/search → return CLEAN. Every hit returns
`clean` text — the hide is enforced at the read boundary, structurally.

FINDING (verified): FTS5's unicode61 tokenizer DROPS emoji, so the lexical facet
cannot be the emoji itself — it is the axis's ASCII sentinel `tag` (e.g. `gsxnegative`),
a rare single token ⇒ maximal IDF ⇒ exact, deterministic rank-pin, no embeddings. The
emoji's job is the dense regime; the tag's job is the lexical one. Same axis, two
renderings. Faceting takes a GLYPH and translates it to its tag internally.
"""
from __future__ import annotations

import re
import sqlite3

from .encode import Chunk
from .vocab import SENTIMENT, Vocabulary

_FTS_TERMS = re.compile(r"\w+")


def build_index(chunks: list[Chunk], vocab: Vocabulary = SENTIMENT,
                db_path: str = ":memory:") -> sqlite3.Connection:
    """Index chunks. `body` = clean prose (lexical match); `code` = space-joined ASCII
    sentinel tags (faceting); `clean` is stored UNINDEXED to return it on a hit."""
    con = sqlite3.connect(db_path)
    # `code` = ASCII tags (INDEXED, for faceting); `glyphs` = the emoji code (UNINDEXED,
    # for human display) — FTS5 can't match the emoji but we still want to return it.
    con.execute("CREATE VIRTUAL TABLE chunks USING fts5("
                "id UNINDEXED, body, code, clean UNINDEXED, glyphs UNINDEXED)")
    con.executemany(
        "INSERT INTO chunks(id, body, code, clean, glyphs) VALUES (?,?,?,?,?)",
        [(c.id, c.text, " ".join(vocab.code_tags(c.code)), c.text, c.code) for c in chunks])
    con.commit()
    return con


def _fts_query(q: str) -> str:
    # quote each term as a literal so FTS5 operators in user text (OR/AND/NOT/NEAR)
    # are treated as words, not syntax
    terms = _FTS_TERMS.findall(q)
    # FTS5 string literals escape an embedded quote by doubling it
    return " OR ".join(f'"{t}"' for t in terms) if terms else '"' + q.replace('"', '""') + '"'


def _facet_tag(facet: str, vocab: Vocabulary) -> str:
    """Accept either a glyph or a tag; resolve to the indexed ASCII tag."""
    return vocab.tag_for(facet) or facet


def search(con: sqlite3.Connection, query: str, *, facet: str | None = None,
           vocab: Vocabulary = SENTIMENT, limit: int = 10) -> list[dict]:
    """BM25-ranked lexical search. `facet` (a glyph) adds an exact-match constraint.

    Every hit's `text` is the CLEAN, glyph-free form — the hide, enforced here.
    """
    where = ["chunks MATCH ?"]
    params: list = [_fts_query(query)]
    if facet:
        where.append("code MATCH ?")
        params.append(_facet_tag(facet, vocab))
    sql = (f"SELECT id, clean, glyphs, bm25(chunks) AS score FROM chunks "
           f"WHERE {' AND '.join(where)} ORDER BY score LIMIT ?")
    params.append(limit)
    return [{"id": r[0], "text": r[1], "code": r[2], "score": r[3]}
            for r in con.execute(sql, params)]


def facet_only(con: sqlite3.Connection, facet: str, *, vocab: Vocabulary = SENTIMENT,
               limit: int = 100) -> list[dict]:
    """Pure faceted retrieval: every chunk carrying `facet` (glyph or tag), no query."""
    sql = ("SELECT id, clean, glyphs FROM chunks WHERE code MATCH ? LIMIT ?")
    return [{"id": r[0], "text": r[1], "code": r[2]}
            for r in con.execute(sql, [_facet_tag(facet, vocab), limit])]


def assert_hidden(hits: list[dict], vocab: Vocabulary) -> None:
    """Guard: no hit's returned text may contain a vocabulary glyph."""
    for h in hits:
        leaked = vocab.glyphs_in(h["text"])
        if leaked:
            raise AssertionError(f"glyph leak in returned text of {h['id']!r}: {leaked}")
