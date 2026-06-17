"""Vocabulary: glyphs are unique, lexically clean, and round-trip through codes."""
import pytest

from glyphsteer import SENTIMENT, Axis, Vocabulary, is_lexically_clean


def test_lexical_cleanliness_rejects_alphanumeric_markers():
    assert is_lexically_clean("\U0001F60A")          # emoji: clean
    assert not is_lexically_clean("A")               # ASCII letter: dirty
    assert not is_lexically_clean("k7")              # has alnum: dirty
    with pytest.raises(ValueError):
        Vocabulary([Axis("bad", "X")])               # would collide with prose


def test_duplicate_glyph_rejected():
    with pytest.raises(ValueError):
        Vocabulary([Axis("a", "\U0001F525"), Axis("b", "\U0001F525")])


def test_code_roundtrip_dedups_and_drops_unknown():
    v = SENTIMENT
    pos, fire = v.by_name("positive").glyph, v.by_name("urgent").glyph
    code = v.code([pos, fire, pos])                  # dup dropped
    assert v.parse(code) == [pos, fire] or v.parse(code) == [fire, pos]
    assert v.parse(code + "Z") == v.parse(code)      # unknown glyph ignored


def test_to_honeyc_emits_chain():
    v = SENTIMENT
    pos, fire = v.by_name("positive").glyph, v.by_name("urgent").glyph
    assert "→" in v.to_honeyc(v.code([pos, fire]))
