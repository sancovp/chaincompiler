"""ACCC tests: forging distinct languages, compiling, and gating."""
from __future__ import annotations

from pathlib import Path

from accc import attention_block, forge, gate, parse_ac
from accc.notation import DEBUG_AC, GENERIC_AC


def test_parse_ac_extracts_foci_and_held():
    foci, held = parse_ac("[Symptom] ⇒ [Repro] ⇒ [Hypothesis] ⇒ |Localize|")
    assert foci == ["Symptom", "Repro", "Hypothesis"]
    assert held == "Localize"


def test_attention_block_renders_ordered_foci():
    block = attention_block("debug", "[Symptom] ⇒ [Repro] ⇒ |Localize|")
    assert "1. Symptom" in block
    assert "2. Repro" in block
    assert "Hold: Localize" in block


def test_forge_two_distinct_languages(tmp_path: Path):
    db = str(tmp_path / "ac.db")
    generic = forge("generic", GENERIC_AC, db=db)
    debug = forge("debug", DEBUG_AC, db=db, strict=True)
    assert generic.scope != debug.scope
    assert generic.rule_count > 0 and debug.rule_count > 0


def test_strict_debug_language_gates_off_domain_chain(tmp_path: Path):
    db = str(tmp_path / "ac.db")
    debug = forge("debug", DEBUG_AC, db=db, strict=True)
    # valid debug chain passes
    ok, _ = gate(debug, "[Symptom] ⇒ [Repro] ⇒ [Diff] ⇒ |Localize|")
    assert ok == []
    # off-domain planning chain is rejected by the pinned vocabulary
    bad, _ = gate(debug, "[Goal] ⇒ [Constraints] ⇒ [Evidence] ⇒ |Plan|")
    assert bad, "strict debug language should reject off-domain foci"


def test_shape_only_language_accepts_any_vocabulary(tmp_path: Path):
    db = str(tmp_path / "ac.db")
    generic = forge("generic", GENERIC_AC, db=db)  # shape only
    # a novel-vocabulary chain of the same SHAPE should pass
    ok, _ = gate(generic, "[Aim] ⇒ [Limits] ⇒ [Facts] ⇒ |Sketch|")
    assert ok == []
