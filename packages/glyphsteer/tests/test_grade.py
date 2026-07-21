"""Grading a corpus: an LLM-assigned grade is a lexical facet + a returned badge.

This is the 'search showing grades' use case. The grade glyph comes back in each hit's
`code` (for display); faceting filters to a grade; the clean text never carries the glyph.
"""
from glyphsteer import GRADE, GRADE_RANK, Chunk, build_index, grade_label, search
from glyphsteer.index import assert_hidden, facet_only

EXC = GRADE.by_name("excellent").glyph
POOR = GRADE.by_name("poor").glyph


def _corpus():
    return [
        Chunk("good1", "use parameterized queries to avoid SQL injection", code=EXC),
        Chunk("bad1", "concatenate user input straight into the SQL string", code=POOR),
        Chunk("good2", "validate inputs at the boundary", code=EXC),
    ]


def test_search_returns_the_grade_badge():
    con = build_index(_corpus(), GRADE)
    hits = search(con, "sql input queries", vocab=GRADE, limit=10)
    by_id = {h["id"]: h for h in hits}
    assert by_id["good1"]["code"] == EXC                 # glyph returned for display
    assert "excellent" in grade_label(GRADE, by_id["good1"]["code"])
    assert_hidden(hits, GRADE)                           # but never in the body text


def test_facet_to_a_grade():
    con = build_index(_corpus(), GRADE)
    assert {h["id"] for h in facet_only(con, EXC, vocab=GRADE)} == {"good1", "good2"}
    assert {h["id"] for h in facet_only(con, POOR, vocab=GRADE)} == {"bad1"}


def test_grades_sort_best_to_worst():
    con = build_index(_corpus(), GRADE)
    hits = search(con, "sql input queries", vocab=GRADE, limit=10)
    ordered = sorted(hits, key=lambda x: GRADE_RANK[x["code"]])
    ordered_ids = [h["id"] for h in ordered]
    # the excellent chunk must rank ahead of the poor one after a grade sort
    assert "good1" in ordered_ids and "bad1" in ordered_ids
    assert ordered_ids.index("good1") < ordered_ids.index("bad1")
