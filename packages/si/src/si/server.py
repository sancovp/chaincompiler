"""The Self-Interpreter as an MCP server (and it is also a skill — see si/skill/).

Exposes the chain dialect to any MCP client:
  - si_interpret(source)              run a chain-dialect program
  - si_walk(root_dir, root_name)      traverse a materialized tree
  - si_reachable(root_dir, root_name) list reachable skills
  - si_read_skill(root_dir, skill)    fetch a skill body by name
  - si_tree_to_mcp(root_dir, name, out) turn a tree/master into its own MCP

Run:  python -m si.server   (or the `si-server` console script)

The tool functions stay plain callables (registered, not rebound) so they're
usable directly and in tests, not only over the wire.
"""
from __future__ import annotations

from fastmcp import FastMCP

from . import runtime
from .interp import interpret
from .mcp_tree import tree_to_mcp

mcp = FastMCP("self-interpreter")


def si_interpret(source: str) -> str:
    """Interpret a ChainCompiler chain-dialect program; returns repr(result)."""
    return repr(interpret(source))


def si_walk(root_dir: str, root_name: str) -> dict:
    """Traverse a materialized skill tree by following its cat-breadcrumbs."""
    return runtime.walk(root_dir, root_name)


def si_reachable(root_dir: str, root_name: str) -> list[str]:
    """List every skill reachable from a tree's root."""
    return runtime.reachable(root_dir, root_name)


def si_read_skill(root_dir: str, skill: str) -> str:
    """Search a tree for a skill by name and return its body."""
    body = runtime.read_skill(root_dir, skill)
    return body if body is not None else f"(no skill named {skill!r})"


def si_tree_to_mcp(root_dir: str, root_name: str, out_path: str) -> str:
    """Turn a skill tree (or exchange master) into a runnable MCP launcher."""
    return str(tree_to_mcp(root_dir, root_name, out_path))


def si_search(root_dir: str, query: str, scope_coord: str | None = None, limit: int = 10) -> list[dict]:
    """Search the skill tree (BM25), optionally scoped to a coordinate subtree (e.g. '0.1')."""
    from skilltree import search_tree
    return search_tree(root_dir, query, scope_coord=scope_coord, limit=limit)


# Register as MCP tools without rebinding the names (keep them plain callables).
for _fn in (si_interpret, si_walk, si_reachable, si_read_skill, si_tree_to_mcp, si_search):
    mcp.tool()(_fn)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
