"""The Odyssey — a SUCCESSION of hero's journeys (ARCHETYPE-COMPILER.md §2).

The original spec's bug: it made an Odyssey a single Persona→Shadow→Self path. That
is ONE hero's journey = ONE Becoming, not an Odyssey. An Odyssey is plural:

    HJ₀          the call-out journey (leave home / Troy)
    HJ₁…HJₙ      the wandering arcs — each an automorphism-encounter with a pantheon
                 member (A meets B as an image of itself; accrues the Aut-web)
    HJ_return    the POST-return mini-HJ (you arrive home and STILL must fight — the
                 suitors; arrival ≠ completion)

The telos = accrue an automorphism-edge to every pantheon member → orbit-closure →
quine the pantheon. Whether the orbit actually CLOSES (vs only tempering) is the open
seam (see ARCHETYPE-MUSIC-CORRESPONDENCE-MAP.md); this generator builds the
succession, it does not claim closure.
"""
from __future__ import annotations

from .model import HJ, MetaArchetype
from .stdlib import Seed, seed_for


def generate_odyssey(arch: MetaArchetype, pantheon: list[str], *,
                     world: dict[str, Seed] | None = None,
                     depth: int | None = None) -> list[HJ]:
    """Build A's odyssey: a call-out HJ, one encounter-HJ per other pantheon member
    (up to `depth`), and a post-return HJ. Each encounter accrues an Aut-edge."""
    hjs: list[HJ] = []

    # HJ₀ — the call-out: A's own Persona → Shadow → Self
    hjs.append(HJ(persona=arch.persona, shadow=arch.shadow, self_=arch.self_,
                  encounter=""))

    # HJ₁…HJₙ — meet each OTHER pantheon member as an automorphism-image of A
    others = [m for m in pantheon if m != arch.name]
    if depth is not None:
        others = others[:max(0, depth)]
    carry = arch.self_
    for m in others:
        ms = seed_for(m, world)
        m_shadow = ms.shadow if ms else f"the shadow of {m}"
        hjs.append(HJ(
            persona=carry,                                   # carry the prior Self forward
            shadow=m_shadow,                                 # confront M's shadow-face
            self_=f"{arch.name}-as-{m} (A's {m}-automorphism)",
            encounter=m))
        carry = f"{arch.name}+{m}"

    # HJ_return — the post-return journey (the suitors): integrate the homecoming
    hjs.append(HJ(persona=carry, shadow=f"the unguarded home ({arch.name} returned but untested)",
                  self_=f"{arch.name} sovereign at home (return integrated)",
                  encounter="", post_return=True))
    return hjs


def aut_web(odyssey: list[HJ]) -> list[str]:
    """The set of pantheon members A has accrued an automorphism-edge to."""
    return [hj.encounter for hj in odyssey if hj.encounter]


def quines(odyssey: list[HJ], pantheon: list[str], name: str) -> bool:
    """Orbit-closure test (the telos): has A met EVERY other pantheon member?
    True ⇒ A can regenerate the whole pantheon from itself (quining). This is the
    discrete closure check; it does NOT settle the comma/tempering question."""
    met = set(aut_web(odyssey))
    return met >= {m for m in pantheon if m != name}
