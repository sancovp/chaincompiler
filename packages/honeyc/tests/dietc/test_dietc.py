from __future__ import annotations

from pathlib import Path
EX = Path(__file__).resolve().parents[2] / "examples" / "dietc"

from dietc.engine import compile_day
from dietc.load import load_day, load_items, load_modules, load_profile
from dietc.render import render_prose
from dietc.rune import render_rune, render_via_honeyc


def _modules():
    return load_modules(EX / "patch_modules.yaml")


def _profile():
    return load_profile(EX / "default_profile.yaml")


# --- loading ---

def test_load_items():
    items = load_items(EX / "items.yaml")
    assert "potato_base" in items
    assert items["potato_base"].nutrient_vector.potassium_mg == 900


def test_load_profile():
    p = _profile()
    assert p.targets.protein_g == 120
    assert p.upper_limits.sodium_mg == 2300


def test_load_modules():
    m = _modules()
    assert "protein_fiber_bar" in m
    assert m["protein_fiber_bar"].contributes.protein_g == 20


def test_load_day():
    events, items_file, label = load_day(EX / "potato_day.yaml")
    assert len(events) == 2
    assert items_file == "items.yaml"
    assert label == "PotatoDay"


# --- engine: totals, gaps, caps ---

def test_compute_totals():
    state = compile_day(EX / "potato_day.yaml", _profile())
    # 2 potatoes (160 each) + 1 sauce (200) = 520 kcal
    assert state.nutrient_totals.calories == 520
    assert state.nutrient_totals.protein_g == 8  # 2 * 4


def test_detect_protein_gap():
    state = compile_day(EX / "potato_day.yaml", _profile())
    assert "protein_g" in state.gaps


def test_detect_matrix_gap():
    state = compile_day(EX / "potato_day.yaml", _profile())
    assert state.matrix_gaps  # potato day has poor matrix diversity


def test_detect_omega3_gap():
    state = compile_day(EX / "potato_day.yaml", _profile())
    assert "omega3_g" in state.gaps


# --- patch planner ---

def test_recommend_protein_fiber_bar():
    state = compile_day(EX / "potato_day.yaml", _profile(), _modules())
    assert any(r.module_id == "protein_fiber_bar" for r in state.patches)


def test_recommend_omega3_capsule():
    state = compile_day(EX / "potato_day.yaml", _profile(), _modules())
    assert any(r.module_id == "omega3_capsule" for r in state.patches)


def test_recommend_matrix_foods():
    state = compile_day(EX / "potato_day.yaml", _profile(), _modules())
    ids = {r.module_id for r in state.patches}
    assert "berry_thing" in ids or "green_thing" in ids


def test_patches_have_reasons():
    state = compile_day(EX / "potato_day.yaml", _profile(), _modules())
    assert state.patches
    assert all(r.reasons for r in state.patches)


def test_no_patch_violates_sodium_cap_silently():
    # electrolyte_water adds no sodium; the planner should prefer it for potassium
    state = compile_day(EX / "potato_day.yaml", _profile(), _modules())
    assert any(r.module_id == "electrolyte_water" for r in state.patches)


# --- renderers ---

def test_render_rune():
    state = compile_day(EX / "potato_day.yaml", _profile(), _modules())
    out = render_rune(state)
    assert "[PotatoDay]" in out
    assert "ΔGap:{" in out
    assert "Patch:{" in out
    assert "|ImprovedPattern|" in out


def test_render_prose_explains_patches():
    state = compile_day(EX / "potato_day.yaml", _profile(), _modules())
    out = render_prose(state)
    assert "Recommended patches:" in out
    assert "Protein Fiber Bar" in out
    assert "protein" in out.lower()


def test_rune_through_honeyc_is_valid():
    # the generated rune block must parse + render through HoneyC
    state = compile_day(EX / "potato_day.yaml", _profile(), _modules())
    out = render_via_honeyc(state)
    assert out is not None
    assert "DietCompiler" in out
