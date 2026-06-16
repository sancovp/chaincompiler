"""SkillTree — a tree of skill dirs wired by links, with programmatic validation.

The substrate won't auto-traverse it (no nested-.claude auto-load), so the
validator is the system. Nodes are skill dirs of any type (ac/cor/sc/skill);
edges are symlinks; descending a level = redirecting the active skills root.
"""
from __future__ import annotations

__version__ = "0.1.0"

from .exchange import Exchange, Member, load_exchange
from .exchange import build as build_exchange
from .exchange import is_valid as exchange_is_valid
from .exchange import validate as validate_exchange
from .materialize import materialize
from .model import SkillTree, TreeNode
from .validate import Violation, is_valid, validate

__all__ = [
    "SkillTree", "TreeNode", "materialize", "validate", "is_valid", "Violation",
    "Exchange", "Member", "load_exchange", "build_exchange", "validate_exchange",
    "exchange_is_valid", "__version__",
]
