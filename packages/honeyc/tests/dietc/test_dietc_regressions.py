"""Regressions for the defects the public repository's two bug sweeps found in dietc (its pull requests #1 and #2).

Each test fails on the code before its fix and passes after it.
"""
from __future__ import annotations

from dietc.load import load_items
from dietc.models import DayState
from dietc.rune import render_rune_block, render_via_honeyc
from dietc.vectors import MatrixVector, NutrientVector, SafetyVector
from honeyc.parser import parse_text


def _day(gaps: dict[str, float]) -> DayState:
    state = DayState(events=[], nutrient_totals=NutrientVector(), matrix_totals=MatrixVector(),
                     safety_state=SafetyVector(), label="Day")
    state.gaps = gaps
    return state


# ── a safety vector keeps a key it does not know, as a note, at every door that reads one ───────────────────
def test_a_safety_vector_keeps_an_unknown_key_as_a_note():
    sv = SafetyVector.from_dict({"caffeine_mg": 10, "caffeine_risk": 0.5})
    assert sv.caffeine_risk == 0.5
    assert any("caffeine_mg" in note for note in sv.notes)


def test_load_items_survives_an_unknown_safety_key(tmp_path):
    items = tmp_path / "items.yaml"
    items.write_text("items:\n  - id: x\n    safety_vector:\n      mystery_risk: 1\n", encoding="utf-8")
    loaded = load_items(items)
    assert any("mystery_risk" in note for note in loaded["x"].safety_vector.notes)


# ── the rune block writes the day's gaps, and still parses as HoneyC ─────────────────────────────────────────
def test_the_rune_block_writes_the_gaps_and_still_parses():
    block = render_rune_block(_day({"protein_g": 50.0, "fiber_g": 10.0}))
    assert "Gap:{Protein,Fiber}" in block
    parse_text(block)


def test_the_rune_block_through_honeyc_carries_the_gaps():
    out = render_via_honeyc(_day({"protein_g": 50.0}))
    assert out is not None and "Gap:{ Protein }" in out
