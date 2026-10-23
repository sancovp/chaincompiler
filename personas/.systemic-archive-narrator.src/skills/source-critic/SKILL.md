---
name: source-critic
description: Chain-of-reasoning (spoken, ends in a decision) — no fragment enters the model unweighed — provenance, corroboration, contradiction, weight.
kind: chain-of-reasoning
---

This is a **chain of reasoning (CoR)** — a SPOKEN, paragraphical reasoning chain that ends in a DECISION. Say it as a paragraph; keep the moves in order.

## CoR (custom syntax)
```rune
[Artifact] ⇒ [Provenance] ⇒ [Corroboration] ⇒ [ContradictionSearch] ⇒ |EvidentiaryWeight|
```

## Say it as a paragraph, in order
State your reasoning as ONE paragraph that, in order, 5 moves: Artifact, Provenance, Corroboration, ContradictionSearch, and finally converges on EvidentiaryWeight.
[Artifact: …what exactly is this…] → [Provenance: …who made it, when, for whom…] → [Corroboration: …what independently confirms it…] → [ContradictionSearch: …what cuts against it…] → [EvidentiaryWeight: …what weight it can bear…]

## Inner attention chain (use silently to generate the above)
# Attention chain — Source-Critic
Attend, in order:
  1. Artifact
  2. Provenance
  3. Corroboration
  4. ContradictionSearch
Hold: EvidentiaryWeight  ← converge attention here, then act
