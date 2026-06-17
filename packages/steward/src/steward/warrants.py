"""Warrants — the gate, at increasing fidelity (the merge axis).

The Custodian's warrant has a fidelity ladder (CCC DESIGN.md §2.1):
  proto_soma  — a shape/regex check (CCC's `required_pattern` today)
  grammar     — a rulecatcher/GlyphSteer syntax gate (ok/orthogonal/syntax_break)
  soma        — full geometry-closure (CB/CartON; not built here)

Building Stewards off the graph lets us swap the warrant up the ladder without touching
the loop — which is exactly the upgrade path when this federates into CCC.
"""
from __future__ import annotations

import re

from .core import Artifact, Verdict, Warrant


def always() -> Warrant:
    """The null warrant — admits everything. The reward-less degenerate case."""
    return Warrant("always", lambda a: Verdict(True), tier="proto_soma")


def shape(required: str, *, on: str = "body") -> Warrant:
    """proto-SOMA: the artifact's `on` field must match a regex (CCC's required_pattern)."""
    rx = re.compile(required)
    def check(a: Artifact) -> Verdict:
        text = getattr(a, on, "") if on != "name" else a.name
        ok = bool(rx.search(text or ""))
        return Verdict(ok, "" if ok else f"{on} does not match /{required}/")
    return Warrant(f"shape:/{required}/", check, tier="proto_soma")


def non_empty() -> Warrant:
    """proto-SOMA: a produced artifact must have a name and a body."""
    def check(a: Artifact) -> Verdict:
        ok = bool(a.name and a.body.strip())
        return Verdict(ok, "" if ok else "empty name or body")
    return Warrant("non_empty", check, tier="proto_soma")


def glyph_grammar(vocab) -> Warrant:
    """grammar: gate the artifact's glyph code through rulecatcher (GlyphSteer).

    The artifact must carry `meta['code']` (a glyph code). syntax_break ⇒ reject;
    orthogonal ⇒ admit-with-fix (canonical reorder noted in detail); ok ⇒ admit.
    This is the rung above the regex gate — the warrant upgrade the merge wants.
    """
    from glyphsteer.grammar import GlyphGrammar
    gg = GlyphGrammar(vocab, scope="steward")

    def check(a: Artifact) -> Verdict:
        code = a.meta.get("code", "")
        lint = gg.lint(code)
        if lint.verdict == "syntax_break":
            return Verdict(False, "syntax_break", {"violations": str(lint.violations)})
        if lint.verdict == "orthogonal":
            a.meta["code"] = lint.fix                       # admit-with-repair (canonical)
            return Verdict(True, "orthogonal→canonicalized", {"fix": lint.fix})
        return Verdict(True, "ok")
    return Warrant("glyph_grammar", check, tier="grammar")
