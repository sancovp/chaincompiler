"""The Self-Interpreter for the chain dialect.

The dialect is **a Python dialect** — so the interpreter does NOT re-wrap Python's
native ops (arithmetic, control flow, data). It runs the program with Python, and
only *injects the ChainCompiler vocabulary* as builtins: forge/gate/package the
chains, build/walk skill trees, build exchanges, turn trees into MCPs. A program
sets `result` (or the namespace is returned) — that's the value.

Self-interpreter: programs can themselves forge languages, build trees, and emit
MCPs — including ones that interpret further. ChainCompiler thereby runs itself.
"""
from __future__ import annotations

from typing import Any


def make_env(extra: dict[str, Any] | None = None) -> dict[str, Any]:
    """The dialect's vocabulary — ChainCompiler primitives, injected as names."""
    import accc
    import chaincompiler
    import chainaios
    import corcc
    import sccc
    import skilltree

    from . import runtime
    from .mcp_tree import tree_to_mcp

    env: dict[str, Any] = {
        # construct (the AIOS top-door now lives in chainaios; write_skill stays in the CC base)
        "construct_language": chainaios.construct_language,
        "write_skill": chaincompiler.write_skill,
        "forge_ac": accc.forge, "package_ac": accc.package, "gate_ac": accc.gate,
        "forge_cor": corcc.forge_persona, "package_cor": corcc.package, "lint_cor": corcc.lint,
        "forge_sc": sccc.forge, "package_sc": sccc.package, "lint_sc": sccc.lint,
        # organize
        "SkillTree": skilltree.SkillTree, "TreeNode": skilltree.TreeNode,
        "materialize": skilltree.materialize, "validate_tree": skilltree.validate,
        "build_exchange": skilltree.build_exchange, "load_exchange": skilltree.load_exchange,
        # execute / search / emit
        "walk": runtime.walk, "reachable": runtime.reachable, "read_skill": runtime.read_skill,
        "tree_to_mcp": tree_to_mcp,
        "result": None,
    }
    if extra:
        env.update(extra)
    return env


def interpret(source: str, *, env: dict[str, Any] | None = None) -> Any:
    """Interpret a chain-dialect program. Returns `result` (or the eval of a single expr)."""
    ns = make_env(env)
    try:
        code = compile(source, "<si>", "eval")          # single expression?
        return eval(code, ns)
    except SyntaxError:
        exec(compile(source, "<si>", "exec"), ns)        # full program
        return ns.get("result")
