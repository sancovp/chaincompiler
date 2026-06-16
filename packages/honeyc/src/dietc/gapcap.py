"""Compute nutrient gaps, upper-limit caps, matrix gaps, and pattern warnings."""
from __future__ import annotations

from .models import GoalProfile
from .vectors import MatrixVector, NutrientVector, positive_cap, positive_gap

_NEAR_LIMIT_FRACTION = 0.8
_CAP_WATCH_KEYS = ["added_sugar_g", "sodium_mg", "saturated_fat_g"]


def compute(
    nutrient_totals: NutrientVector,
    matrix_totals: MatrixVector,
    profile: GoalProfile,
) -> tuple[dict[str, float], dict[str, float], dict[str, float], list[str]]:
    current = nutrient_totals.to_dict()
    targets = {k: v for k, v in profile.targets.to_dict().items() if v > 0}
    limits = {k: v for k, v in profile.upper_limits.to_dict().items() if v > 0}
    min_matrix = {k: v for k, v in profile.minimum_matrix.to_dict().items() if v > 0}

    gaps = positive_gap(targets, current)
    caps = positive_cap(current, limits)
    matrix_gaps = positive_gap(min_matrix, matrix_totals.to_dict())

    warnings: list[str] = []
    # near (but not over) upper limits
    for key in _CAP_WATCH_KEYS:
        if key in limits and key not in caps:
            if current.get(key, 0) >= _NEAR_LIMIT_FRACTION * limits[key]:
                warnings.append(f"{key} is approaching its upper limit "
                                f"({current.get(key, 0):.0f}/{limits[key]:.0f}).")
    # over limit
    for key, over in caps.items():
        warnings.append(f"{key} exceeds its upper limit by {over:.0f}.")
    # technically-patchable-but-poor-pattern signal
    micros_ok = not any(k in gaps for k in ("calcium_mg", "magnesium_mg", "potassium_mg"))
    if matrix_gaps and micros_ok and matrix_totals.whole_food_score < 2:
        warnings.append("matrix/diversity is low even though some micronutrients are met; "
                        "pattern quality may be poor despite patching.")
    return gaps, caps, matrix_gaps, warnings
