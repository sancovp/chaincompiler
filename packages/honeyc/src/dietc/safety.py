"""Conservative software warnings. NOT medical advice."""
from __future__ import annotations

from collections import Counter

from .models import GoalProfile, PatchModule, PatchRecommendation

_FIBER_RAMP_THRESHOLD = 15.0  # grams of patched fiber in one day


def check(
    recommendations: list[PatchRecommendation],
    modules: dict[str, PatchModule],
    caps: dict[str, float],
    profile: GoalProfile,
) -> list[str]:
    warnings: list[str] = []

    # fiber added too quickly via patches
    patched_fiber = sum(
        modules[r.module_id].contributes.fiber_g * r.dose
        for r in recommendations
        if r.module_id in modules
    )
    if patched_fiber >= _FIBER_RAMP_THRESHOLD:
        warnings.append(f"patches add ~{patched_fiber:.0f} g fiber in one day; increase fiber gradually.")

    # high-sodium patch while a sodium cap exists
    if "sodium_mg" in caps:
        for r in recommendations:
            m = modules.get(r.module_id)
            if m and m.contributes.sodium_mg * r.dose > 50:
                warnings.append(f"{m.name} adds sodium while sodium is already at/over its cap.")

    # sugar-alcohol risk surfaced by module metadata
    for r in recommendations:
        m = modules.get(r.module_id)
        if m and any("sugar alcohol" in w.lower() for w in m.warnings):
            warnings.append(f"{m.name} may contain sugar alcohols (possible GI discomfort).")

    # duplicate supplement categories
    cats = Counter(modules[r.module_id].category for r in recommendations if r.module_id in modules)
    for cat, n in cats.items():
        if cat in ("capsule", "pill", "powder") and n > 1:
            warnings.append(f"multiple '{cat}' supplement modules selected; check for overlap.")

    # supplement module used without a configured profile
    if not profile.upper_limits.to_dict() or all(v == 0 for v in profile.upper_limits.to_dict().values()):
        if any(modules.get(r.module_id) and modules[r.module_id].category in ("capsule", "pill") for r in recommendations):
            warnings.append("supplement modules selected without configured upper limits in the profile.")

    return warnings
