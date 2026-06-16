from __future__ import annotations

import tempfile
from pathlib import Path

from rulecatcher.db import connect, list_rules

from chaincompiler.bridge import compile_chain, gate, learn
from chaincompiler.prime import build_prime

SEED = [
    "[Observe] ⇒ [Frame] ⇒ [Integrate] ⇒ [Authenticate] ⇒ |Predict|",
    "[Observe] ⇒ [Frame] ⇒ [Cohere] ⇒ [Authenticate] ⇒ |Predict|",
    "[Observe] ⇒ [Frame] ⇒ [Integrate] ⇒ [Lever] ⇒ |Predict|",
]


def _db(tmp):
    return str(Path(tmp) / "t.db")


def test_learn_ratifies_shape_grammar():
    with tempfile.TemporaryDirectory() as tmp, connect(_db(tmp)) as cx:
        adopted = learn(cx, SEED, scope="cor")
        assert adopted
        # shape-only: every adopted rule is a kind rule, none pin vocabulary
        assert all(r["rule_type"] == "next_kind" for r in adopted)


def test_gate_passes_new_vocabulary_in_grammar():
    # a chain with step names never seen in the seed must still pass — it's a
    # notation (shape), not a fixed vocabulary.
    with tempfile.TemporaryDirectory() as tmp, connect(_db(tmp)) as cx:
        learn(cx, SEED, scope="cor")
        violations, _ = gate(cx, "[Scan] ⇒ [Map] ⇒ [Decide] ⇒ |Predict|", scope="cor")
        assert violations == []


def test_gate_catches_missing_connector():
    with tempfile.TemporaryDirectory() as tmp, connect(_db(tmp)) as cx:
        learn(cx, SEED, scope="cor")
        violations, fixes = gate(cx, "[Observe] [Frame] ⇒ |Predict|", scope="cor")
        assert violations
        assert any("⇒" in f.candidate_tokens for f in fixes)


def test_compile_chain_yields_produces_and_bounded():
    c = compile_chain(SEED[0])
    assert "Observe produces Frame" in c["triples"]
    assert "Predict bounded true" in c["triples"]


def test_prime_contains_grammar_and_compiled_meaning():
    with tempfile.TemporaryDirectory() as tmp, connect(_db(tmp)) as cx:
        learn(cx, SEED, scope="cor")
        adopted = list_rules(cx, "adopted", scope="cor")
        block = build_prime("cor", adopted, SEED[0])
    assert "Ratified grammar" in block
    assert "produces" in block
    assert "|Predict|" in block
    assert "Directive" in block


def test_loop_grammar_is_stable_under_new_vocabulary():
    # closing the loop: fold a gated-clean new chain back in and re-learn;
    # the shape grammar must NOT grow just because new step names appeared.
    with tempfile.TemporaryDirectory() as tmp, connect(_db(tmp)) as cx:
        first = learn(cx, SEED, scope="cor")
        again = learn(cx, ["[Scan] ⇒ [Map] ⇒ [Decide] ⇒ |Predict|"], scope="cor", label="round2")
        assert len(again) == len(first)
