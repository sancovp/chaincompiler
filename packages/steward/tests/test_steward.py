"""The Steward base + hierarchy: O/F/I/A/P loop, the A-lock warrant, the MetaSteward."""
import pytest

from steward import (Artifact, Steward, Task, Verdict, Warrant, always, chain_steward,
                     compiler_steward, core_steward, meta_steward, non_empty, shape,
                     sm_steward)


def _const_maker(body):
    return lambda task: Artifact(task.goal.replace(" ", "-"), "x", body)


def test_loop_runs_ofiap_and_admits_on_warrant_pass():
    st = Steward("x", non_empty(), _const_maker("hello"))
    r = st.run(Task("make a thing"))
    assert r.admitted and r.artifact.body == "hello"
    # the trace shows the full O/F/I/A/P with the A-lock
    joined = " ".join(r.trace)
    assert "O observe" in joined and "A lock" in joined and "P predict" in joined


def test_warrant_reject_blocks_admission():
    st = Steward("x", shape(r"WIDGET"), _const_maker("nope"))
    r = st.run(Task("make"))
    assert not r.admitted and r.artifact is None
    assert "does not match" in r.verdict.reason


def test_warrant_tier_is_on_the_ladder():
    assert non_empty().tier == "proto_soma"
    assert shape("x").tier == "proto_soma"


def test_specialist_stewards_make_their_part_kind():
    assert chain_steward().run(Task("c", {"links": ["a", "b"]})).artifact.body == "a → b"
    sm = sm_steward().run(Task("s", {"steps": [{"id": "boot", "gate": "MERGE"}]}))
    assert "boot" in sm.artifact.body and sm.artifact.kind == "sm"
    comp = compiler_steward().run(Task("k", {"calls": ["sm1", "sm2"]}))
    assert "sm1" in comp.artifact.body and comp.artifact.kind == "compiler"
    core = core_steward().run(Task("o", {"sequence": ["dayA", "nightB"]}))
    assert "0: dayA" in core.artifact.body and core.artifact.kind == "core"


def test_meta_steward_presents_as_one_runs_many():
    # a Core built from a chain-Steward then an sm-Steward (reads as one workflow)
    meta = meta_steward("build-core", [chain_steward(), sm_steward()])
    r = meta.run(Task("assemble", {"links": ["x", "y"], "steps": [{"id": "s0"}]}))
    assert r.admitted
    assert r.artifact.kind == "workflow"
    assert r.artifact.meta["presents_as"] == "1 LLM"
    assert r.artifact.meta["sub"] == ["chain", "sm"]        # ran two autonomous Stewards
    assert "x → y" in r.artifact.body and "s0" in r.artifact.body


def test_meta_steward_is_homoiconic_nests():
    inner = meta_steward("inner", [chain_steward()])
    outer = meta_steward("outer", [inner, sm_steward()])    # a Steward of Stewards-of-Stewards
    r = outer.run(Task("nest", {"links": ["a"], "steps": [{"id": "z"}]}))
    assert r.admitted and "workflow" in r.artifact.meta["sub"]


def test_warrant_upgrade_to_grammar_tier():
    # the same Steward loop, warrant swapped from proto_soma → grammar (rulecatcher).
    pytest.importorskip("glyphsteer")
    pytest.importorskip("chaincompiler")
    from steward import glyph_grammar
    from glyphsteer import SENTIMENT
    POS, URG = SENTIMENT.by_name("positive").glyph, SENTIMENT.by_name("urgent").glyph
    w = glyph_grammar(SENTIMENT)
    assert w.tier == "grammar"
    st = Steward("chain", w, lambda t: Artifact(t.goal, "chain", "x",
                                                meta={"code": t.params["code"]}))
    assert st.run(Task("c", {"code": SENTIMENT.code([POS, URG])})).admitted          # ok
    rev = st.run(Task("r", {"code": URG + POS}))                                      # orthogonal
    assert rev.admitted and rev.artifact.meta["code"] == SENTIMENT.code([POS, URG])   # canonicalized
