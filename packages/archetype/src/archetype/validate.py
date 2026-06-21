"""Graph constraints C1–C6 (ARCHETYPE-COMPILER.md §5, §2.4).

C1  Persona-opposes-Shadow      (shadow ≠ persona; it is the denied inverse)
C2  Self-contains-both          (NOT a purified Persona that bypasses the Shadow)
C3  Odyssey-traverses-Shadow    (every HJ confronts a shadow)
C4  Becoming-type-lifts         (becoming ≠ the archetype itself; it explains A⇒B)
C5  recursion terminates/cycles (becoming resolves to a known/own name)
C6  Odyssey-is-plural           (≥1 HJ AND accrues automorphism-edges)
C6b post-return present         (a complete Odyssey returns AND fights again)

`validate` returns a list of violation strings; empty ⇒ the archetype is well-formed.
"""
from __future__ import annotations

from .model import MetaArchetype
from .odyssey import aut_web


def validate(arch: MetaArchetype) -> list[str]:
    v: list[str] = []

    # C1 — persona opposes shadow
    if not arch.shadow or arch.shadow.strip() == arch.persona.strip():
        v.append("C1: Shadow must be the denied inverse of Persona (got identical/empty).")

    # C2 — Self contains both (the cardinal error: a purified Persona)
    sl = arch.self_.strip().lower()
    if arch.self_.strip() == arch.persona.strip():
        v.append("C2: Self is a purified Persona (identical) — it must integrate the Shadow.")
    elif not ("hold" in sl or "integrat" in sl or "both" in sl or "-as-" in sl
              or arch.name.lower() in sl):
        v.append("C2: Self does not evidence integration of Persona AND Shadow.")

    # C4 — Becoming type-lifts to a different archetype
    if not arch.becoming or arch.becoming.strip() == arch.name.strip():
        v.append("C4: Becoming must type-lift to a DIFFERENT archetype (got self/empty).")

    # odyssey constraints (only when an odyssey was generated)
    if arch.odyssey:
        # C3 — every HJ traverses a shadow
        if any(not hj.shadow.strip() for hj in arch.odyssey):
            v.append("C3: every hero's journey in the Odyssey must confront a Shadow.")
        # C6 — plural AND accrues automorphism-edges
        if len(arch.odyssey) < 2:
            v.append("C6: an Odyssey is a SUCCESSION of HJs (a single P→S→Self is a Becoming).")
        if not aut_web(arch.odyssey):
            v.append("C6: the Odyssey must accrue automorphism-edges to other pantheon members.")
        # C6b — post-return HJ present
        if not any(hj.post_return for hj in arch.odyssey):
            v.append("C6b: a complete Odyssey includes a post-return journey (arrival ≠ completion).")

    return v


def is_valid(arch: MetaArchetype) -> bool:
    return not validate(arch)
