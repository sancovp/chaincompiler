"""Container models for DietC."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .vectors import MatrixVector, NutrientVector, SafetyVector


@dataclass
class IntakeItem:
    id: str
    name: str
    category: str
    nutrient_vector: NutrientVector
    matrix_vector: MatrixVector
    safety_vector: SafetyVector
    serving_size: float = 1
    serving_unit: str = "serving"
    tags: list[str] = field(default_factory=list)
    confidence: float = 1.0


@dataclass
class IntakeEvent:
    item_id: str
    amount: float = 1
    unit: str = "serving"
    timestamp: str | None = None
    notes: str | None = None


@dataclass
class GoalProfile:
    id: str
    name: str
    targets: NutrientVector
    upper_limits: NutrientVector
    minimum_matrix: MatrixVector
    preferences: dict[str, Any] = field(default_factory=dict)
    constraints: dict[str, Any] = field(default_factory=dict)


@dataclass
class PatchModule:
    id: str
    name: str
    category: str
    contributes: NutrientVector
    matrix: MatrixVector
    avoids: list[str] = field(default_factory=list)
    dose_min: float = 0
    dose_max: float = 1
    dose_step: float = 1
    unit: str = "serving"
    tags: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    cost_score: float = 0
    adherence_score: float = 0


@dataclass
class PatchRecommendation:
    module_id: str
    name: str
    dose: float
    unit: str
    reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass
class DayState:
    events: list[IntakeEvent]
    nutrient_totals: NutrientVector
    matrix_totals: MatrixVector
    safety_state: SafetyVector
    gaps: dict[str, float] = field(default_factory=dict)
    caps: dict[str, float] = field(default_factory=dict)
    matrix_gaps: dict[str, float] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    patches: list[PatchRecommendation] = field(default_factory=list)
    label: str = "Day"
