"""Metaformal self-test (frozen): the STRICT gate rejects foreign tokens at branch points.

A metaformal self-test caught the plain gate ADMITTING a foreign token `❌NOPE❌` (it's positional /
rule-triggered, and the position after `⇒` is a genuine branch point no confidence rule governs). The
fix: an opt-in closed-class vocabulary check (`gate(..., strict=True)`). This OBSERVES the fixed gate's
real verdicts — the substrate is the oracle. See ~/.claude/skills/metaformal-self-test.
"""
from __future__ import annotations

import tempfile
from pathlib import Path

from rulecatcher.db import connect
from chaincompiler.bridge import learn, gate

_EXAMPLES = ["[ac:a] ⇒ [cor:b] ⇒ |C|", "[ac:a] ⇒ [ac:b] ⇒ [cor:c] ⇒ |D|"]


def _gate(chain: str, *, strict: bool):
    db = str(Path(tempfile.mkdtemp()) / "g.db")
    with connect(db) as cx:
        learn(cx, _EXAMPLES, scope="cog")
        viol, _ = gate(cx, chain, scope="cog", strict=strict)
    return viol


def test_strict_gate_rejects_foreign_token_at_a_branch_point():
    # OBSERVE: the foreign token is admitted plain (the gap), rejected strict (the fix)
    assert len(_gate("[ac:x] ⇒ ❌NOPE❌ ⇒ |Z|", strict=False)) == 0      # the documented gap
    assert len(_gate("[ac:x] ⇒ ❌NOPE❌ ⇒ |Z|", strict=True)) >= 1       # the fix: REJECT


def test_strict_gate_still_admits_a_valid_chain():
    # the fix must not false-positive a well-formed chain
    assert len(_gate("[ac:x] ⇒ [cor:y] ⇒ |Z|", strict=True)) == 0


def test_strict_gate_still_catches_structural_errors():
    # missing arrows are caught by the positional rules, strict or not
    assert len(_gate("[ac:x] [cor:y] |Z|", strict=True)) >= 1
