"""Compile an attention chain into a usable attention-directing prompt block.

This is the AC-specific lens (HoneyC gives generic triples/prose; this turns an
AC into the actual block you inject to direct a model's attention).
"""
from __future__ import annotations

from honeyc.ast_nodes import Bounded, Chain, Entity, Glyph, Symbol, TypeAnn
from honeyc.parser import parse_text


def _label(term: object) -> str:
    if isinstance(term, Bounded):
        return _label(term.term)
    if isinstance(term, TypeAnn):
        return _label(term.term)
    if isinstance(term, Entity):
        return term.id
    if isinstance(term, Symbol):
        return term.name
    if isinstance(term, Glyph):
        return term.name or term.id
    return str(term)


def parse_ac(ac: str) -> tuple[list[str], str | None]:
    """Return (ordered foci, held focus) for an attention chain."""
    program = parse_text(ac)
    chain = next((s for s in program.statements if isinstance(s, Chain)), None)
    if chain is None:
        raise ValueError(f"not an attention chain: {ac!r}")
    foci = [_label(t) for t in chain.terms if not isinstance(t, Bounded)]
    held_term = next((t for t in chain.terms if isinstance(t, Bounded)), None)
    return foci, (_label(held_term) if held_term is not None else None)


def attention_block(name: str, ac: str) -> str:
    """The injectable prompt block that directs attention along the chain."""
    foci, held = parse_ac(ac)
    lines = [f"# Attention chain — {name}", "Attend, in order:"]
    lines += [f"  {i}. {focus}" for i, focus in enumerate(foci, 1)]
    if held:
        lines.append(f"Hold: {held}  ← converge attention here, then act")
    return "\n".join(lines)
