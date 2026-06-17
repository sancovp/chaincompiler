"""The controlled glyph vocabulary — the language half of GlyphSteer.

A `Vocabulary` maps named axes to glyph markers. A glyph is chosen to be (a) rare
in prose so it is a clean lexical routing key (maximal IDF, no collision with a
word), and (b) — for the dense regime — semantically aligned with its axis so its
*learned direction* nudges the chunk vector the way we intend.

The vocabulary is the gate: an annotation code is only as valid as the glyphs the
vocabulary knows. Unknown glyphs are dropped on parse (the same "syntax-only"
discipline the ChainCompiler `*CC` compilers use — we validate the form, never the
content). A code is a HoneyC chain, so `to_honeyc` emits chain notation.
"""
from __future__ import annotations

from dataclasses import dataclass, field

# the in-band separator between clean text and the glyph code (rare, non-prose)
SEP = " ⁣"  # INVISIBLE SEPARATOR — present in the byte stream, unobtrusive


@dataclass(frozen=True)
class Axis:
    """One steerable dimension with TWO regime-appropriate renderings.

    `glyph`  — the dense marker (an emoji). The embedding model tokenizes it and it
               carries a learned direction; it is non-ASCII so it never collides with
               a prose word.
    `tag`    — the lexical marker (an ASCII sentinel, e.g. `gsxnegative`). FTS5's
               unicode61 tokenizer DROPS emoji (verified), so the lexical facet must
               be an ASCII single-token sentinel. Auto-derived from `name` if omitted.
    """
    name: str
    glyph: str
    description: str = ""
    tag: str = ""

    def __post_init__(self) -> None:
        if not self.tag:
            object.__setattr__(self, "tag", default_tag(self.name))


@dataclass
class Vocabulary:
    """A set of axes. Validates glyph uniqueness and lexical-cleanliness."""
    axes: list[Axis] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.validate()

    # ---- lookups -------------------------------------------------------------
    @property
    def glyphs(self) -> list[str]:
        return [a.glyph for a in self.axes]

    def by_glyph(self, glyph: str) -> Axis | None:
        return next((a for a in self.axes if a.glyph == glyph), None)

    def by_name(self, name: str) -> Axis | None:
        return next((a for a in self.axes if a.name == name), None)

    def by_tag(self, tag: str) -> Axis | None:
        return next((a for a in self.axes if a.tag == tag), None)

    @property
    def tags(self) -> list[str]:
        return [a.tag for a in self.axes]

    def tag_for(self, glyph: str) -> str | None:
        a = self.by_glyph(glyph)
        return a.tag if a else None

    def code_tags(self, code: str) -> list[str]:
        """The ASCII lexical sentinels for the glyphs present in `code`."""
        return [self.by_glyph(g).tag for g in self.parse(code)]

    # ---- validation ----------------------------------------------------------
    def validate(self) -> None:
        seen: set[str] = set()
        tags: set[str] = set()
        for a in self.axes:
            if not a.glyph:
                raise ValueError(f"axis {a.name!r} has an empty glyph")
            if a.glyph in seen:
                raise ValueError(f"duplicate glyph {a.glyph!r} (axis {a.name!r})")
            seen.add(a.glyph)
            if not is_lexically_clean(a.glyph):
                raise ValueError(
                    f"glyph {a.glyph!r} (axis {a.name!r}) is not lexically clean: "
                    "a marker must be non-ASCII / non-alphanumeric so it never "
                    "collides with a prose token in the lexical index")
            if not is_fts_token(a.tag):
                raise ValueError(
                    f"tag {a.tag!r} (axis {a.name!r}) is not a single FTS token: it "
                    "must be one ASCII-alphanumeric run (FTS5 indexes it; emoji don't)")
            if a.tag in tags:
                raise ValueError(f"duplicate tag {a.tag!r} (axis {a.name!r})")
            tags.add(a.tag)

    # ---- code (de)serialization ---------------------------------------------
    def code(self, glyphs: list[str]) -> str:
        """Join glyphs into a compact, order-preserving, de-duplicated code."""
        out: list[str] = []
        for g in glyphs:
            if self.by_glyph(g) and g not in out:
                out.append(g)
        return "".join(out)

    def parse(self, code: str) -> list[str]:
        """Extract the known glyphs from a code string (unknown glyphs dropped)."""
        return [g for g in self.glyphs if g in code]

    def glyphs_in(self, text: str) -> list[str]:
        """Which vocabulary glyphs appear anywhere in `text` (order of vocab)."""
        return [g for g in self.glyphs if g in text]

    def strip(self, text: str) -> str:
        """Remove every vocabulary glyph (and the separator) from `text`."""
        for g in self.glyphs:
            text = text.replace(g, "")
        return text.replace(SEP.strip(), "").replace("⁣", "")

    def to_honeyc(self, code: str) -> str:
        """Render a code as a HoneyC chain (`a→b→c`) — the compiler bridge."""
        return "→".join(self.parse(code))


def is_lexically_clean(glyph: str) -> bool:
    """A glyph is clean iff it contains no ASCII alphanumeric character.

    That guarantees it can never tokenize to (or collide with) a prose word — it is
    near-orthogonal to prose in the dense regime and inert in the lexical one.
    """
    return bool(glyph) and not any(c.isascii() and c.isalnum() for c in glyph)


def is_fts_token(tag: str) -> bool:
    """A lexical sentinel must be a single ASCII-alphanumeric run (one FTS5 token)."""
    return bool(tag) and tag.isascii() and tag.isalnum()


def default_tag(name: str) -> str:
    """Derive a rare single-token ASCII sentinel from an axis name (`gsx<name>`)."""
    return "gsx" + "".join(c for c in name.lower() if c.isascii() and c.isalnum())


# A ready-made sentiment vocabulary — the strongest dense case (emoji *are* how
# humans encode sentiment, so the learned directions are clean; Novak 2015).
SENTIMENT = Vocabulary([
    Axis("positive", "\U0001F60A", "positive / approving / happy sentiment"),
    Axis("negative", "\U0001F621", "negative / angry / disapproving sentiment"),
    Axis("urgent",   "\U0001F525", "urgent / hot / high-priority"),
    Axis("question", "❓",      "open question / unresolved"),
    Axis("caution",  "⚠️", "warning / caution / risk"),
])

# A ready-made QUALITY-GRADE vocabulary — an ordered set of grades an LLM assigns to
# corpus chunks ("what's good and what isn't"). This is a *lexical-facet* axis: grading
# is a label you filter & display by, NOT a sentiment/semantic direction (a correct chunk
# can be grim; an upbeat chunk can be junk). Each grade has an integer `rank` for ordering.
GRADE = Vocabulary([
    Axis("excellent", "\U0001F3C6", "authoritative, correct, well-supported — A"),  # 🏆
    Axis("good",      "✅",     "solid and usable — B"),                          # ✅
    Axis("fair",      "⚠️", "usable with caveats / unverified — C"),        # ⚠️
    Axis("poor",      "❌",     "wrong, unsafe, or misleading — D/F"),            # ❌
])
# grade ordering (best→worst), by glyph — for sorting/Display, not validation
GRADE_RANK = {"\U0001F3C6": 0, "✅": 1, "⚠️": 2, "❌": 3}


def grade_label(vocab: Vocabulary, code: str) -> str:
    """Human badge for a chunk's grade code, e.g. '🏆 excellent'."""
    parts = [f"{g} {vocab.by_glyph(g).name}" for g in vocab.parse(code)]
    return ", ".join(parts) if parts else "(ungraded)"
