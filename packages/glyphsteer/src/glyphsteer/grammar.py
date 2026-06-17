"""Syntax consistency for glyph codes — rulecatcher under GlyphSteer.

A glyph code is a little DSL (a chain of axis markers). ChainCompiler's discipline is
that every DSL goes through **rulecatcher** (lint/gate) for syntax — so GlyphSteer's codes
do too, via `chaincompiler.bridge` (which wraps rulecatcher + HoneyC). This composes the
same engine the `*CC` compilers use; GlyphSteer doesn't reimplement linting.

Codes are gated on their **ASCII tag** rendering, never the emoji — rulecatcher's tokenizer
drops emoji exactly as FTS5 does (same lesson as the dense layer), so the lexical *tag* is
the syntactic unit. Three verdicts, mirroring rulecatcher's own:

  ok           — well-formed, canonical order
  orthogonal   — known tags, wrong order (steerable → `canonicalize` reorders to vocab order)
  syntax_break — a foreign token rulecatcher doesn't recognize (fatal; reject)

rulecatcher owns `syntax_break` (its strength: foreign-token detection). The partial-order
`orthogonal` check is deterministic here (vocab order) because n-gram grammars express a
partial order poorly. Needs the `grammar` extra (`pip install 'glyphsteer[grammar]'`).
"""
from __future__ import annotations

from dataclasses import dataclass

from .vocab import Vocabulary


@dataclass
class GlyphLint:
    """The verdict for one code: ok | orthogonal | syntax_break, plus the rulecatcher
    violations and (for orthogonal) the canonical fix."""
    verdict: str
    violations: list
    fix: str | None = None

    @property
    def ok(self) -> bool:
        return self.verdict == "ok"


def _deps():
    try:
        from chaincompiler import bridge
        from rulecatcher import db
    except ImportError as e:  # pragma: no cover - environment-dependent
        raise ImportError(
            "syntax gating needs ChainCompiler + rulecatcher. Install the extra:\n"
            "    pip install 'glyphsteer[grammar]'\n"
            "(rulecatcher is ChainCompiler's lint/gate engine.)"
        ) from e
    return bridge, db


def canonical_examples(vocab: Vocabulary) -> list[str]:
    """Teach rulecatcher the shape of a valid code: KEYWORD (-> KEYWORD)* over the tag
    alphabet, in vocab order. Full chain + adjacent pairs + singletons."""
    tags = vocab.tags
    ex: list[str] = []
    if tags:
        ex.append(" -> ".join(tags))
    ex += [f"{tags[i]} -> {tags[i + 1]}" for i in range(len(tags) - 1)]
    ex += list(tags)
    return ex


def _raw_order(vocab: Vocabulary, code: str) -> list[str]:
    """Known glyphs in the order they appear in the code string."""
    present = vocab.parse(code)                       # vocab order
    return sorted(present, key=lambda g: code.find(g))


class GlyphGrammar:
    """A rulecatcher-backed syntax gate for one vocabulary's codes.

    Learns the grammar of canonical codes once, then `lint`s any code or tag-chain.
    Holds a rulecatcher connection for its lifetime; use as a context manager or `close()`.
    """

    def __init__(self, vocab: Vocabulary, *, scope: str = "glyphsteer",
                 db_path: str = ":memory:"):
        self.vocab = vocab
        self.scope = scope
        self._bridge, _db = _deps()
        self._cm = _db.connect(db_path)
        self.conn = self._cm.__enter__()
        self.rules = self._bridge.learn(
            self.conn, canonical_examples(vocab), scope=scope, keywords=tuple(vocab.tags))

    # ---- gating --------------------------------------------------------------
    def lint_chain(self, chain: str) -> GlyphLint:
        """Gate a raw ASCII tag-chain (e.g. `gsxpositive -> gsxurgent`) — this is where
        rulecatcher catches foreign tokens (`syntax_break`)."""
        if not chain.strip():
            return GlyphLint("ok", [])
        violations, _ = self._bridge.gate(self.conn, chain, scope=self.scope)
        if any(getattr(v, "verdict", None) == "syntax_break" for v in violations):
            return GlyphLint("syntax_break", violations)
        return GlyphLint("ok", violations)

    def lint(self, code: str) -> GlyphLint:
        """Gate a glyph code: foreign-token (`syntax_break`) via rulecatcher, then
        canonical-order (`orthogonal`) via vocab order."""
        chain = " -> ".join(self.vocab.code_tags(code))
        base = self.lint_chain(chain)
        if base.verdict == "syntax_break":
            return base
        present = self.vocab.parse(code)
        if _raw_order(self.vocab, code) != present:        # known tags, wrong order
            return GlyphLint("orthogonal", base.violations, fix=self.canonicalize(code))
        return GlyphLint("ok", base.violations)

    def canonicalize(self, code: str) -> str:
        """Reorder a code's glyphs into canonical (vocabulary) order — the orthogonal fix."""
        return self.vocab.code(self.vocab.parse(code))

    def consistent(self, code: str) -> bool:
        return self.lint(code).ok

    # ---- lifecycle -----------------------------------------------------------
    def close(self) -> None:
        try:
            self._cm.__exit__(None, None, None)
        except Exception:  # pragma: no cover
            pass

    def __enter__(self) -> "GlyphGrammar":
        return self

    def __exit__(self, *exc) -> None:
        self.close()
