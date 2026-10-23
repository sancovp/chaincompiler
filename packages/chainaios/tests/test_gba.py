"""Stage 1 — the General BanditAgent is a PERSISTENT native-CC AIOS (DESIGN.md §3, §10)."""
from __future__ import annotations

import tempfile
from pathlib import Path

import chainaios as cc
from chainaios.gba import make_gba, construct_into, search, load_gba


def _root():
    # a caller-owned dir (the GBA persists here; the point is the caller owns it, not /tmp-internal)
    return Path(tempfile.mkdtemp(prefix="test_gba_")) / "triage"


def test_make_gba_is_a_persistent_aios():
    g = make_gba("triage", _root(),
                 atoms=["[Symptom] ⇒ [Scope] ⇒ |Severity|", "[Repro] ⇒ [Localize] ⇒ |Cause|"])
    assert g.closed is True
    # the AIOS exists ON DISK — persona + live tree root + kb + index + manifest
    assert g.claude_md.exists()
    assert (g.skills_root / "0-triage" / "SKILL.md").exists()     # tree root, coord-addressed (0)
    assert (g.skills_root / "bandit-chain-system" / "SKILL.md").exists()
    assert g.kb.is_dir() and g.manifest.exists() and g.index_db.exists()
    # CLAUDE.md = the ROLE BLOCK only (the domain invariant / persona = who you are)
    role = g.claude_md.read_text()
    assert "TriageBandit" in role and "ChainSelector for `triage`" in role
    # the loop / law / kb-protocol are RULE BLOCKS (equipment), appended by Claude Code from .claude/rules
    assert g.rules_dir.is_dir()
    rules = "\n".join(p.read_text() for p in g.rules_dir.glob("*.md"))
    assert "default workflow" in rules.lower() and "everything is a skill" in rules.lower()
    # the default workflow lives IN the tree as a flow-skill (agent = persona+skills+skillCHAIN+skilltree)
    assert search(g, "default workflow", limit=5), "the <domain>-loop flow-skill must be in the tree"
    # the loop steps should NOT be inlined in the role block (it's a flow-skill, pointed to by a rule)
    assert "Recall = Select" not in role
    assert g.report["indexed_skills"] >= 3


def test_construct_persists_into_the_tree_and_reindexes():
    g = make_gba("triage", _root(), atoms=["[Symptom] ⇒ [Scope] ⇒ |Severity|"])
    before = g.report["indexed_skills"]
    sysd = construct_into(g, "rollback", ["[Change] ⇒ [Blast] ⇒ |Revert|"])
    # the new chain is a real SKILL.md, persisted into the agent's own dir (not /tmp)
    assert sysd.sc.exists() and sysd.sc.name == "SKILL.md"
    assert g.report["indexed_skills"] > before
    assert search(g, "revert"), "constructed skill must be findable via search"


def test_kb_and_persona_survive_rematerialize():
    g = make_gba("triage", _root(), atoms=["[Symptom] ⇒ [Scope] ⇒ |Severity|"])
    (g.kb / "note.md").write_text("glyphs: 🏆\nworked great\n")
    construct_into(g, "rollback", ["[Change] ⇒ [Blast] ⇒ |Revert|"])
    # materialize rmtree's root — the KB (reward record) and persona must survive
    assert (g.kb / "note.md").exists()
    assert g.claude_md.exists() and "TriageBandit" in g.claude_md.read_text()


def test_addressing_scopes_what_you_see():
    # every node is coordinate-addressed; search scoped to a coord exposes ONLY that subtree
    g = make_gba("triage", _root(), atoms=["[Symptom] ⇒ [Scope] ⇒ |Severity|"])
    construct_into(g, "perf", ["[Latency] ⇒ [Profile] ⇒ |Hotspot|"])
    allhits = search(g, "attend", limit=20)
    coords = {h["coord"] for h in allhits}
    assert "0" in coords                                    # the root is addressed
    in_01 = lambda c: c == "0.1" or c.startswith("0.1.")
    # unscoped finds something OUTSIDE the 0.1 subtree (the perf branch lives elsewhere)
    assert any(not in_01(h["coord"]) for h in allhits)
    # scoped to 0.1 → ONLY 0.1 + its descendants (where you are = what you see)
    scoped = search(g, "attend", scope_coord="0.1")
    assert scoped and all(in_01(h["coord"]) for h in scoped)


def test_reopen_cold_from_disk():
    g = make_gba("triage", _root(), atoms=["[Symptom] ⇒ [Scope] ⇒ |Severity|"])
    reopened = load_gba(g.root)           # nothing in memory — read from gba.json
    assert reopened.domain == "triage"
    assert search(reopened, "severity"), "a cold-reopened GBA is still searchable"


def test_gba_seats_a_custom_persona_cor():
    """persona= seats a real chain-of-reasoning as the GBA's CoR (not the domain bandit),
    and the CLAUDE.md role is derived from that persona's moves — while the GBA stays a
    full persistent AIOS (searchable, construct-able)."""
    from corcc.notation import Move, PersonaSpec

    spec = PersonaSpec(
        name="Aegis",
        blurb="assess the seeker, set the challenge, carry failure into success, ascend, transcend",
        moves=(Move("Assess", ("frame the seeker",)), Move("Challenge", ("set the rung",)),
               Move("Overcome", ("failure into success",)), Move("Transcend", ("toward innovation",))),
    )
    g = make_gba("aegis", _root().parent / "aegis", atoms=["[Challenge] ⇒ [Overcome] ⇒ |Mastery|"],
                 persona=spec)
    assert g.closed is True
    role = g.claude_md.read_text()
    assert "Aegis" in role and "Assess → Challenge → Overcome → Transcend" in role
    assert "TriageBandit" not in role and "ChainSelector" not in role   # not the bandit
    # the CoR skill in the tree is the custom persona, still searchable + construct-able
    assert search(g, "assess the seeker", limit=5)
    construct_into(g, "guardian-rite", ["[Trial] ⇒ [Growth] ⇒ |Ascension|"])
    assert search(g, "ascension"), "constructed subsystem must be findable"


def test_a_constructed_seat_is_a_LORD_you_can_descend_into():
    """Rule 01's forest-of-lords debt, closed + gated. A sub-domain constructed WITH ITS OWN
    persona carries its own `CLAUDE.md` at its dir — so reading into that dir seats you AS
    that persona (the auto-loader injects a dir's CLAUDE.md + skills on Read). Before this,
    the tree was single-lord: the seat's persona was DESCRIBED in a skill, never inhabitable."""
    from corcc.notation import Move, PersonaSpec

    seat = PersonaSpec(
        name="Rollback-Surgeon",
        blurb="find the change, bound the blast radius, revert the smallest safe unit",
        moves=(Move("Change", ("what changed",)), Move("Blast", ("who is affected",)),
               Move("Revert", ("the smallest safe unit",))),
    )
    g = make_gba("triage", _root(), atoms=["[Symptom] ⇒ [Scope] ⇒ |Severity|"])
    construct_into(g, "rollback", ["[Change] ⇒ [Blast] ⇒ |Revert|"], persona=seat)

    lord = g.root / "rollback-cor" / "CLAUDE.md"
    assert lord.exists(), "a persona'd sub-domain must be a LORD (its own CLAUDE.md at its dir)"
    text = lord.read_text()
    assert "Rollback-Surgeon" in text                        # who you BECOME there
    assert "Change → Blast → Revert" in text                 # its own melt-gauge, not the root's
    assert "--scope 0." in text                              # curates its own subtree
    assert "Read `../CLAUDE.md` (relative to this folder)" in text   # the way back UP (traversability)
    assert (lord.parent / ".." / "CLAUDE.md").resolve() == g.claude_md.resolve()  # …and it resolves
    assert str(g.root) not in text                           # portable: no machine's path
    assert g.report["lords"] == 1

    # a lord SURVIVES the next construct (materialize rmtree's root; lords re-emit from the manifest)
    construct_into(g, "perf", ["[Latency] ⇒ [Profile] ⇒ |Hotspot|"])
    assert lord.exists() and "Rollback-Surgeon" in lord.read_text()
    # …and a sub-domain with NO persona of its own gets NO lord (rule 01: grow lords on WARRANT)
    assert not (g.root / "perf-cor" / "CLAUDE.md").exists()
    assert g.report["lords"] == 1


def test_the_persisted_manifest_names_no_machine_path_and_reconstructs():
    """gba.json stores every skill_src relative to the GBA root, so a committed AIOS names no
    machine's path; construct_into resolves it back and keeps building."""
    g = make_gba("triage", _root(), atoms=["[Symptom] ⇒ [Scope] ⇒ |Severity|"])
    raw = g.manifest.read_text()
    assert str(g.root.parent) not in raw
    construct_into(g, "perf", ["[Latency] ⇒ [Profile] ⇒ |Hotspot|"])
    assert str(g.root.parent) not in g.manifest.read_text()
    assert search(g, "hotspot")
