"""ACCC — the Attention-Chain Compiler-Compiler.

The compiler-compiler move: `forge` mints a *new* AC language for a task/domain
(it doesn't just compile one chain). Each forged language is a rulecatcher scope
holding the ratified grammar; `gate` enforces it; `prime` emits the re-injectable
block. CORCC consumes these: a reasoning step embeds a forged AC.
"""
from __future__ import annotations

from dataclasses import dataclass

from chaincompiler import write_skill
from chaincompiler.bridge import grammar_lines, learn
from chaincompiler.bridge import gate as _gate
from rulecatcher.db import connect, list_rules

from .render import attention_block, parse_ac


@dataclass
class Language:
    """A forged attention-chain language."""
    name: str
    scope: str
    db: str
    rule_count: int


def forge(name: str, examples: list[str], *, db: str, strict: bool = False) -> Language:
    """Mint an AC language for `name` from example chains.

    strict=False  → learn the SHAPE only (next_kind): any focus vocabulary is allowed.
    strict=True   → also pin the focus vocabulary (next_token): the gate enforces
                    domain-specific foci (e.g. a debug AC must open on a Symptom).
    """
    scope = f"ac:{name}"
    rule_types = ("next_kind", "next_token") if strict else ("next_kind",)
    with connect(db) as cx:
        adopted = learn(cx, examples, scope=scope, rule_types=rule_types, label=f"forge:{name}")
    return Language(name=name, scope=scope, db=db, rule_count=len(adopted))


def gate(language: Language, ac: str) -> tuple[list, list]:
    """Lint a candidate attention chain against a forged language."""
    with connect(language.db) as cx:
        return _gate(cx, ac, scope=language.scope)


def grammar(language: Language) -> list[str]:
    with connect(language.db) as cx:
        return grammar_lines(list_rules(cx, "adopted", scope=language.scope))


def package(name: str, ac: str, *, out_dir: str, description: str | None = None):
    """Compile an attention chain to a publishable `<name>/SKILL.md` package.

    The body is a markdown file carrying the AC in its custom syntax + how to use
    it. The dir/SKILL.md wrapper is just so any agent auto-loads it.
    """
    foci, held = parse_ac(ac)
    desc = description or (
        f"Attention template (how to think): attend to {', '.join(foci)}"
        + (f" → hold {held}" if held else "") + "."
    )
    body = "\n".join([
        "This is an **attention chain** — an INNER template for how to think about something "
        "(a scaffold for a section or for your thinking). Not necessarily spoken.",
        "",
        "## Chain (custom syntax)",
        "```rune",
        ac.strip(),
        "```",
        "",
        "## How to use it",
        attention_block(name, ac),
    ])
    return write_skill(name, desc, body, out_dir=out_dir, extra={"kind": "attention-chain"})


def prime(language: Language, exemplar: str) -> str:
    """The re-injectable PRIME for a forged AC language."""
    g = grammar(language)
    block = attention_block(language.name, exemplar)
    return "\n".join([
        f'# PRIME — attention-chain language "{language.name}"',
        "",
        "Direct your attention using chains of this shape. Every chain you emit is "
        "gated against the language; fix violations before continuing.",
        "",
        f"## Ratified grammar ({len(g)} rules)",
        *(g or ["(none)"]),
        "",
        "## Exemplar (compiled to an attention block)",
        block,
        "",
        "## Directive",
        "Emit attention chains in this language. End on a bounded |Held| focus.",
    ])
