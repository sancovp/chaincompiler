"""Render a DayState as Dense Rune-Chain notation (optionally via HoneyC)."""
from __future__ import annotations

import re

from .models import DayState

_GAP_LABEL = {
    "protein_g": "Protein", "fiber_g": "Fiber", "omega3_g": "Omega3",
    "potassium_mg": "Potassium", "magnesium_mg": "Magnesium", "calcium_mg": "Calcium",
    "calories": "Calories",
}
_MATRIX_LABEL = {
    "plant_diversity_score": "MatrixDiversity", "color_diversity_score": "MatrixColor",
    "berry_count": "Berry", "green_leafy_count": "Greens", "polyphenol_score": "Polyphenol",
}
_CAP_LABEL = {"added_sugar_g": "AddedSugar", "sodium_mg": "Sodium", "saturated_fat_g": "SatFat"}


def _camel(name: str) -> str:
    parts = [p for p in re.split(r"[-_\s]+", name.strip()) if p]
    if len(parts) <= 1:
        return parts[0] if parts else ""   # preserve existing case, e.g. PotatoDay
    return "".join(p[:1].upper() + p[1:] for p in parts)


def render_rune(state: DayState) -> str:
    gap_terms = [_GAP_LABEL.get(k, _camel(k)) for k in state.gaps]
    gap_terms += [_MATRIX_LABEL.get(k, _camel(k)) for k in state.matrix_gaps]
    cap_terms = [_CAP_LABEL.get(k, _camel(k)) for k in state.caps] or \
                [_CAP_LABEL[k] for k in _CAP_LABEL if k in _near(state)]
    patch_terms = [_camel(r.name) for r in state.patches]

    lines = [f"[{_camel(state.label)}]", "  ⇢ CurrentVector"]
    if gap_terms:
        lines.append("  ⇒ ΔGap:{" + ",".join(gap_terms) + "}")
    if cap_terms:
        lines.append("  ∧ CapWatch:{" + ",".join(cap_terms) + "}")
    if patch_terms:
        lines.append("  ⇒ Patch:{" + ",".join(patch_terms) + "}")
    lines.append("  ⇒ |ImprovedPattern|")
    return "\n".join(lines)


def _near(state: DayState) -> set[str]:
    # cap keys mentioned in warnings (approaching limit) so CapWatch is non-empty
    near: set[str] = set()
    for w in state.warnings:
        for key in _CAP_LABEL:
            if key in w:
                near.add(key)
    return near


def render_rune_block(state: DayState) -> str:
    """A scoped [DietCompiler]:{...} block, valid HoneyC notation."""
    inputs = ",".join(_camel(i) for i in dict.fromkeys(e.item_id for e in state.events))
    patches = ",".join(_camel(r.name) for r in state.patches) or "None"
    gap = ",".join(_GAP_LABEL.get(k, _camel(k)) for k in state.gaps) or "None"
    return (
        "[DietCompiler]:{\n"
        f"  [Input]:{{{inputs}}},\n"
        "  [Estimate]:Input ⇢ NutrientVector,\n"
        f"  [Compare]:DayState ⇔ GoalProfile ⇒ Gap,\n"
        f"  [PatchSelect]:Gap ⇒ {{{patches}}},\n"
        "  [Output] ⇒ |ImprovedPattern|\n"
        "}"
    )


def render_via_honeyc(state: DayState, mode: str = "readable") -> str | None:
    """Pass the rune block through HoneyC if it is importable."""
    try:
        from honeyc.parser import parse_text
        from honeyc.render import render
    except Exception:
        return None
    try:
        return render(parse_text(render_rune_block(state)), mode)
    except Exception:
        return None
