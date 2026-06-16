"""SI tests: the dialect interpreter, the walk runtime, and tree→MCP."""
from __future__ import annotations

from pathlib import Path

from si import build_tree_server, interpret, reachable, read_skill, tree_to_mcp


def test_interpret_single_expression():
    assert interpret("2 + 3") == 5            # native Python op, not re-wrapped


def test_interpret_builds_and_walks_a_tree(tmp_path: Path):
    # a chain-dialect program: build a tree with injected primitives, walk it
    src = """
tree = SkillTree(TreeNode("root", "sc", children=[TreeNode("a", "ac"), TreeNode("b", "cor")]))
materialize(tree, OUT)
result = reachable(OUT, "root")
"""
    out = str(tmp_path / "tree")
    result = interpret(src, env={"OUT": out})
    assert result == ["root", "a", "b"]       # the execute arm followed the breadcrumbs


def test_interpret_constructs_a_language(tmp_path: Path):
    from corcc.notation import EINSTEIN
    src = """
result = construct_language("triage", ac_chain="[A] ⇒ [B] ⇒ |C|",
                            cor_persona=PERSONA, db=DB, skills_dir=SK, out_dir=OUT)
"""
    bundle = interpret(src, env={
        "PERSONA": EINSTEIN, "DB": str(tmp_path / "x.db"),
        "SK": str(tmp_path / "sk"), "OUT": str(tmp_path / "out"),
    })
    assert bundle.ac.exists() and bundle.cor.exists() and bundle.sc.exists()


def test_tree_to_mcp_writes_launcher(tmp_path: Path):
    src = 'materialize(SkillTree(TreeNode("root","sc",children=[TreeNode("a","ac")])), OUT)'
    out = str(tmp_path / "tree")
    interpret(src, env={"OUT": out})
    launcher = tree_to_mcp(out, "root", tmp_path / "serve_tree.py")
    assert launcher.is_file()
    text = launcher.read_text()
    assert "build_tree_server" in text and "root" in text


def test_build_tree_server_constructs(tmp_path: Path):
    src = 'materialize(SkillTree(TreeNode("root","sc",children=[TreeNode("a","ac")])), OUT)'
    out = str(tmp_path / "tree")
    interpret(src, env={"OUT": out})
    server = build_tree_server(out, "root")
    assert server is not None
    # the runtime the server wraps works
    assert reachable(out, "root") == ["root", "a"]
    assert read_skill(out, "a") is not None
