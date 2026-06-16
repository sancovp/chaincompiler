"""Turn a skill tree (or exchange master) into an MCP server.

`build_tree_server` makes a FastMCP server that exposes a materialized tree's
skills as tools (list / read / walk). `tree_to_mcp` writes a tiny launcher so any
tree or master becomes a runnable MCP — that's "make trees and masters into MCPs".
"""
from __future__ import annotations

from pathlib import Path

from . import runtime


def build_tree_server(root_dir: str | Path, root_name: str, *, name: str | None = None):
    """A FastMCP server exposing the tree's skills. (Run with .run() for stdio.)"""
    from fastmcp import FastMCP

    root_dir = str(root_dir)
    server = FastMCP(name or f"skilltree:{root_name}")

    @server.tool()
    def list_skills() -> list[str]:
        """List every skill reachable from this tree's root."""
        return runtime.reachable(root_dir, root_name)

    @server.tool()
    def read_skill(skill: str) -> str:
        """Return the body of a skill in this tree by name."""
        body = runtime.read_skill(root_dir, skill)
        return body if body is not None else f"(no skill named {skill!r} in this tree)"

    @server.tool()
    def walk() -> dict:
        """Return the full tree, traversed by following cat-breadcrumbs."""
        return runtime.walk(root_dir, root_name)

    return server


_LAUNCHER = '''#!/usr/bin/env python3
"""Auto-generated MCP launcher for skill tree {name!r} (root {root!r})."""
from si.mcp_tree import build_tree_server

if __name__ == "__main__":
    build_tree_server({root_dir!r}, {root!r}, name={name!r}).run()
'''


def tree_to_mcp(root_dir: str | Path, root_name: str, out_path: str | Path,
                *, name: str | None = None) -> Path:
    """Write a runnable MCP launcher that serves this tree/master. Returns its path."""
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(_LAUNCHER.format(root_dir=str(Path(root_dir).resolve()),
                                    root=root_name, name=name or f"skilltree:{root_name}"),
                   encoding="utf-8")
    return out
