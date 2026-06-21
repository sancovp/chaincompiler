"""The archetype-as-state-machine model (ARCHETYPE-COMPILER.md §1, §3).

An archetype is NOT a noun (a role label) but a recursive individuation circuit:

    MetaArchetype(A) := ⟨ Persona(A), Shadow(A), Self(A), Odyssey(A), Becoming(A) ⟩

- Persona  = the legible / claimed face (the mask).
- Shadow   = DeniedInverse(Persona) — the failure-mode / projected inverse.
- Self     = Integrate(Persona, Shadow) — contains BOTH, ruled by neither
             (a *purified* Persona that bypasses the Shadow is the cardinal error).
- Odyssey  = the SUCCESSION of hero's journeys (§2) — plural, accrues the pantheon
             automorphism-web, ends in quining (orbit-closure).
- Becoming = TypeLift(Self) — the integrated Self becomes the Persona of the next
             archetype. One Becoming = one hero's journey = one modulation.

These mechanics are G0-by-definition *inside the calculus*. The music-theory frame
(circle of fifths ↔ Becoming-cycle, etc.) is a G8 organizing resonance — see
ARCHETYPE-COMPILER.md §0; it is NOT asserted by this code.
"""
from __future__ import annotations

from dataclasses import dataclass, field

# the generation knobs (= "modes"): each colors one archetype differently.
KNOBS = ("domain", "substrate", "conflict", "boundary", "integration_mode", "scale", "tone")


@dataclass
class HJ:
    """One hero's journey = one Becoming step (Persona-state → Shadow → Self ⇒ next).
    In an Odyssey, each non-zero HJ is an automorphism-encounter with a pantheon
    member (`encounter`): A meets B as an image of itself (one sense, many faces)."""
    persona: str
    shadow: str
    self_: str
    encounter: str = ""          # the pantheon member met as an automorphism-image
    post_return: bool = False    # the post-return HJ (arrival ≠ completion; the suitors)

    def __str__(self) -> str:
        tag = " [post-return]" if self.post_return else (f" ↔{self.encounter}" if self.encounter else "")
        return f"{self.persona} → ⟂{self.shadow} → ⊕{self.self_}{tag}"


@dataclass
class MetaArchetype:
    """A compiled archetype: the five aspects + the knobs that colored it + scores."""
    name: str
    persona: str
    shadow: str
    self_: str
    becoming: str                          # the name of the next archetype (TypeLift target)
    odyssey: list[HJ] = field(default_factory=list)
    knobs: dict = field(default_factory=dict)
    confidence: dict = field(default_factory=dict)

    @property
    def aspects(self) -> dict:
        return {"persona": self.persona, "shadow": self.shadow,
                "self": self.self_, "becoming": self.becoming}


@dataclass
class Seed:
    """A stdlib pantheon entry — the canonical four aspects of one archetype."""
    persona: str
    shadow: str
    self_: str
    becoming: str
