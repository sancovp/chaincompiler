"""SC (skillchain) sequence notation.

An SC IS A sequence chaining ACs + CoRs + regular skills, converging on a result:

    [ac:<name>] ⇒ [cor:<name>] ⇒ [skill:<name>] ⇒ ... ⇒ |Result|

Each `[kind:name]` step references a SKILL.md package on disk — a forged
attention chain (kind=ac), a forged chain-of-reasoning (kind=cor), or a regular
skill (kind=skill). Written in Dense Rune-Chain so it is syntax-linted like every
other *CC notation. SC is the highest composite: AC → CoR → SC.
"""
from __future__ import annotations

# Seed SC sequences (used to forge the SC notation grammar — the shape only).
SEED_SEQUENCES = [
    "[ac:debug-attention] ⇒ [cor:think-like-einstein] ⇒ [skill:summarize] ⇒ |Answer|",
    "[ac:debug-attention] ⇒ [skill:summarize] ⇒ |Answer|",
    "[cor:think-like-einstein] ⇒ [skill:summarize] ⇒ |Answer|",
]
