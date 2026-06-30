"""A COG is a FLOW through three role-AIOS dirs (DESIGN.md §4, §10) — NOT a function.

These are metaformal self-tests: they OBSERVE the real substrate (the dirs/skills that got emitted),
they do not assert the return value of a stubbed orchestrator. There is no `run_cog` — the COG is run
by an agent walking it. See ~/.claude/skills/metaformal-self-test.
"""
from __future__ import annotations

import tempfile
from pathlib import Path

from chainaios.cog import make_cog, PATTERNS


def _root():
    return Path(tempfile.mkdtemp(prefix="test_cog_")) / "triage"


def test_cog_emits_seats_workspace_and_a_flow_skill():
    cog = make_cog("triage", _root(), atoms=["[Symptom] ⇒ [Scope] ⇒ |Severity|"])
    # OBSERVE: each seat is a real role-AIOS dir you can go to (its own CLAUDE.md + tree)
    for seat in (cog.C, cog.O, cog.G):
        assert seat.claude_md.exists() and seat.skills_root.is_dir()
    # OBSERVE: the shared workspace exists (where the deliverable accumulates)
    assert cog.workspace.is_dir()
    # OBSERVE: the default-workflow FLOW is a real skill in the COG tree, and it resolves (shape-guaranteed)
    assert cog.flow is not None and cog.flow.exists()
    flow = cog.flow.read_text()
    assert "Challenger" in flow and "Generator" in flow and "Observer" in flow and "workspace" in flow
    assert cog.closed is True            # validate() found the tree well-formed


def test_cog_role_points_at_the_flow_not_a_function():
    cog = make_cog("triage", _root(), atoms=["[Symptom] ⇒ [Scope] ⇒ |Severity|"])
    role = cog.claude_md.read_text()
    assert "COG" in role and "./C/" in role and "./G/" in role and "./O/" in role
    assert "default workflow" in role.lower()


def _is_hba(seat_root: Path) -> bool:
    return (seat_root / ".claude" / "agents" / "construct-agent.md").exists()


def test_variant_lattice_makes_seats_gba_or_hba():
    # the 2^3 pattern catalog
    assert len(PATTERNS) == 8 and PATTERNS["all-hba"] == {"C", "O", "G"} and PATTERNS["flat"] == set()
    # OBSERVE: seats={"G"} → only G/ carries the subagent scaffold
    cog = make_cog("triage", _root(), atoms=["[Symptom] ⇒ [Scope] ⇒ |Severity|"], seats={"G"})
    assert _is_hba(cog.G.root) and not _is_hba(cog.C.root) and not _is_hba(cog.O.root)


def test_all_hba_variant():
    cog = make_cog("triage", _root(), atoms=["[Symptom] ⇒ [Scope] ⇒ |Severity|"], seats=PATTERNS["all-hba"])
    assert all(_is_hba(s.root) for s in (cog.C, cog.O, cog.G))
