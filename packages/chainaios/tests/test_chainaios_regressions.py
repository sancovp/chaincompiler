"""A GBA's search (`chaincompiler gba search`) never crashes on what a query holds: one with no word in it finds
nothing, and an operator word (`NOT`, `AND`) is read as a word.

A query with no word crashes glyphsteer's index (the public repository's bug sweeps, pull requests #1 and #2), and both
crash SkillTree's search behind this door; the door sends SkillTree the query's words alone.
"""
from __future__ import annotations

import tempfile
from pathlib import Path

from click.testing import CliRunner

from chainaios.cli import main as chaincompiler_cli
from chainaios.gba import make_gba, search


def test_gba_search_answers_a_query_with_no_word_with_nothing():
    root = Path(tempfile.mkdtemp(prefix="test_gba_query_")) / "triage"
    g = make_gba("triage", root, atoms=["[Symptom] ⇒ [Scope] ⇒ |Severity|"])
    for query in ('"', '?"!', '""', "   "):
        assert search(g, query) == []
    assert search(g, "severity")
    result = CliRunner().invoke(chaincompiler_cli, ["gba", "search", str(root), '"'])
    assert result.exit_code == 0, result.output


def test_gba_search_reads_operator_words_as_words():
    root = Path(tempfile.mkdtemp(prefix="test_gba_operators_")) / "triage"
    g = make_gba("triage", root, atoms=["[Symptom] ⇒ [Scope] ⇒ |Severity|"])
    assert search(g, "NOT") == search(g, "not")             # FTS5's NOT, unquoted, was a syntax error; now a word
    for query in ("severity AND", "Severity OR NOT", "NEAR severity"):
        assert search(g, query), query
    result = CliRunner().invoke(chaincompiler_cli, ["gba", "search", str(root), "NOT"])
    assert result.exit_code == 0, result.output
