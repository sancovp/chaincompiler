"""Metaformal self-tests for the nutrition AIOS (the dietc → chaincompiler-built recursion).

NOT unit tests with predicted values — these **trigger the real build + the real dietc pipeline in
the real substrate and OBSERVE the state-change** (the emitted AIOS dir; a real gap/cap number). The
substrate is the oracle. If these go green once, they're frozen: history is the warrant.

Run:  pytest examples/nutrition/test_nutrition_aios.py     (after ./install.sh)
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build import build  # noqa: E402

from chaincompiler.gba import load_gba, search  # noqa: E402

import dietc  # noqa: E402
from dietc import engine, load  # noqa: E402

FIX = Path(dietc.__file__).resolve().parents[2] / "examples" / "dietc"


def test_nutrition_aios_emits_closed_and_safe(tmp_path):
    """Observe the emitted AIOS: it closes, validates, carries the safety rule, and the
    compile-day pipeline + the gap/cap/safety ACs are coord-addressed in the tree."""
    g = build(tmp_path / "aios")

    # closure: the algebra rolled up and the tree validates (no violations)
    assert g.closed is True
    assert g.report.get("violations") == 0

    # the persona + the safety frame are on disk
    role = g.claude_md.read_text()
    assert "NutritionBandit" in role
    assert "NOT medical advice" in role
    safety = (g.rules_dir / "90-safety.md").read_text()
    assert "safety.check" in safety

    # the pipeline + decision are placed in the tree, coord-addressed and searchable
    g2 = load_gba(g.root)
    coords = {h["name"]: h.get("coord") for h in search(g2, "compile day pipeline recommend gaps caps", limit=8)}
    assert any("compile-day" in n for n in coords), coords
    assert any("recommend" in n for n in coords), coords
    # an AC frame (gap/cap/safety attention) is reachable too
    acs = [h["name"] for h in search(g2, "attention attend nutrition", limit=8)]
    assert any("attention" in n for n in acs), acs


def test_real_day_compiles_through_the_tools():
    """Observe a REAL computation: walk the compile-day pipeline's tool calls on the PotatoDay
    fixture (the dietc Python doing the math) and read the gaps/caps/warnings it returns.
    No predicted value asserted — only that the substrate produced a real, non-trivial reading
    and that the safety check actually fired."""
    profile = load.load_profile(FIX / "default_profile.yaml")
    modules = load.load_modules(FIX / "patch_modules.yaml")
    items = load.load_items(FIX / "items.yaml")

    state = engine.compile_day(FIX / "potato_day.yaml", profile, modules, items_override=items)

    # the tools produced a real reading (the oracle): a positive calorie gap on a potato-only day
    assert state.gaps, "expected gaps from the day"
    assert state.gaps.get("calories", 0) > 0
    # the recommend step chose patches that fill gaps
    assert state.patches, "expected patch recommendations"
    # safety actually ran and surfaced at least one warning (it never gets silently skipped)
    assert state.warnings, "expected safety.check to surface warnings"
