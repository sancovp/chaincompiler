"""Prose rendering of a DayState."""
from __future__ import annotations

from .models import DayState

_GAP_WORD = {
    "protein_g": "protein", "fiber_g": "fiber", "omega3_g": "omega-3",
    "potassium_mg": "potassium", "magnesium_mg": "magnesium", "calcium_mg": "calcium",
    "calories": "calories",
}
_MATRIX_WORD = {
    "plant_diversity_score": "plant diversity", "color_diversity_score": "color diversity",
    "berry_count": "berries", "green_leafy_count": "leafy greens", "polyphenol_score": "polyphenols",
}


def render_prose(state: DayState) -> str:
    # opening inline sentences
    sentences: list[str] = []
    items = ", ".join(dict.fromkeys(e.item_id.replace("_", " ") for e in state.events))
    sentences.append(f"This day ({state.label}) is built from {items}.")

    short = [_GAP_WORD.get(k, k) for k in state.gaps] + [_MATRIX_WORD.get(k, k) for k in state.matrix_gaps]
    if short:
        sentences.append("It remains low in " + _join(short) + ".")
    if state.caps:
        sentences.append("It exceeds limits on " + _join(list(state.caps)) + ".")

    blocks: list[str] = [" ".join(sentences)]

    if state.patches:
        lines = ["Recommended patches:"]
        for i, r in enumerate(state.patches, 1):
            warn = (" " + " ".join(r.warnings)) if r.warnings else ""
            lines.append(f"{i}. {r.name} ({r.dose:g} {r.unit}): {'; '.join(r.reasons)}.{warn}")
        blocks.append("\n".join(lines))

    if state.warnings:
        blocks.append("Warnings:\n" + "\n".join(f"- {w}" for w in state.warnings))

    return "\n\n".join(blocks)


def _join(words: list[str]) -> str:
    words = list(dict.fromkeys(words))
    if len(words) == 1:
        return words[0]
    return ", ".join(words[:-1]) + f", and {words[-1]}"
