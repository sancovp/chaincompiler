---
name: adam-curtis-narration-style-loop
description: the adam-curtis-narration-style default workflow (BanditChain) — walk it
---

This is your **default workflow** for `adam-curtis-narration-style` — the BanditChain. Walk it on every task; it is a flow, not a function.

1. **Task** — frame what's being asked.
2. **Recall = Select (search → neural-match)** — `chaincompiler gba search <this-dir> "<query>"` (`--scope <coord>` to look only in your region; `--newest` for the latest versions). Read the hits and intuitively pick the best fit.
3. **Decide** — a fit → **exec** it. Nothing fits → **construct**.
4. **Construct** — `chaincompiler gba construct <this-dir> <name> "[Focus] ⇒ [Focus] ⇒ |Converge|"` (gated + coord-addressed + re-indexed; follow the `adding-a-skill` discipline — place it, AIOS it).
5. **Execute** — run the chosen/built chain.
6. **Reward** — write a graded note to `kb/`. Your KB + tree ARE your policy.
