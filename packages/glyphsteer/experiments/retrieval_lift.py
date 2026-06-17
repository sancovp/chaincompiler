"""Q4: does the glyph sidecar lift retrieval over the no-annotation baseline?

The LEXICAL arm runs with zero deps (run this file directly). The dense arm is
ASPIRATIONAL until the magnitude probe (Q1-Q3) clears — wire it once the nudge is
shown to be big enough to reorder.

Run:  python experiments/retrieval_lift.py
"""
from __future__ import annotations

import json

from glyphsteer import SENTIMENT, Chunk, RuleAnnotator
from glyphsteer.eval import retrieval_lift_lexical

POS = SENTIMENT.by_name("positive").glyph
NEG = SENTIMENT.by_name("negative").glyph

CORPUS = [
    Chunk("r1", "the api migration went smoothly and the team is delighted"),
    Chunk("r2", "the api migration failed and broke production, terrible outcome"),
    Chunk("r3", "the api migration is scheduled for next sprint"),
    Chunk("r4", "the database migration succeeded, excellent work all around"),
    Chunk("r5", "the database migration corrupted records, an awful regression"),
]
ANN = RuleAnnotator.keyword(SENTIMENT, {
    POS: ["delighted", "excellent", "smoothly", "succeeded"],
    NEG: ["failed", "broke", "terrible", "awful", "corrupted"],
})
# "find the migration that went BADLY" — facet on negative
QUERIES = [
    {"text": "migration", "facet": NEG, "relevant": {"r2", "r5"}},
    {"text": "migration", "facet": POS, "relevant": {"r1", "r4"}},
]


def main() -> None:
    rep = retrieval_lift_lexical(CORPUS, QUERIES, ANN, SENTIMENT, k=3)
    print(json.dumps(rep, indent=2))
    b, s = rep["baseline"]["mrr"], rep["steered"]["mrr"]
    print(f"\nMRR: baseline {b:.3f} → steered {s:.3f}  (lift {s - b:+.3f})")


if __name__ == "__main__":
    main()
