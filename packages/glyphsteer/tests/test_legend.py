"""The legend: an LLM authors a glyph language, it persists, accumulates, round-trips."""
from pathlib import Path

import pytest

from glyphsteer import (author, from_legend, load_legend, merge, save_legend,
                        to_legend)


def test_llm_authors_a_vocab_tags_autoderived():
    v = author([
        {"name": "claim", "glyph": "📌", "description": "a factual assertion"},
        {"name": "evidence", "glyph": "🔬", "description": "supporting data"},
    ])
    assert v.by_name("claim").tag == "gsxclaim"          # tag derived from name
    assert v.tag_for("🔬") == "gsxevidence"


def test_legend_roundtrips_exactly():
    v = author([{"name": "risk", "glyph": "☢️", "description": "danger"}])
    v2 = from_legend(to_legend(v))
    assert to_legend(v) == to_legend(v2)


def test_author_rejects_glyph_collision():
    with pytest.raises(ValueError):
        author([{"name": "a", "glyph": "📌"}, {"name": "b", "glyph": "📌"}])


def test_merge_accumulates_a_master_legend():
    v1 = author([{"name": "claim", "glyph": "📌"}])
    v2 = author([{"name": "evidence", "glyph": "🔬"}])
    master = merge(v1, v2)
    assert {a.name for a in master.axes} == {"claim", "evidence"}


def test_merge_last_author_wins_on_glyph_reuse():
    v1 = author([{"name": "old", "glyph": "📌"}])
    v2 = author([{"name": "new", "glyph": "📌"}])   # same glyph, different name
    master = merge(v1, v2)
    assert [a.name for a in master.axes] == ["new"]   # the prior axis is dropped


def test_save_and_load(tmp_path: Path):
    v = author([{"name": "claim", "glyph": "📌", "description": "assertion"}])
    p = tmp_path / "legend.json"
    save_legend(v, p)
    loaded = load_legend(p)
    assert loaded.tag_for("📌") == "gsxclaim"
    assert loaded.by_name("claim").description == "assertion"


def test_merge_last_author_wins_on_tag_collision():
    # distinct names/glyphs can derive the SAME tag ("risk" / "Risk!" -> gsxrisk);
    # merge must evict the prior axis, not crash validation
    m = merge(author([{"name": "risk", "glyph": "☢️"}]),
              author([{"name": "Risk!", "glyph": "💀"}]))
    assert [a.name for a in m.axes] == ["Risk!"]
