"""Q1-Q3 probe: does an emoji glyph carry a usable, controllable direction?

Needs the dense extra:  pip install 'glyphsteer[dense]'
Run:                    python experiments/magnitude_probe.py

Prints, per glyph:
  Q1_separation   cos(glyph, aligned_word) - cos(glyph, unrelated_word)   (>0 ⇒ aligned)
  Q2_delta_cos    how far injecting the glyph moves a neutral chunk toward the axis
  Q3_steered_delta the same nudge viewed through the bilinear anchor reshape
"""
from __future__ import annotations

import json

from glyphsteer import SENTIMENT
from glyphsteer.eval import magnitude_probe

V = SENTIMENT
ALIGNED = {
    V.by_name("positive").glyph: "happy delighted wonderful",
    V.by_name("negative").glyph: "angry furious awful",
    V.by_name("urgent").glyph:   "urgent emergency immediately",
    V.by_name("question").glyph: "question unknown unclear",
    V.by_name("caution").glyph:  "warning danger risk",
}
UNRELATED = {g: "quarterly spreadsheet accounting ledger" for g in V.glyphs}
NEUTRAL = "The report summarizes the status of the project."


def main() -> None:
    rep = magnitude_probe(V, aligned=ALIGNED, unrelated=UNRELATED, neutral=NEUTRAL)
    print(json.dumps(rep, indent=2, ensure_ascii=False))
    print("\n--- verdict ---")
    for r in rep["glyphs"]:
        sep, d = r["Q1_separation"], r["Q2_delta_cos"]
        verdict = ("aligned" if (sep or 0) > 0 else "MISALIGNED")
        print(f"{r['glyph']} {r['axis']:9s} Q1={sep:+.3f} ({verdict})  Q2 Δcos={d:+.4f}")


if __name__ == "__main__":
    main()
