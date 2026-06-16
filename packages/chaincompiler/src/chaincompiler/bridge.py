"""The seam: rulecatcher (learn grammar + gate) ⇄ HoneyC (compile + lenses).

This is the half that closes the compiler-compiler loop. rulecatcher catches the
emergent grammar of a cognition-chain notation and acts as the gate; HoneyC
compiles a gated chain into semantic lenses. Together they let the system learn
a prompt-DSL from examples, enforce it, and compile it into a re-injectable prime.
"""
from __future__ import annotations

import json
from sqlite3 import Connection

from honeyc.normalize import normalize
from honeyc.parser import parse_text
from honeyc.render import render
from rulecatcher.db import list_rules
from rulecatcher.engine import adopt_rules, catch_patterns
from rulecatcher.linting import build_normalization_suggestions, lint_text
from rulecatcher.models import ArtifactInput


def learn(
    connection: Connection,
    chains: list[str],
    *,
    scope: str,
    keywords: tuple[str, ...] = (),
    min_confidence: float = 1.0,
    rule_types: tuple[str, ...] = ("next_kind",),
    label: str = "seed",
) -> list:
    """Catch the grammar of `chains` and ratify (adopt) the rigid rules.

    Defaults to `next_kind` only: the SHAPE of the notation, not its vocabulary.
    A cognition-chain notation's grammar is "an [Identifier] then ⇒ then ..." —
    not the specific step names. Adopting `next_token` too would pin the corpus
    vocabulary and make the grammar grow every time a new step name appears.
    Pass rule_types=("next_kind","next_token") to also fix exact tokens.

    Returns the adopted rule rows = the ratified grammar of the notation.
    """
    content = "\n".join(chains) + "\n"
    catch_patterns(
        connection,
        [ArtifactInput(label=label, content=content)],
        scope=scope,
        keywords=list(keywords) or None,
    )
    pending = list_rules(connection, "pending", scope=scope)
    ids = [
        int(r["id"])
        for r in pending
        if float(r["confidence"]) >= min_confidence and r["rule_type"] in rule_types
    ]
    if ids:
        adopt_rules(connection, ids, actor="chaincompiler",
                    reason=f"ratified {'/'.join(rule_types)} grammar (confidence >= {min_confidence:.2f})")
    return list_rules(connection, "adopted", scope=scope)


def gate(connection: Connection, chain: str, *, scope: str) -> tuple[list, list]:
    """Lint a candidate chain against the ratified grammar. Returns (violations, fixes)."""
    violations = lint_text(connection, chain, scope=scope, record_stats=False)
    return violations, build_normalization_suggestions(violations)


def compile_chain(chain: str) -> dict:
    """Compile a chain through HoneyC into semantic lenses."""
    program = parse_text(chain)
    return {
        "readable": render(program, "readable"),
        "triples": render(program, "triples"),
        "prose": render(program, "prose"),
        "statements": normalize(program),
    }


def grammar_lines(adopted_rows: list) -> list[str]:
    """Human-readable rendering of the ratified grammar (for the prime block)."""
    lines: list[str] = []
    for r in sorted(adopted_rows, key=lambda x: (-len(json.loads(x["prefix_json"])), -float(x["confidence"]))):
        prefix = json.loads(r["prefix_json"])
        kind = "tok" if r["rule_type"] == "next_token" else "kind"
        lines.append(f"- [{kind}] after {prefix} → {r['expected_token']}  "
                     f"({r['support']}/{r['total']}, conf {float(r['confidence']):.2f})")
    return lines
