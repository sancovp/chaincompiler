"""One reading of the notation: honeyc's README, its grammar, its code and its examples agree.

The README's `## Core notation` table is read as data: every marker the grammar defines has a row, and every row's
example parses to exactly the triples the row states. The README's core example prints what it says it prints, the
readable lens writes each relation back in the spelling it read, and the code that writes the notation (check's
rewrites, dietc's rune and the block it passes through honeyc) writes only markers the grammar reads as it means them.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from honeyc.check import check_program
from honeyc.normalize import is_mediation, normalize
from honeyc.parser import parse_text
from honeyc.render import render

PACKAGE = Path(__file__).resolve().parents[1]
README = (PACKAGE / "README.md").read_text(encoding="utf-8")
GRAMMAR = (PACKAGE / "src" / "honeyc" / "grammar.lark").read_text(encoding="utf-8")
_MARKER = {"entity", "symbol", "glyph"}


def _cells(row: str) -> list[str]:
    """A markdown table row's cells: split on the pipes that are not escaped, then unescape `\\|`."""
    return [c.strip().replace("\\|", "|") for c in re.split(r"(?<!\\)\|", row.strip().strip("|"))]


def _code(cell: str) -> list[str]:
    return re.findall(r"`([^`]+)`", cell)


def _table() -> list[dict]:
    section = README.split("## Core notation", 1)[1].split("\n## ", 1)[0]
    rows = [l for l in section.splitlines() if l.startswith("|") and not l.startswith("|---")][1:]
    return [dict(zip(("marker", "reads", "example", "triples"), _cells(r))) for r in rows]


def _statements(text: str) -> list[str]:
    out = []
    for s in normalize(parse_text(text)):
        line = (f"{s.subject} mediates {s.object} target={s.meta['target']}" if is_mediation(s)
                else f"{s.subject} {s.predicate} {s.object}")
        out.append(re.sub(r"xf_[0-9a-f]{8}", "xf_…", line))
    return out


TABLE = _table()


@pytest.mark.parametrize("row", TABLE, ids=[r["marker"] for r in TABLE])
def test_each_marker_s_example_gives_the_triples_its_row_states(row):
    (example,) = _code(row["example"])
    stated = set(_code(row["triples"]))
    full = set(_statements(example))
    markers = {s for s in full if s.split()[1] in _MARKER and s.endswith(" true")}
    assert stated <= full, f"stated but not produced: {stated - full}"
    assert full - markers <= stated, f"produced but not stated: {(full - markers) - stated}"


def test_every_marker_the_grammar_defines_has_a_row():
    markers = " ".join(r["marker"] for r in TABLE)
    literals = set(re.findall(r'"([^"]+)"', GRAMMAR))
    assert literals, "no literal read from the grammar"
    missing = sorted(l for l in literals if l not in markers)
    assert not missing, f"grammar literals with no row: {missing}"
    connectors = [c.split()[1] for r in TABLE for c in _code(r["marker"]) if len(c.split()) == 3]
    for name in ("REL_FWD", "REL_REV", "REL_BI"):
        pattern = re.search(rf"^{name}:\s*/(.+)/\s*$", GRAMMAR, re.M).group(1)
        assert any(re.fullmatch(pattern, c) for c in connectors), f"the relation marker {name} has no row"


def test_the_core_example_prints_what_the_readme_says():
    after = README.split("## Core example", 1)[1]
    source, printed = re.findall(r"```txt\n(.*?)\n```", after, re.S)[:2]
    assert render(parse_text(source), "triples") == printed


@pytest.mark.parametrize("source", ["[A] -rel-> [B]", "[A] <rel- [B]", "[A] <rel> [B]"])
def test_the_readable_lens_writes_each_relation_spelling_back(source):
    written = render(parse_text(source), "readable")
    assert written == source
    assert set(_statements(written)) == set(_statements(source))


def test_every_bundled_example_parses():
    for rune in sorted((PACKAGE / "examples").glob("*.rune")):
        parse_text(rune.read_text(encoding="utf-8"))


@pytest.mark.parametrize("chain, rewrite, mediator, left, right", [
    ("[A] ⇒ [B] ⇒ [C]", "[A] ⇒ |[B]| ⇒ [C]", "B", "A", "C"),
    ("[A] ⇔ 🍯 ⇔ [B]", "[A] ⇔ |🍯| ⇔ [B]", "🍯", "A", "B"),
    ("[A] -owns-> [X] ⇔ 🍯 ⇒ [B]", "[A] -owns-> [X] ⇔ |🍯| ⇒ [B]", "🍯", "A", "B"),
    ("[A] ⇒ [B]: T ⇒ [C]", "[A] ⇒ |[B]: T| ⇒ [C]", "B", "A", "C"),
    ("[A] <owns- [X] ⇒ M ⇒ [B]", "[A] <owns- [X] ⇒ |M| ⇒ [B]", "M", "A", "B"),
])
def test_check_s_rewrite_is_the_chain_with_the_mediator_bounded(chain, rewrite, mediator, left, right):
    (warning,) = [i for i in check_program(parse_text(chain)) if i.severity == "warning"]
    assert warning.suggested_rewrite == rewrite
    added = {f"{mediator} bounded true", f"{mediator} mediates {left} target={right}"}
    assert set(_statements(rewrite)) == set(_statements(chain)) | added


def test_dietc_s_rune_writes_only_markers_the_grammar_reads():
    from dietc.models import DayState
    from dietc.rune import render_rune, render_rune_block
    from dietc.vectors import MatrixVector, NutrientVector, SafetyVector
    day = DayState(events=[], nutrient_totals=NutrientVector(), matrix_totals=MatrixVector(),
                   safety_state=SafetyVector(), label="Day")
    day.gaps, day.caps = {"protein_g": 10.0}, {"sodium_mg": 300.0}
    statements = set(_statements(render_rune(day)))
    assert "ΔGap watches CapWatch" in statements
    assert "ΔGap produces ImprovedPattern" in statements
    assert not any(s.startswith("CapWatch produces") for s in statements)
    block = set(_statements(render_rune_block(day)))           # the block render_via_honeyc passes through honeyc
    assert not [s for s in block if " has_type " in s], "a step label read as a type"
    assert {"Estimate contains Input", "Input compiles_to NutrientVector", "Compare contains DayState",
            "GoalProfile produces Gap", "PatchSelect contains Gap", "Gap produces Patch"} <= block
