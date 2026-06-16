"""CORCC tests: forging personas, the inner/outer split, syntax lint, packaging."""
from __future__ import annotations

from pathlib import Path

from corcc import cor_chain, forge_persona, inner_template, lint, outer_template, package
from corcc.notation import EINSTEIN


def test_cor_chain_built_from_moves():
    assert cor_chain(EINSTEIN) == "[Invariants] ⇒ [ThoughtExperiment] ⇒ [Simplicity] ⇒ |Reframe|"


def test_forge_persona_builds_inner_ac(tmp_path: Path):
    p = forge_persona(EINSTEIN, db=str(tmp_path / "c.db"))
    assert p.inner.scope == "ac:ThinkLikeEinstein"
    assert p.inner.rule_count > 0
    assert "Attend" in inner_template(p)          # inner = silent template
    assert "Invariants" in outer_template(p)      # outer = spoken paragraph skeleton


def test_lint_accepts_well_formed_cor(tmp_path: Path):
    p = forge_persona(EINSTEIN, db=str(tmp_path / "c.db"))
    violations, _ = lint(p, "[Invariants] ⇒ [ThoughtExperiment] ⇒ [Simplicity] ⇒ |Reframe|")
    assert violations == []


def test_lint_flags_malformed_cor(tmp_path: Path):
    p = forge_persona(EINSTEIN, db=str(tmp_path / "c.db"))
    # dropped a connector between the first two moves -> malformed syntax (melting)
    violations, _ = lint(p, "[Invariants] [ThoughtExperiment] ⇒ |Reframe|")
    assert violations, "malformed CoR should be caught by the syntax linter"


def test_package_writes_skill_md(tmp_path: Path):
    p = forge_persona(EINSTEIN, db=str(tmp_path / "c.db"))
    path = package(p, out_dir=str(tmp_path / "skills"))
    assert path.name == "SKILL.md"
    text = path.read_text()
    assert "chain-of-reasoning" in text          # frontmatter kind
    assert "DECISION" in text                     # CoR ends in a decision
    assert cor_chain(EINSTEIN) in text            # the custom-syntax chain is in the body
