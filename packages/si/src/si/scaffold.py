"""P5.1 — scaffold a federated node repo from a skill tree.

When the SI emits an MCP, it can also stamp a ChainCompiler-SHAPED node repo: the
skill tree (cat-breadcrumbs), a marketplace registry that **federates under a
parent**, a runnable MCP launcher, and a README. The fractal made real — each
emitted MCP becomes a repo like ours, its marketplace joining under ours.

Full CI mechanics (deploy workflow, site generator) are P5.2; this stamps the
load-bearing shape: tree + registry + MCP + README, all validatable.
"""
from __future__ import annotations

import json
from pathlib import Path

from skilltree import SkillTree, Violation, materialize
from skilltree import validate as validate_tree

from .mcp_tree import tree_to_mcp

_NODE_README = """# {name} — a ChainCompiler node

A self-contained skill tree, served as an MCP, federated under `{parent}`.

- **Walk it** — start at `.claude/skills/{root}/SKILL.md` and follow the `cat` breadcrumbs.
- **Serve it** — `python serve_mcp.py` (an MCP exposing this tree's skills).
- **Marketplace** — see `registry.json`; this node registers under its parent.
"""


def scaffold_repo(name: str, tree: SkillTree | str | Path, out_dir: str | Path,
                  *, parent: str | None = None) -> Path:
    """Stamp a federated node repo at <out_dir>/<name>. Returns the repo path."""
    if isinstance(tree, (str, Path)):
        tree = SkillTree.load(tree)
    repo = Path(out_dir) / name
    repo.mkdir(parents=True, exist_ok=True)

    materialize(tree, repo)                      # the node's skill tree (cat-breadcrumbs)
    root = tree.root.name

    (repo / "registry.json").write_text(json.dumps({          # marketplace, federated
        "name": name,
        "parent": parent,                                      # null at the root; else a repo ref
        "entries": [{"name": root, "kind": "tree", "manifest": "skilltree.json",
                     "trust": "unverified"}],
    }, indent=2), encoding="utf-8")

    tree_to_mcp(repo, root, repo / "serve_mcp.py", name=f"node:{name}")   # the runnable MCP
    (repo / "README.md").write_text(
        _NODE_README.format(name=name, parent=parent or "(root)", root=root), encoding="utf-8")
    return repo


def validate_node(repo: str | Path) -> list[Violation]:
    """Validate a scaffolded node: the tree + the registry + the MCP launcher."""
    repo = Path(repo)
    out = list(validate_tree(repo))
    reg = repo / "registry.json"
    if not reg.is_file():
        out.append(Violation("error", repo.name, "missing registry.json"))
    else:
        try:
            data = json.loads(reg.read_text(encoding="utf-8"))
            if "parent" not in data or "entries" not in data:
                out.append(Violation("error", repo.name, "registry.json missing parent/entries"))
        except json.JSONDecodeError:
            out.append(Violation("error", repo.name, "registry.json is not valid JSON"))
    if not (repo / "serve_mcp.py").is_file():
        out.append(Violation("error", repo.name, "missing serve_mcp.py launcher"))
    return out
