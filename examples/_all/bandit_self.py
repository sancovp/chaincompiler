#!/usr/bin/env python3
"""
examples/_all/bandit_self.py — the bandit does the `_all` move TO ITSELF.

`run_all.py` proves the stack composes on one outside domain. This proves the
capstone the system is FOR: the default persona (the bandit / ChainSelector) takes
its headline construct move — **roll up the AC→CoR→SC algebra and CLOSE it into a
domain-specific persona** — and applies it (1) to a real domain, then (2) to every
component it is itself composed of. The result is the homoicon: a more granular
view of the bandit, in the bandit's own closed type.

Run:  python examples/_all/bandit_self.py     (after ./install.sh)
"""
from __future__ import annotations

import tempfile
from pathlib import Path

import chaincompiler as cc

results: list[tuple[str, bool, str]] = []


def check(stage: str, ok: bool, detail: str) -> None:
    results.append((stage, ok, detail))
    print(f"  {'✓' if ok else '✗'} {stage}: {detail}")


def main() -> int:
    work = Path(tempfile.mkdtemp(prefix="bandit_self_"))
    print(f"workspace: {work}\n")

    # ── 1. the bandit rolls up ONE domain into a CLOSED chain system ─────────
    print("══ 1. roll up the algebra for a domain → a closed bandit chain system ══")
    sys = cc.roll_up_algebra(
        "triage",
        ["[Symptom] ⇒ [Scope] ⇒ |Severity|", "[Repro] ⇒ [Localize] ⇒ |Cause|"],
        db=str(work / "cc.db"), skills_dir=str(work / "skills"),
        out_dir=str(work / "dist"), persona_root=str(work / "personas"),
    )
    check("algebra closes", sys.closed, f"AC×{len(sys.ac)} ⇒ CoR:{sys.cor.parent.name} ⇒ SC:{sys.sc.parent.name}")
    check("CoR is the bandit (selector, not a flavor)", "bandit" in sys.cor.parent.name.lower(),
          sys.cor.parent.name)
    cmd = (sys.persona_dir / "CLAUDE.md").read_text()
    check("persona is an AIOS (CLAUDE.md, not SKILL.md)", (sys.persona_dir / "CLAUDE.md").exists(),
          f"{sys.persona_dir.name}/ → {sorted(p.name for p in sys.persona_dir.iterdir())}")
    check("persona carries self-KB instructions", "Build your own KB" in cmd, "kb/ + per-topic graded notes")
    check("persona carries glyphsteer-self-improve instructions",
          "Improve yourself via GlyphSteer" in cmd, "🏆-faceted Recall + promote/demote")

    # ── 2. the bandit applies the SAME move to EVERYTHING IT IS MADE OF ──────
    print("\n══ 2. hierarchicalize: roll up over the bandit's own components → self-view ══")
    view = cc.hierarchicalize(workdir=str(work / "self"))
    for s in view.systems:
        print(f"     - {s.domain:12s} closed={s.closed}  (AC×{len(s.ac)} · {s.cor.parent.name})")
    check("every component closed", all(s.closed for s in view.systems),
          f"{sum(s.closed for s in view.systems)}/{len(view.systems)} components")
    check("master self-view tree validates", view.closed and view.report["violations"] == 0,
          f"bandit-self over {len(view.systems)} parts, {view.report['violations']} violations")

    passed = sum(1 for _, ok, _ in results if ok)
    total = len(results)
    print(f"\n{'═'*60}")
    print(f"  bandit_self: {passed}/{total} checks — the bandit rolled up the algebra,")
    print(f"  closed it into a self-improving persona, and applied that to itself.")
    print(f"{'═'*60}")
    failed = [s for s, ok, _ in results if not ok]
    if failed:
        print(f"  FAILED: {failed}")
        return 1
    print("  ✓ the closed algebra is self-applying. the bandit sees itself, granularly.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
