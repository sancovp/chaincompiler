"""Regression tests for the 2026-07 bug sweep (dietc side)."""
from __future__ import annotations

from dietc.models import DayState
from dietc.rune import render_rune_block
from dietc.vectors import MatrixVector, NutrientVector, SafetyVector


def test_safety_vector_tolerates_unknown_keys():
    # NutrientVector routes unknowns into `other`; SafetyVector must not crash on them
    sv = SafetyVector.from_dict({"caffeine_mg": 10, "caffeine_risk": 0.5})
    assert sv.caffeine_risk == 0.5
    assert any("caffeine_mg" in n for n in sv.notes)


def test_rune_block_carries_the_gap_terms():
    state = DayState(events=[], nutrient_totals=NutrientVector(),
                     matrix_totals=MatrixVector(), safety_state=SafetyVector(),
                     label="Day")
    state.gaps = {"protein_g": 50.0, "fiber_g": 10.0}
    block = render_rune_block(state)
    assert "Gap:{Protein,Fiber}" in block

    # and the block must still be valid HoneyC notation
    from honeyc.parser import parse_text
    parse_text(block)
