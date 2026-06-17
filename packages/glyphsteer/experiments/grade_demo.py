"""Grading a RAG corpus: an LLM grades 'what's good and what isn't', search shows grades.

Grading rides the LEXICAL regime (the reliable one): the grade is an exact-match facet you
filter by + a badge you display. NOT the dense/sentiment direction — quality != mood.

Here the grades are hand-assigned to stand in for an LLM judge; in production you'd use
`LLMAnnotator(GRADE, judge=...)` where the judge returns the grade glyph for each chunk.

Run:  python experiments/grade_demo.py   (zero deps)
"""
from __future__ import annotations

from glyphsteer import GRADE, GRADE_RANK, Chunk, build_index, grade_label, search
from glyphsteer.index import facet_only

EXC, GOOD, FAIR, POOR = (GRADE.by_name(n).glyph for n in ("excellent", "good", "fair", "poor"))

# A corpus about database practices, each chunk graded by (a stand-in for) an LLM judge.
CORPUS = [
    Chunk("c1", "Use parameterized queries to prevent SQL injection (OWASP A03).", code=EXC),
    Chunk("c2", "Connection pooling improves DB throughput; benchmark before tuning.", code=GOOD),
    Chunk("c3", "A caching layer cuts DB load; set TTL per access pattern.", code=GOOD),
    Chunk("c4", "You can concatenate user input into SQL strings, usually fine.", code=POOR),
    Chunk("c5", "If the database is slow just restart the server.", code=POOR),
    Chunk("c6", "Indexes might help query speed, not totally sure when.", code=FAIR),
]


def show(title, hits):
    print(f"\n{title}")
    for h in sorted(hits, key=lambda x: GRADE_RANK.get(x["code"], 9)):
        print(f"  [{grade_label(GRADE, h['code']):16s}] {h['text']}")


def main() -> None:
    con = build_index(CORPUS, GRADE)

    # 1) ordinary search — every result carries its grade badge
    show("search 'database' — results WITH grades (best→worst):",
         search(con, "database SQL query DB", vocab=GRADE, limit=10))

    # 2) faceted: only the excellent chunks
    show("facet = excellent only:", facet_only(con, EXC, vocab=GRADE))

    # 3) faceted: the bad ones (audit 'what isn't good')
    show("facet = poor only (the audit view):", facet_only(con, POOR, vocab=GRADE))


if __name__ == "__main__":
    main()
