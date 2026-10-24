"""The self-interpreter's search door never crashes on what a query holds: one with no word in it finds nothing, and
an operator word (`NOT`, `AND`) is read as a word.

A query with no word crashes glyphsteer's index (the public repository's bug sweeps, pull requests #1 and #2), and both
crash SkillTree's search behind this door; the door sends SkillTree the query's words alone.
"""
from __future__ import annotations

from pathlib import Path

from si.server import si_search


def _tree(root: Path) -> Path:
    skill = root / "triage" / "SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text("---\nname: triage\ndescription: triage some text\n---\nbody text\n", encoding="utf-8")
    return root


def test_si_search_answers_a_query_with_no_word_with_nothing(tmp_path):
    root = _tree(tmp_path)
    for query in ('"', '?"!', '""', "   "):
        assert si_search(str(root), query) == []
    assert [h["name"] for h in si_search(str(root), "triage")] == ["triage"]


def test_si_search_reads_operator_words_as_words(tmp_path):
    root = _tree(tmp_path)
    assert si_search(str(root), "NOT") == []                   # FTS5's NOT, unquoted, was a syntax error
    for query in ("triage AND", "Triage OR NOT", "NEAR triage", "triage*"):
        assert [h["name"] for h in si_search(str(root), query)] == ["triage"], query
