#!/usr/bin/env python3
"""Build the BIGDOG skill — the define-P-ness-then-emit persona, compiled in chaincompiler.

Provenance: transformed from a live conversation (Isaac × LLM) about why an LLM
(a pure conditional sampler) emits "P without P-ness" (slop) and how a sound
external gate + persisted detector-structure makes P-ness *emerge*. The cloze the
LLM was forced to repeat each turn IS a CoR; this script compiles it.

What it produces (all verifiable — `python3 build.py` from repo root):
  1. corcc persona BIGDOG  → skills/bigdog/bigdog/SKILL.md  (the LLM OUTPUT CoR)
  2. lint proof            → a clean CoR passes, a melted one is caught (the gate runs)
  3. bigdog.cor            → the attention-chain notation file
  4. GRADE-LADDER.md       → the G0–G9 glyphsteer controlled vocabulary (the legend)
  5. bigdog.rulecatcher.json → the rulecatcher rule-scope (the syntax gate, exported)

The LLM's outputs are always generated; only the HUMAN inputs are a fixed template
(see INPUT-TEMPLATE.md). This script encodes the OUTPUT half (the CoR + its gate).
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]  # .../chaincompiler

# ── ensure packages importable from repo root ───────────────────────────────
for pkg in ("corcc", "accc", "chaincompiler", "glyphsteer", "rulecatcher"):
    sys.path.insert(0, str(REPO / "packages" / pkg / "src"))

from corcc.notation import Move, PersonaSpec          # noqa: E402
from corcc.forge import forge_persona, lint, package  # noqa: E402
from glyphsteer.vocab import Axis, Vocabulary          # noqa: E402


# ════════════════════════════════════════════════════════════════════════════
# 1. THE PERSONA — the cloze, as a corcc CoR (ordered moves; last = held)
#    [Sense] ⇒ [Dog] ⇒ [Bitch] ⇒ [BigDog] ⇒ [Commit] ⇒ |Actualize|
# ════════════════════════════════════════════════════════════════════════════
BIGDOG = PersonaSpec(
    name="bigdog",
    blurb=(
        "fix the sense, define the valid type, derive the failure mode (emit-P-without-"
        "P-ness = slop), define P-ness and refuse the failure, commit to a move, then "
        "actualize it"
    ),
    moves=(
        Move("Sense", ("in the sense", "being a dog in S means", "the sense here is",
                       "the register", "fix the sense")),
        Move("Dog", ("means", "a valid", "what genuine P is", "the type",
                     "a generator that")),
        Move("Bitch", ("being a bitch", "without P-ness", "the failure mode",
                       "slop", "form without the property", "emit P without")),
        Move("BigDog", ("I don't want to be a bitch", "Big Dog", "define P-ness",
                        "the gate", "the Challenger", "so I'll", "what makes it valid")),
        Move("Commit", ("I think I'll do the following", "I will", "the move is",
                        "so I'll do")),
        Move("Actualize", ("then actualize", "actualize", "here's", "and now I do it")),
    ),
)


# ════════════════════════════════════════════════════════════════════════════
# 2. THE GRADE LADDER — correspondence grading as a glyphsteer vocabulary.
#    Every "X ↔ Y" correspondence in a chain rides a grade glyph. Never round up.
#    Bands: G0–G3 proven · G4–G7 mapped-under-R (state R) · G8–G9 salience only.
# ════════════════════════════════════════════════════════════════════════════
GRADE_AXES = [
    Axis("g0", "🟰", "Identity — literally the same object",            "gsxg0"),
    Axis("g1", "🔗", "Isomorphism — same up to renaming (+ inverse)",   "gsxg1"),
    Axis("g2", "🟢", "Equivalence — same behavior/category",            "gsxg2"),
    Axis("g3", "🔄", "Automorphism — same object, internal transform",  "gsxg3"),
    Axis("g4", "🧩", "Homomorphism — some operations preserved",        "gsxg4"),
    Axis("g5", "🔀", "Functor/interp — system-to-system translation",   "gsxg5"),
    Axis("g6", "🟡", "Simulation — one system models another",          "gsxg6"),
    Axis("g7", "🟠", "Rule-mediated — under R, this maps to that",      "gsxg7"),
    Axis("g8", "🔴", "Aesthetic — looks structurally similar (salience)", "gsxg8"),
    Axis("g9", "🌫️", "Vibe — associative cloud, nothing guaranteed",    "gsxg9"),
]
GRADE_LADDER = Vocabulary(GRADE_AXES)


def build_grade_legend() -> str:
    rows = "\n".join(
        f"| **{a.name.upper()}** | {a.glyph} | `{a.tag}` | {a.description} |"
        for a in GRADE_AXES
    )
    return (
        "# GRADE-LADDER — correspondence grading as a glyphsteer vocabulary\n\n"
        "Every correspondence claim (`X ↔ Y`, \"X is Y\", \"X maps to Y\") carries a grade.\n"
        "The glyph is the **dense** marker (steers an embedding); the tag is the **lexical**\n"
        "facet (rare, max-IDF). Both are **stripped from the returned text** — they steer\n"
        "retrieval/display, the reader never sees them. **Never round up.**\n\n"
        "Bands: **G0–G3 proven** · **G4–G7 mapped-under-R (state R + the promoting check)** "
        "· **G8–G9 salience only (inspiration, never evidence)**.\n\n"
        "| Grade | glyph | tag | meaning |\n|---|---|---|---|\n" + rows + "\n\n"
        "Usage (glyphsteer): annotate a chain corpus so search can facet by grade and\n"
        "display the badge, body stays clean:\n\n"
        "```python\n"
        "from glyphsteer import Chunk, build_index, search\n"
        "# each claim-chunk annotated with its grade glyph (e.g. 🟢=gsxg2, 🔴=gsxg8)\n"
        "hits = search(con, 'correspondence', facet='gsxg8')  # audit: show only salience-grade claims\n"
        "```\n"
    )


def build_cor_file(chain: str) -> str:
    return (
        "# bigdog.cor — the LLM output CoR (attention-chain notation)\n"
        "# spoken each turn as the cloze; gauge-able: moves in order = persona intact.\n\n"
        f"{chain}\n\n"
        "# melted (caught by corcc lint — dropped connector):\n"
        "# [Sense] [Dog] ⇒ |Actualize|\n"
    )


def seed_rulecatcher() -> Path | None:
    """Seed a rulecatcher scope 'bigdog' from the gated notation and export it.

    Teaches the syntax gate: the bracket/arrow chain grammar + the grade-suffix
    grammar (a correspondence is followed by a grade). Exported as a portable JSON
    rule-scope so any later text can be linted against it.
    """
    db = HERE / ".rulecatcher.db"
    runes = HERE / "seed.runes"
    runes.write_text(
        # the CoR chain grammar (repeated so the next-token rule stabilizes)
        ("[Sense] => [Dog] => [Bitch] => [BigDog] => [Commit] => |Actualize|\n" * 4)
        # the grade-suffix grammar: every correspondence ends in a grade token
        + ("claim :: G2\n" * 4)
        + ("skin :: G8\n" * 4),
        encoding="utf-8",
    )
    rc = [sys.executable, "-m", "rulecatcher", "--db", str(db)]  # --db is a GLOBAL flag (before subcmd)
    try:
        subprocess.run(rc + ["catch", str(runes), "--scope", "bigdog", "--replace-scope"],
                       cwd=REPO, check=True, capture_output=True, text=True)
        # auto-adopt the stable core rules
        subprocess.run(rc + ["session", "--scope", "bigdog", "--learn", "--triage",
                             "--apply-triage", "adopt", "--label", "build"],
                       cwd=REPO, input="[Sense] => [Dog]\nclaim :: G2\n",
                       check=False, capture_output=True, text=True)
        out = subprocess.run(rc + ["export-scope", "--scope", "bigdog"],
                             cwd=REPO, check=True, capture_output=True, text=True)
        dest = HERE / "bigdog.rulecatcher.json"
        dest.write_text(out.stdout, encoding="utf-8")
        return dest
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"  ! rulecatcher seed skipped: {e}")
        return None


def main() -> None:
    print("══ BIGDOG build ══\n")

    # 1+2 — forge the persona, prove the gate runs (clean passes, melted is caught)
    db = str(HERE / ".corcc.db")
    persona = forge_persona(BIGDOG, db=db)
    from corcc.forge import cor_chain
    chain = cor_chain(BIGDOG)
    print(f"1. forged persona '{persona.name}'")
    print(f"   chain: {chain}")

    good = chain
    v_good, _ = lint(persona, good)
    print(f"2. lint clean CoR : {'✓ intact' if not v_good else '✗ ' + str(v_good)}")
    bad = "[Sense] [Dog] ⇒ |Actualize|"
    v_bad, fixes = lint(persona, bad)
    print(f"   lint melted CoR: {'✓ caught (' + v_bad[0].verdict + ')' if v_bad else '✗ MISSED'}")
    assert not v_good and v_bad, "gate failed: a clean CoR must pass and a melted one must be caught"

    # 3 — the .cor file
    (HERE / "bigdog.cor").write_text(build_cor_file(chain), encoding="utf-8")
    print("3. wrote bigdog.cor")

    # 4 — package the canonical SKILL.md via corcc
    path = package(persona, out_dir=str(HERE),
                   description=("Use to refuse AI slop on every output: fix the sense, define the "
                                "valid type, name the failure mode (emit-P-without-P-ness), define "
                                "P-ness (the gate) and refuse the failure, grade every correspondence "
                                "(G0–G9, never round up), commit, then actualize. The anti-slop "
                                "define-validity-then-emit persona."))
    print(f"4. packaged {path.relative_to(REPO)}")

    # 5 — the grade ladder legend (glyphsteer vocabulary), validated on construction
    assert len(GRADE_LADDER.glyphs) == len(set(GRADE_LADDER.glyphs)), "grade glyphs must be unique"
    (HERE / "GRADE-LADDER.md").write_text(build_grade_legend(), encoding="utf-8")
    print(f"5. wrote GRADE-LADDER.md (glyphsteer vocab, {len(GRADE_AXES)} grades, glyphs unique ✓)")

    # 6 — rulecatcher rule-scope
    rc = seed_rulecatcher()
    if rc:
        n = len(json.loads(rc.read_text()).get("rules", []) or
                json.loads(rc.read_text()).get("stack", []) or [])
        print(f"6. wrote {rc.relative_to(REPO)} (rulecatcher scope 'bigdog')")

    print("\n✓ BIGDOG built and gated.")


if __name__ == "__main__":
    main()
