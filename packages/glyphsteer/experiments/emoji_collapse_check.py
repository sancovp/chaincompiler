"""Emoji-collapse check — the FIRST thing to run against any candidate dense model.

Many English transformer tokenizers (BERT/WordPiece-based, e.g. bge-small-en) map
EVERY emoji to the same token ([UNK]) → all emoji embed to the identical vector →
the dense steering claim is impossible for that model. Byte-aware / multilingual
tokenizers (XLM-R sentencepiece) represent emoji distinctly.

This script measures the pairwise cosine between distinct glyphs. ~1.000 across the
board = COLLAPSE (reject the model). Spread well below 1.0 = distinct (proceed).

Run (against the running sidecar):
    GLYPHSTEER_EMBED_URL=http://localhost:8088 python experiments/emoji_collapse_check.py
"""
from __future__ import annotations

import numpy as np

from glyphsteer import SENTIMENT, dense
from glyphsteer.steer import unit

COLLAPSE_THRESHOLD = 0.995   # mean off-diagonal cosine above this ⇒ collapsed


def main() -> None:
    glyphs = SENTIMENT.glyphs
    U = unit(dense.embed(glyphs))
    M = U @ U.T
    n = len(glyphs)
    off = [M[i, j] for i in range(n) for j in range(n) if i != j]
    mean_off = float(np.mean(off))
    print("pairwise cosine between distinct glyphs:")
    for i, g in enumerate(glyphs):
        print(f"  {g}  " + " ".join(f"{M[i, j]:.3f}" for j in range(n)))
    print(f"\nmean off-diagonal cosine = {mean_off:.3f}")
    if mean_off > COLLAPSE_THRESHOLD:
        print("VERDICT: COLLAPSED — this model is emoji-blind. Reject it for the dense "
              "regime (use a byte-aware / multilingual tokenizer).")
    else:
        print("VERDICT: DISTINCT — glyphs are separable; the dense regime is viable.")


if __name__ == "__main__":
    main()
