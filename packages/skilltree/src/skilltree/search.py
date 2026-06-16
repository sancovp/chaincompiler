"""The `search` arm — coordinate-scoped lexical search over the skill corpus.

v1 (evidence-driven, see .claude/rules + the research): SQLite **FTS5 / BM25** over
the skill files, with **coordinate-scoped subtree filtering** — rank within any
coord-rooted region of the tree (`scope_coord="0.1"` → only `0.1` and its
descendants). For a small corpus of short, keyword-dense skill docs, BM25 is
enough; the differentiated capability is the subtree scoping (the coordinate is
the address AND the search scope).

A dense/vector layer fused via RRF is a LATER, evidence-driven upgrade — add it
only when logged BM25 misses are semantic (synonym/paraphrase), not lexical.
MCTS-style tree search is for skill *composition* (SCCC), not lookup.
"""
from __future__ import annotations

import re
import sqlite3
from pathlib import Path

_COORD_NAME = re.compile(r"^([0-9][0-9.]*)-(.+)$")
_FTS_TERMS = re.compile(r"\w+")


def _read_skill(md: Path) -> tuple[str, str, str, str]:
    txt = md.read_text(encoding="utf-8", errors="replace")
    nm = re.search(r"^\s*name:\s*(.+?)\s*$", txt, re.M)
    ds = re.search(r"^\s*description:\s*(.+?)\s*$", txt, re.M)
    name = nm.group(1).strip() if nm else md.parent.name
    desc = ds.group(1).strip() if ds else ""
    body = txt.split("---", 2)[-1].strip() if txt.lstrip().startswith("---") else txt.strip()
    m = _COORD_NAME.match(name)
    coord = m.group(1) if m else ""
    return coord, name, desc, body


def build_index(root_dir: str | Path, db_path: str = ":memory:") -> sqlite3.Connection:
    """Index every SKILL.md under root_dir into an FTS5 table. Returns the connection."""
    con = sqlite3.connect(db_path)
    con.execute("CREATE VIRTUAL TABLE skills USING fts5(name, description, body, "
                "coord UNINDEXED, path UNINDEXED)")
    rows = []
    for md in Path(root_dir).rglob("SKILL.md"):
        coord, name, desc, body = _read_skill(md)
        rows.append((name, desc, body, coord, str(md)))
    con.executemany("INSERT INTO skills(name, description, body, coord, path) VALUES (?,?,?,?,?)", rows)
    con.commit()
    return con


def _fts_query(q: str) -> str:
    terms = _FTS_TERMS.findall(q)
    return " OR ".join(terms) if terms else q


def search(con: sqlite3.Connection, query: str, *, scope_coord: str | None = None,
           limit: int = 10) -> list[dict]:
    """BM25-ranked search, optionally scoped to a coordinate subtree."""
    sql = ("SELECT name, coord, description, path, bm25(skills) AS score "
           "FROM skills WHERE skills MATCH ?")
    params: list = [_fts_query(query)]
    if scope_coord:
        sql += " AND (coord = ? OR coord LIKE ?)"
        params += [scope_coord, f"{scope_coord}.%"]
    sql += " ORDER BY score LIMIT ?"      # bm25(): lower = better
    params.append(limit)
    return [{"name": r[0], "coord": r[1], "description": r[2], "path": r[3], "score": r[4]}
            for r in con.execute(sql, params)]


def search_tree(root_dir: str | Path, query: str, *, scope_coord: str | None = None,
                limit: int = 10) -> list[dict]:
    """Convenience: index a tree dir and search it in one call."""
    return search(build_index(root_dir), query, scope_coord=scope_coord, limit=limit)
