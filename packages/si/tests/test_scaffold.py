"""P5.1 tests: scaffold a federated node repo and validate it."""
from __future__ import annotations

import json
from pathlib import Path

from si import scaffold_repo, validate_node
from skilltree import SkillTree, TreeNode


def _tree() -> SkillTree:
    return SkillTree(TreeNode("cc-skill-tree", "sc", children=[
        TreeNode("reason", "cor", children=[TreeNode("simplify", "ac")]),
    ]))


def test_scaffold_stamps_a_chaincompiler_shaped_node(tmp_path: Path):
    repo = scaffold_repo("debug-node", _tree(), tmp_path, parent="github:sancovp/chaincompiler")
    # the load-bearing shape: tree + registry + MCP launcher + README
    assert (repo / ".claude" / "skills" / "cc-skill-tree" / "SKILL.md").is_file()
    assert (repo / "skilltree.json").is_file()
    assert (repo / "registry.json").is_file()
    assert (repo / "serve_mcp.py").is_file()
    assert (repo / "README.md").is_file()
    assert validate_node(repo) == []


def test_registry_federates_under_parent(tmp_path: Path):
    repo = scaffold_repo("node-x", _tree(), tmp_path, parent="github:sancovp/chaincompiler")
    reg = json.loads((repo / "registry.json").read_text())
    assert reg["parent"] == "github:sancovp/chaincompiler"     # joins under ours
    assert reg["entries"][0]["name"] == "cc-skill-tree"
    assert reg["entries"][0]["trust"] == "unverified"          # untrusted by default


def test_validate_node_catches_a_broken_node(tmp_path: Path):
    repo = scaffold_repo("node-y", _tree(), tmp_path)
    (repo / "serve_mcp.py").unlink()                            # remove the MCP launcher
    issues = [v for v in validate_node(repo) if v.severity == "error"]
    assert any("serve_mcp.py" in v.message for v in issues)
