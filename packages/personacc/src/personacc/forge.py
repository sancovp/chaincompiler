"""PersonaCC — the Persona Compiler-Compiler. Composes ACCC + CORCC.

Same *CC shape as ACCC / CORCC / SCCC: catch the notation, LINT it (so the model
never emits a malformed persona), compile it to a markdown body, and PACKAGE that
as `<name>/SKILL.md`. PersonaCC judges no content — only the SYNTAX and the
STRUCTURE of the bundle (the ratified definition: blocks + ACs + ≥1 CoR that uses
them).

Where it sits: ACCC forges an attention chain; CORCC forges a CoR (embedding an
AC); PersonaCC forges the whole PERSONA (a set of blocks + ACs + ≥1 CoR that uses
them) and SEATS it into `chainaios.make_gba(persona=…)`. ACCC → CORCC → PersonaCC.

The headline check is `uses_them` — the lint that makes the "…that USES them"
clause of the definition mechanically checkable. See its docstring for the rule
and the honest weakening.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import tempfile

from accc import Language as ACLanguage
from accc import forge as ac_forge
from accc import gate as ac_gate
from accc import parse_ac
from corcc import Persona, cor_chain, forge_persona, inner_template, prime as cor_prime
from chaincompiler import slugify, write_skill  # made FROM CC (CC re-exports APE's write_skill/slugify)

from .notation import Block, PersonaBundle


# ── notation helpers ─────────────────────────────────────────────────────────
def _focus_set(chains: list[str]) -> set[str]:
    """Every focus (ordered `[Focus]` term AND the `|Held|`) across the chains."""
    foci: set[str] = set()
    for ch in chains:
        try:
            ordered, held = parse_ac(ch)
        except Exception:
            continue  # malformed chains are caught by `lint`, not here
        foci.update(ordered)
        if held:
            foci.add(held)
    return foci


def _derived_focus_set(bundle: PersonaBundle) -> set[str]:
    """The union of every CoR's OWN derived chain foci (= all its move names)."""
    return _focus_set([cor_chain(cor) for cor in bundle.cors])


# ── the notation lint (syntax + structure) ───────────────────────────────────
def lint(bundle: PersonaBundle) -> list[str]:
    """Syntax/structure lint of a persona bundle's NOTATION (the *CC check).

    Checks, without judging any content:
      - every AC string is a well-formed rune attention chain (parseable, has a
        bounded `|Held|`);
      - every CoR's derived chain is well-formed;
      - the bundle has ≥1 CoR and every block has a non-empty kind.

    Returns a list of human-readable issue strings (empty = clean notation). This
    is the "is it well-formed?" gate; the "does the CoR use the ACs?" gate is the
    separate `uses_them` below.
    """
    issues: list[str] = []
    if not bundle.cors:
        issues.append("bundle has no CoR (a persona needs ≥1 CoR)")
    for i, ac in enumerate(bundle.acs):
        try:
            _, held = parse_ac(ac)
        except Exception as e:
            issues.append(f"AC[{i}] {ac!r}: not a well-formed attention chain ({e})")
            continue
        if not held:
            issues.append(f"AC[{i}] {ac!r}: no bounded |Held| convergence")
    for cor in bundle.cors:
        chain = cor_chain(cor)
        try:
            parse_ac(chain)
        except Exception as e:
            issues.append(f"CoR {cor.name!r} derived chain {chain!r}: malformed ({e})")
    for b in bundle.blocks:
        if not b.kind.strip():
            issues.append("a block has an empty kind")
    # TOTAL SYNTAXIFICATION: a chain-graded block that MELTS its own gauge is a hard
    # notation issue (folded in here). Prose blocks are only WARNINGS (soup is tolerated
    # for migration), so they ride the warnings channel of `lint_blocks` — folding them
    # in as issues would wrongly fail every migration-era bundle.
    block_issues, _block_warnings = lint_blocks(bundle)
    issues.extend(block_issues)
    return issues


# ── the language-gate registry (TYPE ⊥ SYNTAX) ───────────────────────────────
# A block is (type, LANGUAGE, string). Each chain LANGUAGE carries its own melt-gauge:
# a callable `gate(body: str) -> list[str]` returning violation strings (empty = clean).
# "rune" is the built-in honeyc Dense Rune-Chain gauge; new languages register here.

def _rune_gate(body: str) -> list[str]:
    """The 'rune' language gate = the block melt-gauge (the SAME gauge CORCC uses on a CoR).

    CORCC forges an accc Language from a CoR's canonical `cor_chain(spec)` and gates the
    spoken CoR text against it (`corcc.lint` = `ac_gate(persona.inner, cor_text)`); drift
    out of the syntax = the persona "melting". The block analogue: the block IS its own
    notation, so we forge the Language from the block's CLEAN rune skeleton (the canonical
    chain `parse_ac` recovers) and gate the RAW body against it. A clean chain equals its
    skeleton → 0 violations; a body that hides prose between foci, misplaces the `|Held|`,
    or drops a `⇒` drifts from the skeleton → the gate fires. The forge needs a scratch DB
    (the gate is only defined against a forged Language — the forge-backed check, stated
    plainly), so a throwaway temp DB is used and discarded per call.
    """
    foci, held = parse_ac(body)  # body is rune-chain-graded, so this succeeds
    canonical = " ⇒ ".join(f"[{f}]" for f in foci)
    if held:
        canonical += f" ⇒ |{held}|"
    with tempfile.TemporaryDirectory() as tmp:
        language = ac_forge("rune-block-gate", [canonical], db=str(Path(tmp) / "rune-gate.db"))
        violations, _warnings = ac_gate(language, body)
    if violations:
        return [f"{len(violations)} violation(s) vs its rune skeleton {canonical!r}"]
    return []


LANG_GATES: dict[str, callable] = {"rune": _rune_gate}


def register_lang_gate(name: str, fn) -> None:
    """Register a melt-gauge for a chain LANGUAGE: `fn(body: str) -> list[str]` (violations).

    TYPE ⊥ SYNTAX: registering a gate makes a language LINTABLE — blocks written in it
    then grade "chain" and are melt-gauged like any rune block. Until a language has a
    gate it is unlintable = soup-grade (its blocks grade "prose")."""
    LANG_GATES[name] = fn


def lint_blocks(bundle: PersonaBundle) -> tuple[list[str], list[str]]:
    """Block-level syntaxification gate → `(issues, warnings)`, dispatched by `lang`.

    For each description block, split on its `grade`:
      - "chain" → run the language's registered melt-gauge (`LANG_GATES[block.lang]`, the
        same gauge CORCC uses on a CoR). A chain block that drifts out of its language's
        syntax is a hard ISSUE.
      - "prose" → a WARNING: "unsyntactified block: <kind>" for an unparsed rune body, or
        "no gate registered for lang=<x>" for a block in an unknown (unlintable) language.
        Tolerated soup, but flagged so the migration to one-notation-all-the-way-down is
        visible.

    Mirrors `uses_them`'s (violations, warnings) split.
    """
    issues: list[str] = []
    warnings: list[str] = []
    for b in bundle.blocks:
        if b.grade == "chain":
            gate = LANG_GATES.get(b.lang)
            if gate is None:  # defensive: grade==chain implies a gate exists, but be safe
                warnings.append(f"no gate registered for lang={b.lang}")
                continue
            for v in gate(b.body):
                issues.append(f"block {b.kind!r} (lang={b.lang}) MELTS the gate: {v}")
        elif b.lang != "rune" and b.lang not in LANG_GATES:
            warnings.append(f"no gate registered for lang={b.lang}")
        else:
            warnings.append(f"unsyntactified block: {b.kind}")
    return issues, warnings


# ── the "…that USES them" lint (the headline check) ──────────────────────────
def uses_them(bundle: PersonaBundle, *, strict: bool = False) -> tuple[list[str], list[str]]:
    """Check the "…that USES them" clause of the persona definition.

    THE RULE (as ratified):
        Every CoR move name must appear as a FOCUS in at least one of the bundle's
        AC chains, OR in the CoR's OWN derived chain (`corcc.cor_chain(cor)`).

    Honest implementation note (the weakening, stated loudly). A CoR's own derived
    chain is `[m0] ⇒ [m1] ⇒ … ⇒ |m_last|` — so it ALWAYS contains every one of
    that CoR's move names. Taken literally, the "OR the CoR's own derived chain"
    escape hatch means a well-formed bundle can NEVER hard-fail. That is by design
    for the seed/proof bundles, whose ACs (their real attention atoms) legitimately
    do NOT re-list every CoR move — failing them would be wrong. So:

      - DEFAULT (`strict=False`): the escape hatch is ON. A move grounded by a real
        bundle AC is clean; a move grounded ONLY by its CoR's own derived chain is
        a WARNING ("declared but not wired to an attention chain"); a move grounded
        by NEITHER is a hard VIOLATION (only reachable via a structurally broken
        spec). This is the "weaken to a warning and SAY SO" mode.

      - STRICT (`strict=True`): the escape hatch is OFF. A move must be a focus in
        a real bundle AC or it is a VIOLATION. This is the teeth: it fires on any
        bundle whose CoR is not actually wired to its attention chains.

    Returns `(violations, warnings)` — lists of human-readable strings.
    """
    ac_foci = _focus_set(list(bundle.acs))
    violations: list[str] = []
    warnings: list[str] = []
    for cor in bundle.cors:
        own_foci = _focus_set([cor_chain(cor)])
        for move in cor.moves:
            n = move.name
            if n in ac_foci:
                continue  # grounded by a real bundle AC — fully wired
            if strict:
                violations.append(
                    f"{cor.name}.{n}: CoR move is not a focus in any bundle AC (strict)")
            elif n in own_foci:
                warnings.append(
                    f"{cor.name}.{n}: grounded only by the CoR's own derived chain, "
                    "not surfaced as a focus in any bundle AC")
            else:
                violations.append(
                    f"{cor.name}.{n}: move appears in neither the bundle ACs nor the "
                    "CoR's own derived chain (structurally broken)")
    return violations, warnings


# ── forge ────────────────────────────────────────────────────────────────────
@dataclass
class ForgedBundle:
    """The compiled artifacts of a persona bundle."""
    bundle: PersonaBundle
    ac_languages: list[ACLanguage]      # one forged AC language per bundle AC (via ACCC)
    personas: list[Persona]             # one forged persona per CoR (via CORCC)
    uses_violations: list[str] = field(default_factory=list)
    uses_warnings: list[str] = field(default_factory=list)
    notation_issues: list[str] = field(default_factory=list)  # includes any melted chain-block issues
    block_warnings: list[str] = field(default_factory=list)    # prose (unsyntactified) blocks — tolerated

    @property
    def name(self) -> str:
        return self.bundle.name

    @property
    def clean(self) -> bool:
        return not self.notation_issues and not self.uses_violations


def forge_bundle(bundle: PersonaBundle, *, db: str, strict_uses: bool = False) -> ForgedBundle:
    """Forge a persona bundle: forge each AC via ACCC, forge each CoR via CORCC.

    - Each AC string is forged into its own `accc` Language (ACCC → the `ac:` kind).
    - Each CoR (`corcc.PersonaSpec`) is forged into a `corcc.Persona` (which itself
      forges the CoR's inner attention chain — CORCC composes ACCC).
    - The bundle is linted (`lint`) for notation validity and gated by `uses_them`
      for the "…that uses them" clause.

    `strict_uses` selects the `uses_them` mode (see its docstring). This never
    raises on a lint failure — it records the issues on the `ForgedBundle` so the
    caller decides; that mirrors the other *CC (lint reports, it does not throw).
    """
    notation_issues = lint(bundle)                 # already includes melted chain-block issues
    _block_issues, block_warnings = lint_blocks(bundle)  # recover the prose-block warnings
    ac_languages = [
        ac_forge(f"{slugify(bundle.name)}-ac{i}", [ac], db=db)
        for i, ac in enumerate(bundle.acs)
    ]
    personas = [forge_persona(cor, db=db) for cor in bundle.cors]
    violations, warnings = uses_them(bundle, strict=strict_uses)
    return ForgedBundle(
        bundle=bundle, ac_languages=ac_languages, personas=personas,
        uses_violations=violations, uses_warnings=warnings, notation_issues=notation_issues,
        block_warnings=block_warnings,
    )


def _safe_prime(persona: Persona) -> str:
    """CORCC's persona PRIME, with a cue-free fallback.

    Some CoR specs recovered from the proof GBAs have no per-move `cues` persisted
    (the original build scripts weren't retained — honest under-specification, not
    invented). CORCC's cue-based paragraph skeleton can't render those, so fall
    back to a cue-free prime (inner chain + the ordered moves)."""
    try:
        return cor_prime(persona)
    except Exception:
        spec = persona.spec
        moves = " → ".join(m.name for m in spec.moves)
        return "\n".join([
            f'# PRIME — persona "{spec.name}"',
            f"({spec.blurb})" if spec.blurb else "",
            "",
            "## Inner attention chain (use silently)",
            inner_template(persona),
            "",
            "## Chain-of-reasoning moves (perform in order; the last is the held convergence)",
            moves,
            "",
            "_(per-move cue phrases were not persisted for this recovered persona.)_",
        ])


# ── render / package ─────────────────────────────────────────────────────────
def render_blocks(bundle: PersonaBundle) -> str:
    """The description blocks rendered as markdown sections (one `##` per block)."""
    out: list[str] = []
    for b in bundle.blocks:
        title = b.kind.replace("_", " ").strip().title()
        out.append(f"## {title}")
        out.append("")
        out.append(b.body.strip())
        out.append("")
    return "\n".join(out).strip()


def role_block(bundle: PersonaBundle) -> str | None:
    """Assemble a CLAUDE.md-ready role block from the description blocks.

    Returns None when the bundle carries no blocks (a degenerate persona whose
    identity is its CoR — `make_gba` then derives the role from the persona moves).
    """
    if not bundle.blocks:
        return None
    header = f"# {bundle.name}"
    if bundle.blurb:
        header += f"\n\n{bundle.blurb}"
    body = render_blocks(bundle)
    return f"{header}\n\n{body}".strip()


def package(bundle: PersonaBundle, out_dir: str, *, db: str | None = None,
            description: str | None = None) -> Path:
    """Compile the persona bundle to a publishable `<name>/SKILL.md` package.

    The body renders: the description blocks as sections + the AC set + each CoR's
    re-injectable PRIME (from CORCC). Written via `chaincompiler.write_skill`.
    A `db` is needed to forge each CoR's prime; if omitted a temp DB is used.
    """
    desc = description or (
        f"Persona (blocks + attention chains + chain-of-reasoning): {bundle.blurb}."
        if bundle.blurb else f"Persona bundle {bundle.name}."
    )

    def _build(db_path: str) -> str:
        personas = [forge_persona(cor, db=db_path) for cor in bundle.cors]
        parts: list[str] = [
            "This is a **persona** — a set of DESCRIPTION BLOCKS, a set of ATTENTION CHAINS "
            "(how to think), and one or more CHAINS OF REASONING (spoken, ending in a decision) "
            "that use them. Adopt the blocks; think along the attention chains; perform the CoR.",
            "",
        ]
        blocks_md = render_blocks(bundle)
        if blocks_md:
            parts += ["# Description blocks", "", blocks_md, ""]
        parts += ["# Attention chains (how to think — silent templates)", ""]
        if bundle.acs:
            parts.append("```rune")
            parts += [ac.strip() for ac in bundle.acs]
            parts.append("```")
        else:
            parts.append("_(none — this persona's chains are carried by its CoR)_")
        parts.append("")
        parts += ["# Chains of reasoning (spoken; you MUST perform these, in order)", ""]
        for p in personas:
            parts.append(_safe_prime(p))
            parts.append("")
        return "\n".join(parts).rstrip()

    if db is None:
        with tempfile.TemporaryDirectory() as tmp:
            body = _build(str(Path(tmp) / "personacc.db"))
    else:
        body = _build(db)
    return write_skill(bundle.name, desc, body, out_dir=out_dir, extra={"kind": "persona-bundle"})


# ── seat — the make_gba seam ─────────────────────────────────────────────────
def seat(bundle: PersonaBundle) -> dict:
    """Return exactly the kwargs `chainaios.make_gba(domain, root, **seat(bundle))` accepts.

        {
          "atoms":      list(bundle.acs),   # the attention chains become the GBA's atoms
          "blurb":      bundle.blurb,
          "role_block": role_block(bundle), # rendered from the description blocks (or None)
          "persona":    bundle.cors[0],     # the first CoR is seated as the GBA's CoR
        }

    FUTURE WORK: only `cors[0]` is seated. A GBA seats exactly one CoR persona
    today (the melt-gauge is one ordered move-chain), so multi-CoR bundles have
    their remaining CoRs compiled into the SKILL.md by `package` but not seated.
    Seating additional CoRs (e.g. as sub-personas / a routed ensemble) is future
    work — it needs a `make_gba` that carries more than one persona seam.
    """
    return {
        "atoms": list(bundle.acs),
        "blurb": bundle.blurb,
        "role_block": role_block(bundle),
        "persona": bundle.cors[0],
    }
