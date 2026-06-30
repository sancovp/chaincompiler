"""ACCC — the Attention-Chain Compiler-Compiler. Made FROM ChainCompiler (spec §3: ACCC imports CC).

The compiler-compiler move: `forge` mints a *new* AC language for a task/domain (it doesn't just compile
one chain). The generic machinery (forge a rulecatcher scope, gate against it, read the grammar, wrap a
body as SKILL.md) lives in `chaincompiler.forge`; ACCC specializes it to attention chains (the `ac:` kind
+ the attention-block render). CORCC consumes these: a reasoning step embeds a forged AC.
"""
from __future__ import annotations

# made FROM CC — the generic forge core (CC re-exports APE's write_skill/learn/gate underneath):
from chaincompiler import (
    Language,
    forge as _forge,
    gate_language as _gate,
    grammar as _grammar,
    package_skill as _package,
)

from .render import attention_block, parse_ac


def forge(name: str, examples: list[str], *, db: str, strict: bool = False) -> Language:
    """Mint an AC language for `name` from example chains (CC's forge, `ac:` kind).

    strict=False  → learn the SHAPE only (next_kind): any focus vocabulary is allowed.
    strict=True   → also pin the focus vocabulary (next_token): the gate enforces
                    domain-specific foci (e.g. a debug AC must open on a Symptom).
    """
    return _forge("ac", name, examples, db=db, strict=strict)


def gate(language: Language, ac: str) -> tuple[list, list]:
    """Lint a candidate attention chain against a forged language."""
    return _gate(language, ac)


def grammar(language: Language) -> list[str]:
    return _grammar(language)


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
    return _package(name, body, out_dir=out_dir, description=desc, extra={"kind": "attention-chain"})


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
