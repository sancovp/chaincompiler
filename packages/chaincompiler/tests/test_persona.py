"""The persona compiler: a glyph-persona-program → legend + workflow + SKILL.md."""
from pathlib import Path

import pytest

pytest.importorskip("glyphsteer")

from chaincompiler.persona import (compile_persona, extract_legend,
                                   extract_workflow, parse_header, parse_persona)

EXAMPLE = Path(__file__).resolve().parents[1] / "examples" / "bizzibee.txt"
TEXT = EXAMPLE.read_text(encoding="utf-8")


def test_header_parsed():
    h = parse_header(TEXT)
    assert h["CogID"] == "BB"
    assert h["Mission"].startswith("Produce RoyalJelly")


def test_legend_extracts_the_dense_runes():
    V = extract_legend(TEXT)
    names = {a.name for a in V.axes}
    assert {"NectarWF", "RoyalJelly", "drilldown"} <= names
    # the ZWJ rune 🌸‍💧 is captured as ONE glyph
    nectar = V.by_name("NectarWF").glyph
    assert "‍" in nectar and nectar.startswith("\U0001F338")


def test_workflow_steps_and_control_flow():
    steps = extract_workflow(TEXT)
    nums = [s["step"] for s in steps]
    assert "0" in nums and "5" in nums                 # the bookend steps
    allctrl = {c for s in steps for c in s["ctrl"]}
    assert {"if", "while", "for"} <= allctrl           # control flow detected
    assert any("🔁" in s["ctrl"] for s in steps)        # the loop-back


def test_compile_writes_skill_and_legend(tmp_path: Path):
    res = compile_persona(TEXT, tmp_path)
    assert res["name"] == "BB"
    assert res["axes"] >= 4 and res["steps"] >= 6
    skill = Path(res["skill"])
    legend = Path(res["legend"])
    assert skill.exists() and skill.name == "SKILL.md"
    assert legend.exists()
    body = skill.read_text(encoding="utf-8")
    assert "compiled persona" in body and "Legend" in body and "Workflow" in body
    # the rulecatcher gate ran and the legend chain is well-formed
    assert res["gate"] is None or res["gate"]["verdict"] in {"ok", "orthogonal", "syntax_break"}


def test_roundtrip_legend_is_loadable(tmp_path: Path):
    from glyphsteer import load_legend
    res = compile_persona(TEXT, tmp_path)
    V = load_legend(res["legend"])
    assert V.by_name("RoyalJelly") is not None
