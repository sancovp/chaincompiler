"""si — the Self-Interpreter for the ChainCompiler chain dialect.

A Python dialect: the interpreter defers to native Python and only injects the
ChainCompiler vocabulary. Ships as an MCP server (si.server) that is ALSO a skill
(si/skill/SKILL.md), and can turn skill trees / exchange masters into MCPs.
The execute arm of Compilero Bandito; the self-hosting capstone.
"""
from __future__ import annotations

__version__ = "0.1.0"

from .interp import interpret, make_env
from .mcp_tree import build_tree_server, tree_to_mcp
from .runtime import reachable, read_skill, walk
from .scaffold import scaffold_repo, validate_node

__all__ = [
    "interpret", "make_env", "walk", "reachable", "read_skill",
    "build_tree_server", "tree_to_mcp", "scaffold_repo", "validate_node", "__version__",
]
