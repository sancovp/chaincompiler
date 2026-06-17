"""The annotation pass — the LLM/judge half that writes the glyph sidecar.

An `Annotator` reads a chunk's clean text and returns the axes that apply. Two
implementations:

  RuleAnnotator  — deterministic predicates (no LLM). Reproducible; the CI/test pass.
  LLMAnnotator   — an injectable judge callable. The real research pass; the judge
                   returns a glyph-code string which is parsed back THROUGH the
                   vocabulary (unknown glyphs dropped — the vocab is the gate).

The annotation pass over a whole corpus is a ChainCompiler skillchain (SC); these
classes are the per-chunk step it runs.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Protocol

from .vocab import Vocabulary


@dataclass(frozen=True)
class Annotation:
    """One applied axis: which axis fired and the glyph it contributes."""
    axis: str
    glyph: str


class Annotator(Protocol):
    def annotate(self, text: str) -> list[Annotation]: ...


class RuleAnnotator:
    """Deterministic annotation by predicate. `rules: {glyph: text -> bool}`."""

    def __init__(self, vocab: Vocabulary, rules: dict[str, Callable[[str], bool]]):
        self.vocab = vocab
        unknown = [g for g in rules if vocab.by_glyph(g) is None]
        if unknown:
            raise ValueError(f"rules reference glyphs not in the vocabulary: {unknown}")
        self.rules = rules

    def annotate(self, text: str) -> list[Annotation]:
        out: list[Annotation] = []
        for glyph, pred in self.rules.items():
            if pred(text):
                axis = self.vocab.by_glyph(glyph)
                out.append(Annotation(axis.name, glyph))
        return out

    @classmethod
    def keyword(cls, vocab: Vocabulary, keywords: dict[str, list[str]]) -> "RuleAnnotator":
        """Convenience: `{glyph: [words]}` → case-insensitive substring rules."""
        def make(words: list[str]) -> Callable[[str], bool]:
            low = [w.lower() for w in words]
            return lambda t, low=low: any(w in t.lower() for w in low)
        return cls(vocab, {g: make(ws) for g, ws in keywords.items()})


class LLMAnnotator:
    """Annotation by an injected judge: `judge(text, vocab) -> glyph_code_str`."""

    def __init__(self, vocab: Vocabulary, judge: Callable[[str, Vocabulary], str]):
        self.vocab = vocab
        self.judge = judge

    def annotate(self, text: str) -> list[Annotation]:
        code = self.judge(text, self.vocab)
        out: list[Annotation] = []
        for g in self.vocab.parse(code or ""):
            axis = self.vocab.by_glyph(g)
            out.append(Annotation(axis.name, g))
        return out
