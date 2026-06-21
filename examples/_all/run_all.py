#!/usr/bin/env python3
"""
examples/_all — THE everything example.

One domain ("reviewer": a cognition system that reviews & grades) flowed through
EVERY package in the monorepo, end to end, each stage asserting, ending in a
verifiable round-trip. This is the dogfood: if `./install.sh` worked, this runs
green from a clean clone and proves the whole stack composes on a single artifact.

    persona  → AIOS dir (legend + gated chain + SKILL.md)         [chaincompiler.persona]
    honeyc   → parse a dense-rune chain into statements           [honeyc]
    gate     → rulecatcher admits valid syntax, rejects foreign   [chaincompiler.bridge]
    construct→ AC + CoR + SC minted in one call                   [accc · corcc · sccc]
    organize → a cat-breadcrumb SkillTree, materialized+validated [skilltree]
    steer    → glyph-faceted retrieval; markers hidden on return  [glyphsteer]
    interpret→ walk the tree + run a chain-dialect snippet        [si]

Every operation produces or consumes the ONE type — a skill dir (`<name>/SKILL.md`).

Run:  python examples/_all/run_all.py     (after ./install.sh)
"""
from __future__ import annotations

import tempfile
from pathlib import Path

# the whole stack
import chaincompiler as cc
from chaincompiler.persona import compile_persona
from rulecatcher.db import connect
import honeyc
import glyphsteer as gs
from glyphsteer import SENTIMENT, Chunk, RuleAnnotator
from skilltree import SkillTree, TreeNode, materialize, validate, build_index, search
import si

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
BIZZIBEE = REPO / "packages" / "chaincompiler" / "examples" / "bizzibee.txt"

results: list[tuple[str, bool, str]] = []


def check(stage: str, ok: bool, detail: str) -> None:
    results.append((stage, ok, detail))
    mark = "✓" if ok else "✗"
    print(f"  {mark} {stage}: {detail}")


def section(n: int, title: str) -> None:
    print(f"\n══ {n}. {title} ══")


def main() -> int:
    work = Path(tempfile.mkdtemp(prefix="cc_all_"))
    db = str(work / "cc.db")
    skills = work / "skills"; skills.mkdir()
    dist = work / "dist"; dist.mkdir()
    print(f"workspace: {work}")

    # ── 1. persona → AIOS dir ────────────────────────────────────────────────
    section(1, "persona compiler — a glyph-persona program → legend + gated chain + SKILL.md")
    persona_out = work / "persona"
    pres = compile_persona(BIZZIBEE.read_text(), out_dir=persona_out)
    n_axes = pres["axes"]
    skill_md = pres["skill"]
    wrote = Path(skill_md).exists()
    check("persona→legend", n_axes >= 3, f"{n_axes} glyph axes extracted")
    check("persona→SKILL.md", wrote, f"wrote {Path(skill_md).name} (+ {pres['steps']} ⚙️ steps, gate={pres['gate'].get('verdict','?')})")

    # ── 2. honeyc — compile a dense-rune chain ───────────────────────────────
    section(2, "honeyc — parse a dense-rune chain into normalized statements")
    rune = "[Claim] 🌸 [Evidence] 🍯 |Grade|"
    stmts = honeyc.normalize(honeyc.parse_text(rune))
    check("honeyc parse", len(stmts) >= 1, f"{len(stmts)} statement(s) from {rune!r}")

    # ── 3. rulecatcher — the gate (admit valid, reject foreign) ──────────────
    section(3, "rulecatcher — learn a grammar, admit valid syntax, flag malformed")
    with connect(str(work / "gate.db")) as cx:
        cc.learn(cx, ["[A] ⇒ [B] ⇒ [C] ⇒ |D|"], scope="reviewdsl")
        good_viol, _ = cc.gate(cx, "[P] ⇒ [Q] ⇒ |R|", scope="reviewdsl")
        bad_viol, _ = cc.gate(cx, "[P] [Q] ⇒ |R|", scope="reviewdsl")
    check("gate admits valid", len(good_viol) == 0, f"valid chain → {len(good_viol)} violations")
    check("gate flags malformed", len(bad_viol) >= 1, f"missing-arrow chain → {len(bad_viol)} violation(s)")

    # ── 4. construct_language — AC + CoR + SC in one call ────────────────────
    #     No cor_persona ⇒ the DEFAULT persona = corcc.BANDIT = the ChainSelector.
    #     The default agent doesn't get a flavor; it gets the selector itself.
    section(4, "construct_language — mint reviewer AC + CoR + SC; the DEFAULT CoR is the bandit")
    bundle = cc.construct_language(
        "reviewer",
        ac_chain="[Claim] ⇒ [Evidence] ⇒ |Grade|",
        db=db, skills_dir=str(skills), out_dir=str(dist),
    )
    paths = {"ac": Path(bundle.ac), "cor": Path(bundle.cor), "sc": Path(bundle.sc)}
    for kind, p in paths.items():
        check(f"minted {kind}", p.exists() and p.name == "SKILL.md", str(p.relative_to(work)))
    check("default persona = BanditChain (the selector)", "bandit" in paths["cor"].parent.name.lower(),
          f"CoR is {paths['cor'].parent.name} (select↔construct, not a flavor)")

    # ── 5. skilltree — organize into a cat-breadcrumb tree, validate ─────────
    section(5, "SkillTree — organize the cognition into a breadcrumb tree, materialize + validate")
    tree = SkillTree(TreeNode("reviewer", "sc", description="review & grade a claim", children=[
        TreeNode("evidence", "cor", description="weigh the evidence for a claim", children=[
            TreeNode("claim-attn", "ac", description="attend to the claim under review"),
        ]),
        TreeNode("grade", "cor", description="assign a grade to the reviewed claim", children=[
            TreeNode("rubric-attn", "ac", description="attend to the grading rubric"),
        ]),
    ]))
    tree_root = work / "reviewer_tree"
    materialize(tree, tree_root)
    viol = validate(tree_root)
    check("tree validates", len(viol) == 0, f"{len(viol)} violations")

    con = build_index(tree_root)
    hits = search(con, "rubric")
    check("tree search", len(hits) >= 1, f"'rubric' → {len(hits)} hit(s)")

    # ── 6. glyphsteer — faceted retrieval, markers hidden on return ──────────
    section(6, "GlyphSteer — glyph-faceted retrieval; the marker steers the match but is hidden")
    corpus = [
        Chunk("c1", "The deployment succeeded and latency improved."),
        Chunk("c2", "The deployment failed and the rollback broke."),
        Chunk("c3", "The deployment shipped on schedule."),
    ]
    ann = RuleAnnotator.keyword(SENTIMENT, {
        SENTIMENT.by_name("negative").glyph: ["failed", "broke", "terrible"],
        SENTIMENT.by_name("positive").glyph: ["succeeded", "improved", "great"],
    })
    annotated = [gs.annotate_chunk(c, ann, SENTIMENT) for c in corpus]
    gcon = gs.build_index(annotated)
    neg = SENTIMENT.by_name("negative").glyph
    ghits = gs.search(gcon, "deployment", facet=neg)
    top_is_failure = bool(ghits) and "failed" in ghits[0]["text"]
    clean = all(neg not in h["text"] and "negative" not in h.get("text", "") for h in ghits)
    check("facet pins the negative chunk", top_is_failure, f"top → {ghits[0]['text'][:38]!r}" if ghits else "no hits")
    check("returned text is clean (HIDE invariant)", clean, "no glyph in any returned body")

    # ── 7. si — self-interpreter: walk the tree + run a chain snippet ────────
    section(7, "si — walk the materialized tree (reachable leaves) + interpret a chain snippet")
    reach = si.reachable(tree_root, "reviewer")
    leaf = si.read_skill(tree_root, "rubric-attn")
    check("si walks to leaves", "rubric-attn" in reach, f"{len(reach)} reachable: {reach}")
    check("si reads a leaf", leaf is not None, "rubric-attn SKILL.md read" if leaf else "leaf not found")
    val = si.interpret("40 + 2")
    check("si interprets", val == 42, f"40 + 2 = {val}")

    # ── summary ──────────────────────────────────────────────────────────────
    passed = sum(1 for _, ok, _ in results if ok)
    total = len(results)
    print(f"\n{'═'*60}")
    print(f"  _all: {passed}/{total} checks passed — 7 stages across 9 packages on ONE domain")
    print(f"  (chaincompiler · honeyc · rulecatcher · accc · corcc · sccc · skilltree · glyphsteer · si)")
    print(f"  the ONE type round-tripped: persona→honeyc→gate→construct→tree→steer→interpret")
    print(f"{'═'*60}")
    failed = [s for s, ok, _ in results if not ok]
    if failed:
        print(f"  FAILED: {failed}")
        return 1
    print("  ✓ the stack composes end-to-end. chaincompiler is dogfooded.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
