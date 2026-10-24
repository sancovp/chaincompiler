---
name: 0.5-causal-graph-cor
description: "[0.5] an edge in the story requires a mechanism, a temporal order, and a survived rival explanation"
---

This is a **chain of reasoning (CoR)** — a SPOKEN, paragraphical reasoning chain that ends in a DECISION. Say it as a paragraph; keep the moves in order.

## CoR (custom syntax)
```rune
[Observation] ⇒ [CandidateCause] ⇒ [Confounders] ⇒ [Mechanism] ⇒ [TemporalOrder] ⇒ [RivalExplanation] ⇒ |ConfidenceEstimate|
```

## Say it as a paragraph, in order
State your reasoning as ONE paragraph that performs, in order, 7 moves: Observation, CandidateCause, Confounders, Mechanism, TemporalOrder, RivalExplanation, and finally converges on ConfidenceEstimate.
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

## Index summary
[0.5] causal-graph-cor — a cor index node; opens to 1 branch(es): causal-graph-pass (ac). Reachable below: causal-graph-pass.

## Descend — the next layer (1)
Only this layer is loaded now. To descend, use the **Read tool** on a child below — that injects the child's layer (its persona + skills). A Bash `cat` reads the bytes but loads nothing; you must use the Read tool. Each path below is relative to this node's folder — the folder that holds this file's `.claude/` — so join it to that folder before you Read it.

- 0.5.1-causal-graph-pass (ac): Read `causal-graph-pass/.claude/skills/0.5.1-causal-graph-pass/SKILL.md`
