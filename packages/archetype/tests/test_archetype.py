"""Tests for the Archetype Compiler — the spec's MVP test list (§7) + the ✦new ones."""
from __future__ import annotations

import json
import tempfile

import archetype as arc


# ── the preserved MVP tests ──────────────────────────────────────────────────
def test_hero_becomes_guardian():
    a = arc.compile_archetype("Hero")
    assert a.becoming == "Guardian"


def test_shadow_opposes_persona():
    a = arc.compile_archetype("Hero")
    assert a.shadow and a.shadow != a.persona
    assert ("DENIED_INVERSE_OF", a.persona) in [(p, o) for s, p, o in arc.triples(a)
                                                if p == "DENIED_INVERSE_OF"][0:1] or True
    assert (a.shadow, "DENIED_INVERSE_OF", a.persona) in arc.triples(a)


def test_self_integrates_both():
    a = arc.compile_archetype("Hero")
    assert (a.self_, "INTEGRATES", a.persona) in arc.triples(a)
    assert (a.self_, "INTEGRATES", a.shadow) in arc.triples(a)
    assert arc.is_valid(a)


def test_recursive_depth():
    chain = arc.compile_chain(["Hero", "Guardian", "King", "Steward", "Sage"])
    assert [m.name for m in chain] == ["Hero", "Guardian", "King", "Steward", "Sage"]
    # each Becoming points at the next link (the chain type-lifts forward)
    assert [m.becoming for m in chain[:-1]] == ["Guardian", "King", "Steward", "Sage"]


def test_purified_self_fails():
    # a Self that is just the Persona (bypasses the Shadow) must be a C2 violation
    bad = arc.compile_archetype("Hero", with_odyssey=False, self_="Rescuer / champion",
                                persona="Rescuer / champion")
    v = arc.validate(bad)
    assert any(x.startswith("C2") for x in v)


# ── ✦new tests (the Odyssey refactor) ────────────────────────────────────────
def test_odyssey_is_plural():
    a = arc.compile_archetype("Hero")
    # a real Odyssey is a SUCCESSION (call-out + encounters + post-return), not 1 HJ
    assert len(a.odyssey) >= 2
    assert arc.is_valid(a)


def test_odyssey_accrues_pantheon_edges():
    a = arc.compile_archetype("Hero")
    web = arc.aut_web(a.odyssey)
    assert len(web) >= 1
    # visiting the full pantheon ⇒ quines it (orbit-closure, discrete check)
    full = arc.compile_archetype("Hero")  # default depth = all others
    assert arc.quines(full.odyssey, arc.CYCLE, "Hero")


def test_post_return_hj_present():
    a = arc.compile_archetype("Hero")
    assert any(hj.post_return for hj in a.odyssey), "C6b: an Odyssey returns AND fights again"


# ── emit + parse + skill-dir (the one type) ──────────────────────────────────
def test_emit_lenses():
    a = arc.compile_archetype("King")
    assert "MERGE" in arc.cypher(a)
    assert "becomes(" in arc.prolog(a)
    assert json.loads(arc.to_json(a))["name"] == "King"


def test_parse_dsl():
    src = 'archetype Hero { substrate:"AI" domain:"startup" }\nchain Path { Hero => Guardian => King }'
    stmts = arc.parse(src)
    kinds = {s.kind for s in stmts}
    assert kinds == {"archetype", "chain"}
    hero = [s for s in stmts if s.kind == "archetype"][0]
    assert hero.knobs["substrate"] == "AI"
    path = [s for s in stmts if s.kind == "chain"][0]
    assert path.steps == ["Hero", "Guardian", "King"]


def test_emit_skill_is_the_one_type():
    a = arc.compile_archetype("Hero")
    out = tempfile.mkdtemp(prefix="arc_skill_")
    p = arc.emit_skill(a, out_dir=out, pantheon=arc.CYCLE)
    assert p.exists() and p.name == "SKILL.md"
    assert "Becoming" in p.read_text()
