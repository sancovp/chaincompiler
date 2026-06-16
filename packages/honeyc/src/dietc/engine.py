"""Orchestrate the DietC daily compile loop."""
from __future__ import annotations

from pathlib import Path

from . import gapcap, patch, safety
from .load import load_day, load_items, load_modules, load_profile
from .models import DayState, GoalProfile, IntakeEvent, IntakeItem, PatchModule
from .vectors import MatrixVector, NutrientVector, SafetyVector


def build_day_state(events: list[IntakeEvent], items: dict[str, IntakeItem], label: str = "Day") -> DayState:
    nutrient = NutrientVector()
    matrix = MatrixVector()
    safety_state = SafetyVector()
    for ev in events:
        item = items.get(ev.item_id)
        if item is None:
            safety_state.notes.append(f"unknown item: {ev.item_id}")
            continue
        nutrient = nutrient + item.nutrient_vector.scale(ev.amount)
        matrix = matrix + item.matrix_vector.scale(ev.amount)
    return DayState(events=events, nutrient_totals=nutrient, matrix_totals=matrix,
                    safety_state=safety_state, label=label)


def compile_day(
    day_path: Path | str,
    profile: GoalProfile,
    modules: dict[str, PatchModule] | None = None,
    *,
    items_override: dict[str, IntakeItem] | None = None,
) -> DayState:
    events, items_file, label = load_day(day_path)
    if items_override is not None:
        items = items_override
    else:
        base = Path(day_path).parent
        items = load_items(base / items_file) if items_file else {}
    state = build_day_state(events, items, label=label)

    gaps, caps, matrix_gaps, warnings = gapcap.compute(state.nutrient_totals, state.matrix_totals, profile)
    state.gaps, state.caps, state.matrix_gaps, state.warnings = gaps, caps, matrix_gaps, warnings

    if modules:
        state.patches = patch.plan(gaps, caps, matrix_gaps, modules, profile)
        state.warnings += safety.check(state.patches, modules, caps, profile)
    return state
