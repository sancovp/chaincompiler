"""Nutrient / matrix / safety vectors and their arithmetic."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

NUTRIENT_FIELDS = [
    "calories", "protein_g", "carbs_g", "sugars_g", "added_sugar_g", "fiber_g",
    "fat_g", "saturated_fat_g", "omega3_g", "omega6_g", "sodium_mg", "potassium_mg",
    "calcium_mg", "magnesium_mg", "iron_mg", "zinc_mg", "iodine_mcg", "selenium_mcg",
    "vitamin_d_mcg", "vitamin_b12_mcg", "choline_mg",
]


@dataclass
class NutrientVector:
    calories: float = 0
    protein_g: float = 0
    carbs_g: float = 0
    sugars_g: float = 0
    added_sugar_g: float = 0
    fiber_g: float = 0
    fat_g: float = 0
    saturated_fat_g: float = 0
    omega3_g: float = 0
    omega6_g: float = 0
    sodium_mg: float = 0
    potassium_mg: float = 0
    calcium_mg: float = 0
    magnesium_mg: float = 0
    iron_mg: float = 0
    zinc_mg: float = 0
    iodine_mcg: float = 0
    selenium_mcg: float = 0
    vitamin_d_mcg: float = 0
    vitamin_b12_mcg: float = 0
    choline_mg: float = 0
    other: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, float]:
        out = {f: float(getattr(self, f)) for f in NUTRIENT_FIELDS}
        out.update({k: float(v) for k, v in self.other.items()})
        return out

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "NutrientVector":
        data = dict(data or {})
        known = {k: float(data.pop(k)) for k in list(data) if k in NUTRIENT_FIELDS}
        other = {k: float(v) for k, v in data.items() if k != "other"}
        other.update({k: float(v) for k, v in (data.get("other") or {}).items()})
        return cls(**known, other=other)

    def __add__(self, o: "NutrientVector") -> "NutrientVector":
        a, b = self.to_dict(), o.to_dict()
        return NutrientVector.from_dict({k: a.get(k, 0) + b.get(k, 0) for k in set(a) | set(b)})

    def scale(self, k: float) -> "NutrientVector":
        return NutrientVector.from_dict({key: v * k for key, v in self.to_dict().items()})


_MATRIX_FIELDS = [
    "whole_food_score", "plant_diversity_score", "color_diversity_score", "fermented_count",
    "legume_count", "cruciferous_count", "berry_count", "green_leafy_count", "polyphenol_score",
    "processing_score", "satiety_score", "chewing_score", "water_content_score", "gut_tolerance_risk",
]


@dataclass
class MatrixVector:
    whole_food_score: float = 0
    plant_diversity_score: float = 0
    color_diversity_score: float = 0
    fermented_count: float = 0
    legume_count: float = 0
    cruciferous_count: float = 0
    berry_count: float = 0
    green_leafy_count: float = 0
    polyphenol_score: float = 0
    processing_score: float = 0
    satiety_score: float = 0
    chewing_score: float = 0
    water_content_score: float = 0
    gut_tolerance_risk: float = 0

    def to_dict(self) -> dict[str, float]:
        return {f: float(getattr(self, f)) for f in _MATRIX_FIELDS}

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "MatrixVector":
        data = data or {}
        return cls(**{k: float(v) for k, v in data.items() if k in _MATRIX_FIELDS})

    def __add__(self, o: "MatrixVector") -> "MatrixVector":
        a, b = self.to_dict(), o.to_dict()
        return MatrixVector.from_dict({k: a[k] + b[k] for k in a})

    def scale(self, k: float) -> "MatrixVector":
        return MatrixVector.from_dict({key: v * k for key, v in self.to_dict().items()})


@dataclass
class SafetyVector:
    sodium_excess_risk: float = 0
    added_sugar_excess_risk: float = 0
    saturated_fat_excess_risk: float = 0
    fiber_ramp_risk: float = 0
    sugar_alcohol_risk: float = 0
    caffeine_risk: float = 0
    supplement_conflict_risk: float = 0
    allergen_flags: list[str] = field(default_factory=list)
    interaction_flags: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "SafetyVector":
        data = data or {}
        numeric = {k: float(v) for k, v in data.items()
                   if k not in ("allergen_flags", "interaction_flags", "notes")}
        return cls(
            **numeric,
            allergen_flags=list(data.get("allergen_flags", [])),
            interaction_flags=list(data.get("interaction_flags", [])),
            notes=list(data.get("notes", [])),
        )


def positive_gap(target: dict[str, float], current: dict[str, float]) -> dict[str, float]:
    """Target − current, keeping only positive (under-target) entries."""
    return {k: round(t - current.get(k, 0), 3) for k, t in target.items() if t - current.get(k, 0) > 1e-9}


def positive_cap(current: dict[str, float], limit: dict[str, float]) -> dict[str, float]:
    """Current − limit, keeping only positive (over-limit) entries."""
    return {k: round(current.get(k, 0) - lim, 3) for k, lim in limit.items() if current.get(k, 0) - lim > 1e-9}
