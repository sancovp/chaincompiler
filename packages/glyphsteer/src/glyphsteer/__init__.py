"""GlyphSteer — dual-regime retrieval steering via compiled in-band glyph annotations.

A compiled controlled vocabulary of glyph markers, written onto a corpus by an LLM
annotation pass, steers retrieval in BOTH regimes at once — lexical (a rare glyph is a
maximal-IDF exact-match facet) and dense (a glyph carries a learned direction that
nudges the chunk vector) — while being STRIPPED from the returned text (the sidecar
split: indexed-form ≠ returned-form). HoneyC pointed at the index instead of Prolog.

The dense layer (`dense`, `eval.magnitude_probe`) needs the optional `dense` extra;
everything else (vocab, encode, the lexical index, the steer math) is dependency-light.
"""
from __future__ import annotations

__version__ = "0.1.0"

from .annotate import Annotation, Annotator, LLMAnnotator, RuleAnnotator
from .encode import Chunk, annotate_chunk, check_hidden, indexed_form, returned_form
from .index import assert_hidden, build_index, facet_only, search
from .legend import (author, from_legend, load_legend, merge, render_legend,
                     save_legend, to_legend)
from .grammar import GlyphGrammar, GlyphLint
from .steer import cosine, rerank, sim_eff, unit
from .vocab import (GRADE, GRADE_RANK, SENTIMENT, SEP, Axis, Vocabulary,
                    grade_label, is_lexically_clean)

__all__ = [
    "Axis", "Vocabulary", "SENTIMENT", "GRADE", "GRADE_RANK", "grade_label",
    "SEP", "is_lexically_clean",
    "Annotation", "Annotator", "RuleAnnotator", "LLMAnnotator",
    "Chunk", "indexed_form", "returned_form", "annotate_chunk", "check_hidden",
    "build_index", "search", "facet_only", "assert_hidden",
    "to_legend", "from_legend", "author", "merge", "save_legend", "load_legend",
    "render_legend", "GlyphGrammar", "GlyphLint",
    "sim_eff", "cosine", "rerank", "unit",
    "__version__",
]
