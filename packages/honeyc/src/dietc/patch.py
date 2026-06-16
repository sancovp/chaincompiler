"""Greedy patch planner: pick modules that close gaps without violating caps."""
from __future__ import annotations

import math

from .models import GoalProfile, PatchModule, PatchRecommendation

_NUTRIENT_LABEL = {
    "protein_g": "protein", "fiber_g": "fiber", "omega3_g": "omega-3",
    "potassium_mg": "potassium", "magnesium_mg": "magnesium", "calcium_mg": "calcium",
}


def plan(
    gaps: dict[str, float],
    caps: dict[str, float],
    matrix_gaps: dict[str, float],
    modules: dict[str, PatchModule],
    profile: GoalProfile,
    *,
    max_modules: int = 6,
) -> list[PatchRecommendation]:
    remaining_n = dict(gaps)
    remaining_m = dict(matrix_gaps)
    prefs = profile.preferences
    chosen: list[PatchRecommendation] = []
    available = dict(modules)

    while available and (remaining_n or remaining_m) and len(chosen) < max_modules:
        best_id, best_score, best = None, 0.0, None
        for mid, m in available.items():
            score = _score(m, remaining_n, remaining_m, caps, prefs)
            if score > best_score:
                best_id, best_score, best = mid, score, m
        if best is None:
            break
        available.pop(best_id)
        rec = _recommend(best, remaining_n, remaining_m, prefs)
        chosen.append(rec)
        # subtract contribution at the chosen dose
        contributes = best.contributes.scale(rec.dose).to_dict()
        matrix = best.matrix.scale(rec.dose).to_dict()
        for k, v in contributes.items():
            if k in remaining_n:
                remaining_n[k] = max(0.0, remaining_n[k] - v)
                if remaining_n[k] <= 1e-9:
                    remaining_n.pop(k)
        for k, v in matrix.items():
            if k in remaining_m:
                remaining_m[k] = max(0.0, remaining_m[k] - v)
                if remaining_m[k] <= 1e-9:
                    remaining_m.pop(k)
    return chosen


def _adds_to_capped(module: PatchModule, caps: dict[str, float]) -> bool:
    contributes = module.contributes.to_dict()
    return any(contributes.get(k, 0) > 0 for k in caps)


def _score(module: PatchModule, gaps, matrix_gaps, caps, prefs) -> float:
    contributes = module.contributes.to_dict()
    matrix = module.matrix.to_dict()
    gap_cover = sum(1 for k in gaps if contributes.get(k, 0) > 0)
    matrix_cover = sum(1 for k in matrix_gaps if matrix.get(k, 0) > 0)
    score = 2.0 * gap_cover + 1.5 * matrix_cover + module.adherence_score - module.cost_score
    if _adds_to_capped(module, caps):
        score -= 3.0
    if prefs.get("avoid_high_sodium_patches") and contributes.get("sodium_mg", 0) > 50:
        score -= 2.0
    if prefs.get("prefer_drinks") and module.category == "drink":
        score += 0.5
    if prefs.get("prefer_low_prep") and module.category in ("drink", "capsule", "bar", "powder"):
        score += 0.3
    return score


def _recommend(module: PatchModule, gaps, matrix_gaps, prefs) -> PatchRecommendation:
    contributes = module.contributes.to_dict()
    matrix = module.matrix.to_dict()
    addressed_n = [k for k in gaps if contributes.get(k, 0) > 0]
    addressed_m = [k for k in matrix_gaps if matrix.get(k, 0) > 0]

    # meter dose to the largest nutrient gap it covers, clamped to the module's range
    dose = module.dose_step or 1
    if addressed_n:
        needs = max(gaps[k] / contributes[k] for k in addressed_n)
        steps = max(1, math.ceil(needs / (module.dose_step or 1)))
        dose = min(module.dose_max, steps * (module.dose_step or 1))
    dose = max(dose, module.dose_min or 0) or (module.dose_step or 1)

    reasons: list[str] = []
    if addressed_n:
        names = ", ".join(_NUTRIENT_LABEL.get(k, k) for k in addressed_n)
        reasons.append(f"improves {names} (below target)")
    if addressed_m:
        reasons.append("improves plant/color/polyphenol matrix coverage")
    if prefs.get("avoid_high_sodium_patches") and contributes.get("sodium_mg", 0) <= 50 and "potassium_mg" in addressed_n:
        reasons.append("adds potassium without adding sodium")
    if not reasons:
        reasons.append("supports overall coverage")
    return PatchRecommendation(
        module_id=module.id,
        name=module.name,
        dose=dose,
        unit=module.unit,
        reasons=reasons,
        warnings=list(module.warnings),
    )
