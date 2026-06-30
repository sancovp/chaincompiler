"""forge.py — the generic compiler-compiler core (the "forge a language" move).

This is the machine the *CC are *made FROM* (META-APE spec §3: ACCC/CORCC/SCCC import CC). A forged
language = a rulecatcher SCOPE holding a ratified grammar; `forge` mints one, `gate_language` enforces it,
`grammar` reads it back, `package_skill` wraps a compiled body as a publishable `<name>/SKILL.md`. Each
*CC calls these with its own chain-kind prefix + render/parse and adds nothing to the mechanism.

CC imports only DOWN (APE + rulecatcher); it never imports the *CC.
"""
from __future__ import annotations

from dataclasses import dataclass

from prompt_engineering import write_skill, grammar_lines, learn
from prompt_engineering.grammar import gate as _gate
from rulecatcher.db import connect, list_rules


@dataclass
class Language:
    """A forged language: a rulecatcher scope holding a ratified grammar."""
    name: str
    scope: str
    db: str
    rule_count: int


def forge(kind: str, name: str, examples: list[str], *, db: str, strict: bool = False) -> Language:
    """Mint a `kind` language for `name` from example chains (scope = `<kind>:<name>`).

    strict=False → learn the SHAPE only (next_kind): any vocabulary is allowed.
    strict=True  → also pin the vocabulary (next_token): the gate enforces domain-specific tokens.
    """
    scope = f"{kind}:{name}"
    rule_types = ("next_kind", "next_token") if strict else ("next_kind",)
    with connect(db) as cx:
        adopted = learn(cx, examples, scope=scope, rule_types=rule_types, label=f"forge:{name}")
    return Language(name=name, scope=scope, db=db, rule_count=len(adopted))


def gate_language(language: Language, candidate: str) -> tuple[list, list]:
    """Lint a candidate chain against a forged language's ratified grammar."""
    with connect(language.db) as cx:
        return _gate(cx, candidate, scope=language.scope)


def grammar(language: Language) -> list[str]:
    """The ratified grammar lines of a forged language."""
    with connect(language.db) as cx:
        return grammar_lines(list_rules(cx, "adopted", scope=language.scope))


def package_skill(name: str, body: str, *, out_dir: str, description: str,
                  extra: dict | None = None):
    """Wrap a compiled chain body as a publishable `<name>/SKILL.md` package."""
    return write_skill(name, description, body, out_dir=out_dir, extra=extra)


__all__ = ["Language", "forge", "gate_language", "grammar", "package_skill"]
