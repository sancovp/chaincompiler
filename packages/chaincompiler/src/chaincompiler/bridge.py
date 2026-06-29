"""The HoneyC seam (compile a gated chain into lenses) + re-exports of the rulecatcher seam.

The rulecatcher seam — `learn` / `gate` / `grammar_lines` / `foreign_tokens` — MOVED DOWN to
`prompt_engineering.grammar` (REBUILD-SPEC.md §4 — single source of truth, D1). chaincompiler keeps the
HoneyC-wrapping `compile_chain` (HoneyC is chaincompiler's concern, §6) and RE-EXPORTS the grammar seam,
so `from chaincompiler.bridge import learn, gate, grammar_lines` and `from chaincompiler import learn,
gate` stay byte-stable.
"""
from __future__ import annotations

from honeyc.normalize import normalize
from honeyc.parser import parse_text
from honeyc.render import render

# the rulecatcher seam now lives in the base (DOWN edge):
from prompt_engineering.grammar import (
    ForeignToken,
    foreign_tokens,
    gate,
    grammar_lines,
    learn,
)


def compile_chain(chain: str) -> dict:
    """Compile a chain through HoneyC into semantic lenses."""
    program = parse_text(chain)
    return {
        "readable": render(program, "readable"),
        "triples": render(program, "triples"),
        "prose": render(program, "prose"),
        "statements": normalize(program),
    }


__all__ = ["compile_chain", "learn", "gate", "grammar_lines", "foreign_tokens", "ForeignToken"]
