from __future__ import annotations

MBR = '[Mbr]: M*Boundary <is_a-🌸\u200d💧 ⇔ |🍯| ⇔ [Mbl]: M*Blanket <is_a-🍹'

from honeyc.normalize import normalize
from honeyc.parser import parse_text


def _triples(text: str) -> set[tuple[str, str, str]]:
    out = set()
    for s in normalize(parse_text(text)):
        if s.predicate == "mediates":
            out.add((s.subject, "mediates", f"{s.object}:{s.meta['target']}"))
        else:
            out.add((s.subject, s.predicate, s.object))
    return out


def test_normalize_mbr_matches_spec():
    t = _triples(MBR)
    # The doc's Definition-of-Done facts.
    assert ("Mbr", "has_type", "M*Boundary") in t
    assert ("Mbr", "is_a", "🌸‍💧") in t
    assert ("🍯", "bounded", "true") in t
    assert ("Mbr", "equiv", "🍯") in t
    assert ("🍯", "equiv", "Mbl") in t
    assert ("Mbl", "has_type", "M*Blanket") in t
    assert ("Mbl", "is_a", "🍹") in t
    assert ("🍯", "mediates", "Mbr:Mbl") in t


def test_reverse_relation_is_a_leaf_not_backbone():
    # 🌸‍💧 must hang off Mbr (is_a), NOT become the left operand of the next equiv.
    t = _triples(MBR)
    assert ("Mbr", "equiv", "🍯") in t
    assert ("🌸‍💧", "equiv", "🍯") not in t


def test_scope_contains_and_placeholder():
    t = _triples("[HIVE]:{ [Goal], [Worker], 📃 }")
    assert ("HIVE", "contains", "Goal") in t
    assert ("HIVE", "contains", "Worker") in t
    assert ("HIVE", "placeholder", "drilldown") in t


def test_no_terms_are_silently_dropped():
    # every entity in the chain shows up as a subject somewhere
    subjects = {s.subject for s in normalize(parse_text(MBR))}
    assert {"Mbr", "Mbl", "🍯", "🌸‍💧", "🍹"} <= subjects
