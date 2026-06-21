"""The execute arm — walk a SkillTree by following its Read-breadcrumbs.

This is what "running" a tree means: start at the root SKILL.md, parse the
breadcrumb paths, and recurse. No new mechanism — the same breadcrumbs the
validator checks are the ones the runtime follows. (The breadcrumb verb is the
Read tool, not `cat`; the path is what we follow.)
"""
from __future__ import annotations

from pathlib import Path
import re

_CRUMB = re.compile(r"`([^`]+/SKILL\.md)`")     # the backticked SKILL.md path, verb-agnostic


def _skill_md(node_dir: Path, name: str) -> Path:
    return Path(node_dir) / ".claude" / "skills" / name / "SKILL.md"


def _strip_front(text: str) -> str:
    return text.split("---", 2)[-1].strip() if text.lstrip().startswith("---") else text.strip()


def _walk_md(md: Path) -> dict:
    node = {"name": md.parent.name, "skill": str(md), "children": []}
    if not md.is_file():
        node["error"] = "missing"
        return node
    for p in _CRUMB.findall(md.read_text(encoding="utf-8")):
        node["children"].append(_walk_md(Path(p)))
    return node


def walk(root_dir: str | Path, root_name: str) -> dict:
    """Traverse the tree from its root by following breadcrumbs. Returns a nested dict."""
    return _walk_md(_skill_md(Path(root_dir), root_name))


def reachable(root_dir: str | Path, root_name: str) -> list[str]:
    """Flat list of every skill name reachable from the root (the execute frontier)."""
    out: list[str] = []
    def rec(n):
        out.append(n["name"])
        for c in n["children"]:
            rec(c)
    rec(walk(root_dir, root_name))
    return out


def read_skill(root_dir: str | Path, name: str) -> str | None:
    """Search the tree for a skill by name; return its body (the search arm)."""
    for md in Path(root_dir).rglob("SKILL.md"):
        if md.parent.name == name:
            return _strip_front(md.read_text(encoding="utf-8"))
    return None
