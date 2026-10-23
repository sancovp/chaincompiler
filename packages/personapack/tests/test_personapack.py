"""personapack tests: the library loads, bundles are valid, uses-them passes on
BODHISATTVA, entries seat + build a real GBA."""
from __future__ import annotations

from collections import Counter
from pathlib import Path

import pytest

import personacc as pc
import personapack as pp


def test_pack_loads_ten_entries():
    assert len(pp.PACK) == 10


def test_grade_distribution():
    counts = Counter(e.activation_grade for e in pp.PACK.values())
    assert counts == {"seed": 3, "proven-in-forge": 4, "tested-with-receipt": 3}


def test_every_entry_grade_is_valid():
    for e in pp.PACK.values():
        assert e.activation_grade in pp.GRADES


@pytest.mark.parametrize("name", sorted(pp.PACK))
def test_every_bundle_is_valid(name):
    e = pp.PACK[name]
    b = e.bundle
    assert len(b.cors) >= 1                       # a persona needs ≥1 CoR
    assert pc.lint(b) == []                        # notation is well-formed
    # uses-them PASSES (no violations) in default mode for every shipped bundle.
    violations, _ = pc.uses_them(b)
    assert violations == []


def test_uses_them_passes_on_bodhisattva():
    # the headline requirement: BODHISATTVA passes the uses-them lint.
    violations, warnings = pc.uses_them(pp.bundle("bodhisattva"))
    assert violations == []                        # passes
    # (it carries warnings — its 5 atoms don't re-list all 14 CoR moves — which is honest.)


def test_seed_bundles_are_degenerate():
    for name in ("banditchain", "thinklikeeinstein", "thinklikefeynman"):
        b = pp.bundle(name)
        assert b.blocks == ()                      # empty description blocks
        v, w = pc.uses_them(b)
        assert v == [] and w == []                 # acs = own chain -> fully wired


def test_get_and_lookups():
    assert pp.get("Bodhisattva").name == "Bodhisattva"
    assert pp.by_grade("tested-with-receipt")
    assert pp.by_domain("code")                    # samaya + paramita
    with pytest.raises(KeyError):
        pp.get("nobody")


def test_entries_carry_metadata():
    for e in pp.PACK.values():
        assert e.invocation_terms                  # every entry has handles
        assert e.provenance
        # a receipt is required exactly for the tested-with-receipt grade
        if e.activation_grade == "tested-with-receipt":
            assert e.receipt


def test_seat_returns_make_gba_kwargs():
    kw = pp.seat("samayareviewer")
    assert set(kw) == {"atoms", "blurb", "role_block", "persona"}
    assert kw["persona"].name == "SamayaReviewer"


def test_seat_smoke_builds_a_gba(tmp_path: Path):
    # a receipt-grade persona seats + builds a closed GBA (BODHISATTVA — full cues).
    from chainaios.gba import make_gba
    g = make_gba("bodhi", tmp_path / "aios", **pp.seat("bodhisattva"))
    assert g.claude_md.exists()
    assert g.closed


def test_package_every_bundle(tmp_path: Path):
    # each bundle compiles to a SKILL.md (including the empty-cue recovered personas).
    for name in pp.PACK:
        path = pc.package(pp.bundle(name), out_dir=str(tmp_path / name))
        assert path.name == "SKILL.md" and path.exists()
