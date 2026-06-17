"""The legend — persist & accumulate LLM-authored glyph vocabularies.

A vocabulary is a *language the LLM invents*: it picks glyphs, says what each means, and
we auto-derive the lexical sentinel tag. The **legend** is that language written down —
the glyph ↔ meaning ↔ tag table — so it survives a session, travels with an index, and is
shown to whoever reads the results. `keep a legend of all` = `merge` several authored
vocabularies into one master legend.

A legend entry is `{name, glyph, tag, description}`. The tag is reproducible from the name,
so a legend round-trips exactly.
"""
from __future__ import annotations

import json
from pathlib import Path

from .vocab import Axis, Vocabulary


def to_legend(vocab: Vocabulary) -> list[dict]:
    """Serialize a vocabulary to a legend (list of glyph↔meaning↔tag entries)."""
    return [{"name": a.name, "glyph": a.glyph, "tag": a.tag, "description": a.description}
            for a in vocab.axes]


def from_legend(entries: list[dict]) -> Vocabulary:
    """Rebuild a vocabulary from a legend."""
    return Vocabulary([Axis(e["name"], e["glyph"], e.get("description", ""), e.get("tag", ""))
                       for e in entries])


def author(specs: list[dict]) -> Vocabulary:
    """LLM-authoring entrypoint: the model proposes {name, glyph, description?}; we derive
    the tag and validate. Raises on glyph/tag collisions — the vocabulary is the gate."""
    return Vocabulary([Axis(s["name"], s["glyph"], s.get("description", "")) for s in specs])


def merge(*vocabs: Vocabulary) -> Vocabulary:
    """Accumulate vocabularies into one master legend (later wins on name/glyph clash —
    deterministic, last-author-priority). Skips entries that would break validation."""
    by_name: dict[str, Axis] = {}
    by_glyph: dict[str, str] = {}     # glyph -> name (to detect cross-name reuse)
    for v in vocabs:
        for a in v.axes:
            # drop a prior axis that used this glyph under a different name
            clash = by_glyph.get(a.glyph)
            if clash and clash != a.name:
                by_name.pop(clash, None)
            by_name[a.name] = a
            by_glyph[a.glyph] = a.name
    return Vocabulary(list(by_name.values()))


def save_legend(vocab: Vocabulary, path: str | Path) -> None:
    Path(path).write_text(json.dumps(to_legend(vocab), indent=2, ensure_ascii=False),
                          encoding="utf-8")


def load_legend(path: str | Path) -> Vocabulary:
    return from_legend(json.loads(Path(path).read_text(encoding="utf-8")))


def render_legend(vocab: Vocabulary) -> str:
    """Human-readable legend block (for showing alongside search results)."""
    rows = [f"  {a.glyph}  {a.tag:16s} {a.name} — {a.description}" for a in vocab.axes]
    return "LEGEND\n" + "\n".join(rows)
