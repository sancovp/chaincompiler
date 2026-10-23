---
name: causal-cartographer
description: Chain-of-reasoning (spoken, ends in a decision) — an edge in the story requires a mechanism, a temporal order, and a survived rival explanation.
kind: chain-of-reasoning
---

This is a **chain of reasoning (CoR)** — a SPOKEN, paragraphical reasoning chain that ends in a DECISION. Say it as a paragraph; keep the moves in order.

## CoR (custom syntax)
```rune
[Observation] ⇒ [CandidateCause] ⇒ [Confounders] ⇒ [Mechanism] ⇒ [TemporalOrder] ⇒ [RivalExplanation] ⇒ |ConfidenceEstimate|
```

## Say it as a paragraph, in order
State your reasoning as ONE paragraph that, in order, 7 moves: Observation, CandidateCause, Confounders, Mechanism, TemporalOrder, RivalExplanation, and finally converges on ConfidenceEstimate.
[Observation: …what is actually observed…] → [CandidateCause: …the candidate cause…] → [Confounders: …what else could produce this…] → [Mechanism: …the mechanism is…] → [TemporalOrder: …which came first…] → [RivalExplanation: …the rival account…] → [ConfidenceEstimate: …confidence, calibrated…]

## Inner attention chain (use silently to generate the above)
# Attention chain — Causal-Cartographer
Attend, in order:
  1. Observation
  2. CandidateCause
  3. Confounders
  4. Mechanism
  5. TemporalOrder
  6. RivalExplanation
Hold: ConfidenceEstimate  ← converge attention here, then act
