"""Materialize a SkillTree as nested dirs wired by `cat`-breadcrumbs.

The auto-loader only ever loads the ROOT (it won't descend a nested `.claude`).
So each node's SKILL.md body carries the `cat` commands that tell you how to read
its children — the breadcrumb links. The tree is nested dirs; traversal is manual
`cat` following the breadcrumbs. Layout for a node N with children C1..Ck:

    <N_dir>/.claude/skills/<N>/SKILL.md          # N's skill + `cat` links to each child
    <N_dir>/<C1>/.claude/skills/<C1>/SKILL.md     # child dir is a SIBLING of N's .claude
    <N_dir>/<C2>/...

The root node's dir IS the tree root; root skill at <root>/.claude/skills/<root>/.
Leaves carry the actual skill content (from skill_src); no further breadcrumbs.
"""
from __future__ import annotations

from pathlib import Path
import shutil

from .model import SkillTree, TreeNode, assign_coords, skill_name

# A breadcrumb line is parseable by validate.py: `- <name> (<kind>): cat <abspath>`
_CRUMB = "- {name} ({kind}): `cat {path}`"


def node_skill_md(node_dir: Path, node_name: str) -> Path:
    return node_dir / ".claude" / "skills" / node_name / "SKILL.md"


def _front(name: str, description: str, body: str) -> str:
    return f"---\nname: {name}\ndescription: {description}\n---\n\n{body.rstrip()}\n"


def _write_node(node: TreeNode, node_dir: Path, root: Path) -> None:
    sname = skill_name(node)                      # coord-prefixed identity (or plain name)
    skill_md = node_skill_md(node_dir, sname)
    skill_md.parent.mkdir(parents=True, exist_ok=True)

    # base body: the node's own skill content (from src) or a stub
    if node.skill_src and (Path(node.skill_src) / "SKILL.md").exists():
        src = (Path(node.skill_src) / "SKILL.md").read_text(encoding="utf-8")
        # strip frontmatter from the source body; we re-emit our own
        base = src.split("---", 2)[-1].strip() if src.lstrip().startswith("---") else src.strip()
        desc = node.description or f"{node.kind} node {node.name}"
    else:
        base = f"SkillTree {node.kind} node `{node.name}`."
        desc = node.description or f"{node.kind} node {node.name} in a SkillTree."
    if node.coord:
        desc = f"[{node.coord}] {desc}"

    if node.children:
        crumbs = [_CRUMB.format(name=skill_name(c), kind=c.kind,
                                path=node_skill_md(node_dir / c.name, skill_name(c)).resolve())
                  for c in node.children]
        body = (f"{base}\n\n## Descend — the next layer ({len(node.children)})\n"
                "Auto-load stops here (nested `.claude` will not load). To go deeper, "
                "run the `cat` for the child you want:\n\n" + "\n".join(crumbs))
    else:
        body = base + "\n\n_(leaf — this is an actual skill.)_"

    skill_md.write_text(_front(sname, desc, body), encoding="utf-8")

    # recurse: each child's dir is a sibling of this node's .claude (tree-path uses plain name)
    for child in node.children:
        _write_node(child, node_dir / child.name, root)


def materialize(tree: SkillTree, root: str | Path, *, overwrite: bool = True,
                coords: bool = False, base: str = "0") -> Path:
    root = Path(root)
    if coords:
        assign_coords(tree.root, base)            # address every node before writing
    if overwrite and root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True, exist_ok=True)
    _write_node(tree.root, root, root)          # root node's dir IS the tree root
    tree.save(root / "skilltree.json")
    return root
