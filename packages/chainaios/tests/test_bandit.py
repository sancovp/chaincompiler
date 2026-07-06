"""Tests for the bandit's roll-up + hierarchicalize capability."""
from __future__ import annotations

import tempfile
from pathlib import Path

import chainaios as cc
from chainaios.bandit import COMPONENTS, domain_bandit


def _work():
    return Path(tempfile.mkdtemp(prefix="test_bandit_"))


def test_domain_bandit_is_the_selector_specialized():
    p = domain_bandit("triage")
    assert p.name == "TriageBandit"
    # same explore/exploit moves as the base bandit (still the selector, not a flavor)
    assert [m.name for m in p.moves] == ["Task", "Recall", "Decide", "Execute", "Reward"]
    assert "triage" in p.blurb


def test_roll_up_algebra_closes():
    w = _work()
    s = cc.roll_up_algebra(
        "triage",
        ["[Symptom] ⇒ [Scope] ⇒ |Severity|", "[Repro] ⇒ [Localize] ⇒ |Cause|"],
        db=str(w / "cc.db"), skills_dir=str(w / "skills"), out_dir=str(w / "dist"),
        persona_root=str(w / "personas"),
    )
    assert s.closed is True
    assert s.report["minted_ok"] and s.report["violations"] == 0
    # the one type: every artifact is a SKILL.md
    for p in [*s.ac, s.cor, s.sc]:
        assert p.exists() and p.name == "SKILL.md"
    assert len(s.ac) == 2
    # the CoR is the domain-specialized bandit
    assert "bandit" in s.cor.parent.name.lower()


def test_persona_aios_has_kb_and_glyphsteer_instructions():
    w = _work()
    s = cc.roll_up_algebra(
        "triage", ["[Symptom] ⇒ |Severity|"],
        db=str(w / "cc.db"), skills_dir=str(w / "skills"), out_dir=str(w / "dist"),
        persona_root=str(w / "personas"),
    )
    # a persona IS a CLAUDE.md inside a dir (an AIOS), not a single SKILL.md
    claude = s.persona_dir / "CLAUDE.md"
    assert claude.exists()
    text = claude.read_text()
    assert "Build your own KB" in text                      # self-KB instruction
    assert "Improve yourself via GlyphSteer" in text        # glyphsteer self-improve instruction
    assert (s.persona_dir / "kb").is_dir()                  # the KB itself
    assert (s.persona_dir / "legend.json").exists()         # the glyph vocabulary


def test_roll_up_algebra_custom_persona_and_named_atoms():
    """persona= seats a custom PersonaSpec CoR (e.g. an SDNA v2 melt-gauge chain);
    dict atoms control the minted AC package names (+ optional descriptions)."""
    from corcc.notation import Move, PersonaSpec

    w = _work()
    spec = PersonaSpec(
        name="WoomEngineer",
        blurb="experience, seam, floor, generator, law, proof",
        moves=(
            Move("Experience", ("the felt experience",)),
            Move("Seam", ("which seam",)),
            Move("Proof", ("observed directly",)),
        ),
    )
    s = cc.roll_up_algebra(
        "woom",
        {"woom-design-attention": ("[Experience] ⇒ [Seam] ⇒ |Floor|", "Design attention."),
         "woom-verify-attention": "[Claim] ⇒ [Evidence] ⇒ |Label|"},
        db=str(w / "cc.db"), skills_dir=str(w / "skills"), out_dir=str(w / "dist"),
        persona_root=str(w / "personas"), persona=spec,
    )
    assert s.closed is True
    # named atoms → named AC packages (not {domain}-attention-N)
    assert {p.parent.name for p in s.ac} == {"woom-design-attention", "woom-verify-attention"}
    # the CoR seat is the custom persona, not the bandit
    assert s.cor.parent.name == "woomengineer"
    assert "bandit" not in s.cor.parent.name.lower()
    text = (s.persona_dir / "CLAUDE.md").read_text()
    assert "WoomEngineer" in text
    assert "Experience → Seam → Proof" in text     # role + loop render from ITS moves
    assert "ChainSelector" not in text             # no bandit wording leaks in
    assert "the bandit, spoken" not in text        # CoR label renders as the melt-gauge
    assert "Build your own KB" in text             # AIOS self-improvement kept
    assert "Improve yourself via GlyphSteer" in text
    # persona dir named from the persona, not "-bandit-"
    assert "bandit" not in s.persona_dir.name


def test_hierarchicalize_over_own_components_closes():
    w = _work()
    view = cc.hierarchicalize(workdir=str(w / "self"))
    assert view.closed is True
    assert view.report["violations"] == 0
    # one closed system per component the bandit is made of
    assert len(view.systems) == len(COMPONENTS)
    assert all(s.closed for s in view.systems)
    assert {s.domain for s in view.systems} == set(COMPONENTS)
    # the master self-view tree exists (the granular view of itself)
    assert (view.tree_root / ".claude" / "skills").exists() or view.tree_root.exists()
