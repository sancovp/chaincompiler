"""The sidecar split — the keystone of GlyphSteer.

A chunk has TWO representations that are deliberately NOT the same string:

  indexed-form  = clean_text ⊕ SEP ⊕ glyph_code     → embedded / FTS5-indexed (MATCH)
  returned-form = clean_text                          → handed to the reader (READ)

The glyph code lives ONLY in the indexed-form. It steers retrieval (lexical facet +
dense direction) and then disappears: `returned_form` is provably glyph-free. This
module owns that contract and the invariant that proves it.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .vocab import SEP, Vocabulary


@dataclass
class Chunk:
    """A unit of the corpus. `text` is ALWAYS clean; `code` is the glyph sidecar."""
    id: str
    text: str
    code: str = ""
    meta: dict = field(default_factory=dict)


def indexed_form(chunk: Chunk) -> str:
    """What gets embedded / FTS5-indexed: clean text + the glyph code."""
    return f"{chunk.text}{SEP}{chunk.code}" if chunk.code else chunk.text


def returned_form(chunk: Chunk, vocab: Vocabulary) -> str:
    """What the reader/generator sees: clean text, guaranteed glyph-free."""
    return vocab.strip(chunk.text)


def annotate_chunk(chunk: Chunk, annotator, vocab: Vocabulary, grammar=None) -> Chunk:
    """Run the annotation pass over a chunk and attach its glyph code.

    The chunk's `text` is first stripped of any stray vocabulary glyphs so the
    sidecar is the ONLY source of markers (keeps the hide-invariant total).

    If a `grammar` (glyphsteer.grammar.GlyphGrammar) is given, the code is gated for
    syntax consistency via rulecatcher: `syntax_break` raises; `orthogonal` is repaired
    to canonical order. `grammar=None` ⇒ unchanged behaviour.
    """
    clean = vocab.strip(chunk.text)
    glyphs = [a.glyph for a in annotator.annotate(clean)]
    code = vocab.code(glyphs)
    if grammar is not None:
        lint = grammar.lint(code)
        if lint.verdict == "syntax_break":
            raise ValueError(f"syntax_break in annotated code {code!r}: {lint.violations}")
        if lint.verdict == "orthogonal":
            code = lint.fix
    return Chunk(id=chunk.id, text=clean, code=code, meta=dict(chunk.meta))


def check_hidden(chunk: Chunk, vocab: Vocabulary) -> bool:
    """The hide invariant: no vocabulary glyph survives into the returned-form."""
    return vocab.glyphs_in(returned_form(chunk, vocab)) == []
