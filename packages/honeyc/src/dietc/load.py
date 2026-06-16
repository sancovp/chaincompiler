"""Load DietC items, profiles, patch modules, and day logs from YAML/JSON."""
from __future__ import annotations

from pathlib import Path

import yaml

from .models import GoalProfile, IntakeEvent, IntakeItem, PatchModule
from .vectors import MatrixVector, NutrientVector, SafetyVector


def _read(path: Path | str) -> dict:
    return yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}


def load_items(path: Path | str) -> dict[str, IntakeItem]:
    data = _read(path)
    items: dict[str, IntakeItem] = {}
    for raw in data.get("items", []):
        item = IntakeItem(
            id=raw["id"],
            name=raw.get("name", raw["id"]),
            category=raw.get("category", "unknown"),
            serving_size=float(raw.get("serving_size", 1)),
            serving_unit=raw.get("serving_unit", "serving"),
            nutrient_vector=NutrientVector.from_dict(raw.get("nutrient_vector")),
            matrix_vector=MatrixVector.from_dict(raw.get("matrix_vector")),
            safety_vector=SafetyVector.from_dict(raw.get("safety_vector")),
            tags=list(raw.get("tags", [])),
            confidence=float(raw.get("confidence", 1.0)),
        )
        items[item.id] = item
    return items


def load_profile(path: Path | str) -> GoalProfile:
    data = _read(path)
    return GoalProfile(
        id=data.get("id", "profile"),
        name=data.get("name", "Profile"),
        targets=NutrientVector.from_dict(data.get("targets")),
        upper_limits=NutrientVector.from_dict(data.get("upper_limits")),
        minimum_matrix=MatrixVector.from_dict(data.get("minimum_matrix")),
        preferences=dict(data.get("preferences", {})),
        constraints=dict(data.get("constraints", {})),
    )


def load_modules(path: Path | str) -> dict[str, PatchModule]:
    data = _read(path)
    modules: dict[str, PatchModule] = {}
    for raw in data.get("modules", []):
        module = PatchModule(
            id=raw["id"],
            name=raw.get("name", raw["id"]),
            category=raw.get("category", "unknown"),
            contributes=NutrientVector.from_dict(raw.get("contributes")),
            matrix=MatrixVector.from_dict(raw.get("matrix")),
            avoids=list(raw.get("avoids", [])),
            dose_min=float(raw.get("dose_min", 0)),
            dose_max=float(raw.get("dose_max", 1)),
            dose_step=float(raw.get("dose_step", 1)),
            unit=raw.get("unit", "serving"),
            tags=list(raw.get("tags", [])),
            warnings=list(raw.get("warnings", [])),
            cost_score=float(raw.get("cost_score", 0)),
            adherence_score=float(raw.get("adherence_score", 0)),
        )
        modules[module.id] = module
    return modules


def load_day(path: Path | str) -> tuple[list[IntakeEvent], str | None, str]:
    """Return (events, items_file (relative), label)."""
    data = _read(path)
    events = [
        IntakeEvent(
            item_id=e["item_id"],
            amount=float(e.get("amount", 1)),
            unit=e.get("unit", "serving"),
            timestamp=e.get("timestamp"),
            notes=e.get("notes"),
        )
        for e in data.get("events", [])
    ]
    label = data.get("label") or Path(path).stem.replace("_", " ").title().replace(" ", "")
    return events, data.get("items_file"), label
