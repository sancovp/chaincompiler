"""PersonaCC tests: bundle validity, the uses-them lint, notation lint, package, seat.

Self-contained — uses corcc seed CoRs (no personapack dependency). The
"passes on BODHISATTVA" half of the uses-them requirement is tested in
personapack (where BODHISATTVA lives)."""
from __future__ import annotations

from pathlib import Path

import pytest

from corcc import cor_chain
from corcc.notation import EINSTEIN, BANDIT

import personacc as pc
from personacc import Block, PersonaBundle


# ── a helper: a well-wired bundle whose acs = the CoR's own derived chain ──────
def _wired(spec=EINSTEIN, blocks=()):
    return PersonaBundle(name=spec.name, blocks=blocks, acs=(cor_chain(spec),),
                         cors=(spec,), blurb=spec.blurb)


def test_bundle_requires_at_least_one_cor():
    with pytest.raises(ValueError):
        PersonaBundle(name="Empty", blocks=(), acs=("[A] ⇒ [B] ⇒ |C|",), cors=(), blurb="")


def test_block_kind_is_extensible():
    # ANY kind string is legal (the template-template rule) — no closed enum.
    b = Block(kind="a-brand-new-kind", body="hi")
    assert b.kind == "a-brand-new-kind"
    with pytest.raises(ValueError):
        Block(kind="  ", body="x")


def test_blocks_render_as_sections():
    bundle = _wired(blocks=(Block("role", "You are X."), Block("invocation_terms", "a · b")))
    md = pc.render_blocks(bundle)
    assert "## Role" in md and "You are X." in md
    assert "## Invocation Terms" in md and "a · b" in md
    rb = pc.role_block(bundle)
    assert rb is not None and "# ThinkLikeEinstein" in rb


def test_role_block_none_when_no_blocks():
    assert pc.role_block(_wired(blocks=())) is None


def test_notation_lint_catches_malformed_ac():
    good = _wired()
    assert pc.lint(good) == []
    broken = PersonaBundle(name="Bad", blocks=(), acs=("this is not a rune chain",),
                           cors=(BANDIT,), blurb="")
    issues = pc.lint(broken)
    assert issues, "a malformed AC string should be flagged by the notation lint"


def test_uses_them_clean_when_acs_cover_moves():
    # acs = the CoR's own derived chain -> every move is a focus in a real AC.
    v, w = pc.uses_them(_wired())
    assert v == [] and w == []


def test_uses_them_fires_on_deliberately_broken_bundle():
    # acs do NOT cover the CoR's moves -> strict fires as VIOLATIONS, default as WARNINGS.
    broken = PersonaBundle(name="Broken", blocks=(),
                           acs=("[Alpha] ⇒ [Beta] ⇒ |Gamma|",), cors=(EINSTEIN,), blurb="")
    v_strict, _ = pc.uses_them(broken, strict=True)
    assert v_strict, "strict uses-them must fire on a CoR not wired to any AC"
    v_default, w_default = pc.uses_them(broken)              # weakened mode
    assert v_default == [] and w_default, "default mode reports warnings, not violations"


def test_package_writes_skill_md(tmp_path: Path):
    path = pc.package(_wired(blocks=(Block("role", "You are Einstein."),)), out_dir=str(tmp_path))
    assert path.name == "SKILL.md"
    text = path.read_text()
    assert "persona-bundle" in text                 # frontmatter kind
    assert "Attention chains" in text               # the AC set section
    assert "PRIME" in text                          # each CoR's prime is rendered
    assert cor_chain(EINSTEIN) in text              # the CoR chain is present


def test_seat_returns_make_gba_kwargs():
    kw = pc.seat(_wired(blocks=(Block("role", "You are Einstein."),)))
    assert set(kw) == {"atoms", "blurb", "role_block", "persona"}
    assert kw["atoms"] == [cor_chain(EINSTEIN)]
    assert kw["persona"] is EINSTEIN
    assert kw["role_block"] is not None


# ── block grades + the block melt-gauge (TOTAL SYNTAXIFICATION) ────────────────
def test_block_grades_chain_and_prose():
    chain = Block("wrapper", "[Output] ⇒ [Adorn] ⇒ |Wrapped|")
    assert chain.is_chain and chain.grade == "chain"
    prose = Block("role", "You are a helpful wrapper.")
    assert not prose.is_chain and prose.grade == "prose"


def test_lint_blocks_chain_clean_prose_warns():
    bundle = _wired(blocks=(Block("wrapper", "[Output] ⇒ [Adorn] ⇒ |Wrapped|"),
                            Block("role", "You are X.")))
    issues, warnings = pc.lint_blocks(bundle)
    assert issues == []                                   # the chain block lints clean
    assert any("unsyntactified block: role" in w for w in warnings)
    # a clean chain block + prose warnings ⇒ lint() stays empty (prose is tolerated soup).
    assert pc.lint(bundle) == []


def test_lint_blocks_malformed_chain_fires_gate():
    bad = _wired(blocks=(Block("wrapper", "[Output] ⇒ [Adorn] this then blah ⇒ |Wrapped|"),))
    assert bad.blocks[0].grade == "chain"                 # it still parses as a chain…
    issues, _ = pc.lint_blocks(bad)
    assert issues, "a malformed chain-block must fire its melt-gauge"
    assert pc.lint(bad), "…and the melted-block issue folds into lint()"


def test_unknown_lang_grades_prose_until_gate_registered():
    # TYPE ⊥ SYNTAX: an unregistered language is unlintable = soup-grade, until a gate lands.
    from personacc.forge import LANG_GATES, register_lang_gate
    b = Block("wrapper", "A -> B -> C", lang="arrowlang")
    assert b.grade == "prose"                             # no gate registered yet
    _, warnings = pc.lint_blocks(_wired(blocks=(b,)))
    assert any("no gate registered for lang=arrowlang" in w for w in warnings)
    try:
        register_lang_gate("arrowlang", lambda body: [] if "->" in body else ["missing ->"])
        assert b.grade == "chain"                         # now lintable ⇒ chain-graded
        issues, _ = pc.lint_blocks(_wired(blocks=(b,)))
        assert issues == []                               # "A -> B -> C" contains "->" ⇒ clean
    finally:
        LANG_GATES.pop("arrowlang", None)


def test_seat_smoke_builds_a_gba(tmp_path: Path):
    # seat() kwargs actually drive make_gba into a closed GBA (uses EINSTEIN — full cues).
    from chainaios.gba import make_gba
    bundle = _wired(blocks=(Block("role", "You are Einstein."),))
    g = make_gba("physics", tmp_path / "aios", **pc.seat(bundle))
    assert g.claude_md.exists()
    assert g.closed
