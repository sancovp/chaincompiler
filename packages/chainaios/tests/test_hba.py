"""Stage 3 — the HBA emits a subagent-dispatch scaffold (DESIGN.md §3, §10 stage 3)."""
from __future__ import annotations

import re
import tempfile
from pathlib import Path

from chainaios.hba import make_hba
from chainaios.gba import construct_into, search


def _root():
    return Path(tempfile.mkdtemp(prefix="test_hba_")) / "triage"


def _frontmatter(md: Path) -> dict:
    m = re.match(r"^---\n(.*?)\n---", md.read_text(), re.S)
    assert m, f"{md} missing YAML frontmatter"
    out = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            out[k.strip()] = v.strip()
    return out


def test_hba_emits_seat_subagent_defs():
    h = make_hba("triage", _root(), atoms=["[Symptom] ⇒ [Scope] ⇒ |Severity|"])
    sel = h.agents_dir / "select-agent.md"
    con = h.agents_dir / "construct-agent.md"
    assert sel.exists() and con.exists()
    # valid subagent defs (name + description + tools)
    fs, fc = _frontmatter(sel), _frontmatter(con)
    assert fs["name"] == "select-agent" and "tools" in fs
    assert fc["name"] == "construct-agent" and "Write" in fc["tools"]   # construct needs Write
    # the construct seat is the anti-melt one (own context)
    assert "anti-melt" in con.read_text() or "own context" in con.read_text()


def test_hba_role_and_dispatch_protocol():
    h = make_hba("triage", _root(), atoms=["[Symptom] ⇒ [Scope] ⇒ |Severity|"])
    role = h.claude_md.read_text()
    assert "TriageHBA" in role and "dispatch" in role.lower()
    # the dispatch rule REPLACES the inline loop and names both seats + the Agent tool
    disp = (h.rules_dir / "01-hba-dispatch.md").read_text()
    assert "select-agent" in disp and "construct-agent" in disp and "Agent/Task tool" in disp
    assert not (h.rules_dir / "01-bandit-loop.md").exists()   # inline loop is gone (dispatched instead)


def test_hba_is_still_a_gba_underneath():
    h = make_hba("triage", _root(), atoms=["[Symptom] ⇒ [Scope] ⇒ |Severity|"])
    # the HBA has a live tree + index + kb (it's a GBA), so exec/search still work
    assert h.gba.index_db.exists() and h.gba.kb.is_dir()
    assert search(h.gba, "severity")


def test_construct_preserves_hba_identity():
    # the construct-agent persists into the tree at runtime → _apply_tree must NOT clobber the HBA role
    h = make_hba("triage", _root(), atoms=["[Symptom] ⇒ [Scope] ⇒ |Severity|"])
    construct_into(h.gba, "rollback", ["[Change] ⇒ [Blast] ⇒ |Revert|"])
    role = h.claude_md.read_text()
    assert "TriageHBA" in role                       # role survived
    assert (h.rules_dir / "01-hba-dispatch.md").exists()   # dispatch rule survived
    assert "01-bandit-loop.md" not in [p.name for p in h.rules_dir.glob("*.md")]
    assert (h.agents_dir / "select-agent.md").exists()     # seat defs survived
