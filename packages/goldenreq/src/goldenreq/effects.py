"""effects.py — the promotion effects, dispatched ONLY on an accepted verdict.

`dispatch` routes an accepted request to its effect by `kind`. An effect is the
thing the gauge was NOT allowed to do itself; here it runs because a handler
accepted. Each returns an `outcome` dict that verdict.py stores in the record.

Honesty rule: two effects are real (they have a testable local target), two are
stubs (they'd need cross-package wiring we cannot exercise here). The stubs
raise `NotImplementedError` and point at the exact upstream call to make — we do
NOT fake an integration we can't test.
"""
from __future__ import annotations

from pathlib import Path

# the personapack activation_grade ladder, BEST → WORST.
# Mirror of personapack.entry.GRADES (kept as a literal so goldenreq stays
# dependency-free; a drift here is caught by the pack-grade-bump test).
PACK_GRADES: tuple[str, ...] = ("tested-with-receipt", "proven-in-forge", "seed")


def dispatch(request: dict, *, by: str, **kwargs) -> dict:
    """Route an ACCEPTED request to its promotion effect. Returns the outcome dict."""
    kind = request.get("kind")
    if kind == "chain-golden":
        return mark_chain_golden(request, by=by, **kwargs)
    if kind == "pack-grade-bump":
        new_grade = bump_pack_grade(request.get("requested_promotion") or _current_from(request))
        return {"effect": "pack-grade-bump", "new_grade": new_grade,
                "note": "pure result — personapack applies it to the PackEntry"}
    if kind == "rule-adopt":
        return adopt_rule(request, by=by, **kwargs)
    if kind == "template-promote":
        return promote_template(request, by=by, **kwargs)
    raise ValueError(f"no effect for kind {request.get('kind')!r}")


def _current_from(request: dict) -> str:
    # if requested_promotion wasn't a grade, fall back to the weakest rung
    return "seed"


# ── chain-golden: append an ACCEPTED-BY marker into the GBA KB note ──────────
def mark_chain_golden(request: dict, *, by: str, **_) -> dict:
    """Write the golden marker into the GBA KB.

    `candidate_id` is the path to the graded KB note (a `kb/<topic>.md`, headed
    with a `glyphs:` grade line — see chainaios bandit.kb_instructions). We
    APPEND an ACCEPTED-BY line; we NEVER rewrite the agent's own notes. The
    marker is what turns "the gauge claims 🏆🏆" into "a handler certified it
    golden" — the thing self-folding used to do without authority.
    """
    note = Path(request["candidate_id"])
    if not note.exists():
        raise FileNotFoundError(f"KB note not found: {note}")
    marker = (f"\nACCEPTED-BY: {by} — goldenized on request {request['request_id']} "
              f"(promotion: {request.get('requested_promotion')}); "
              f"evidence: {', '.join(request.get('evidence', [])) or 'none'}. 🏆🏆 → golden\n")
    with open(note, "a", encoding="utf-8") as f:
        f.write(marker)
    return {"effect": "chain-golden", "kb_note": str(note), "marker": marker.strip()}


# ── pack-grade-bump: a PURE function personapack applies itself ──────────────
def bump_pack_grade(current_grade: str) -> str:
    """Return the next-higher personapack `activation_grade`, or the same grade
    if already at the top. PURE — personapack constructs the new PackEntry with it.

    Ladder (best→worst): tested-with-receipt > proven-in-forge > seed.
    A bump moves ONE rung toward tested-with-receipt.
    """
    if current_grade not in PACK_GRADES:
        raise ValueError(f"grade {current_grade!r} not in {PACK_GRADES}")
    i = PACK_GRADES.index(current_grade)
    return PACK_GRADES[max(0, i - 1)]


# ── honest stubs: real cross-package integration we cannot test here ─────────
def adopt_rule(request: dict, *, by: str, **_) -> dict:
    """STUB. A real rule-adopt would call rulecatcher's adopt path:

        rulecatcher.engine.adopt_rules(connection, rule_ids, actor=by,
                                       source="goldenreq", reason=<verdict reason>)

    (see base/chaincompiler/packages/rulecatcher/src/rulecatcher/engine.py:90).
    That needs a live rulecatcher sqlite `Connection` and real candidate rule ids
    threaded through the request — wiring goldenreq cannot construct or exercise
    in isolation. Not faked.
    """
    raise NotImplementedError(
        "rule-adopt: wire request.candidate_id (rule ids) + a rulecatcher "
        "Connection to rulecatcher.engine.adopt_rules(actor=by, source='goldenreq'). "
        "Deliberately unimplemented — no fake integration.")


def promote_template(request: dict, *, by: str, **_) -> dict:
    """STUB. A real template-promote would move a forged language/template from
    candidate into the canonical set (the chainaios `construct_language` /
    template store). That store's promotion API is not defined yet, so there is
    nothing honest to call. Not faked.
    """
    raise NotImplementedError(
        "template-promote: no canonical-template promotion API exists to call "
        "yet; when one does, dispatch request.candidate_id to it here. "
        "Deliberately unimplemented — no fake integration.")
