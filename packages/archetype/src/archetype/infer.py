"""Inference — generate the missing aspects from whichever one is known (§5).

The compiler accepts a seed + knobs + (optional partial aspects) and generates the
rest. When the name is in the stdlib pantheon, the canonical aspects are used; else
the generic generators below produce them deterministically (no LLM — same stance as
the rest of ChainCompiler: the mechanics are code, the content is the model's job).
"""
from __future__ import annotations

from .model import MetaArchetype
from .stdlib import Seed, next_in_cycle, seed_for


# ── the three operators (generic forms; stdlib overrides with canonical content) ──
def denied_inverse(persona: str) -> str:
    """Shadow = DeniedInverse(Persona): the persona's virtue as its failure-mode."""
    return f"Denied {persona} (the virtue turned to its failure-mode / projection)"


def integrate(persona: str, shadow: str) -> str:
    """Self = Integrate(Persona, Shadow): holds BOTH, ruled by neither."""
    return f"Integrated form (holds «{persona}» and «{shadow}» without collapsing into either)"


def type_lift(name: str, knobs: dict) -> str:
    """Becoming = TypeLift(Self): the next archetype's name (knob can override)."""
    return knobs.get("becoming") or next_in_cycle(name)


def _scores(name: str, from_stdlib: bool, self_: str, becoming: str,
            knobs: dict) -> dict:
    """Deterministic confidence scores (§5: the emitted *_fit numbers)."""
    integrates = ("holds" in self_.lower()) or ("integrat" in self_.lower())
    return {
        "persona_shadow_fit": 1.0 if from_stdlib else 0.6,
        "self_integration_fit": 1.0 if integrates else 0.3,   # purified-Self penalty
        "becoming_fit": 1.0 if becoming and becoming != name else 0.0,
        "substrate_fit": 1.0 if knobs.get("substrate") else 0.5,
        "nonredundancy": 1.0 if becoming != name else 0.0,
    }


def infer(name: str, *, knobs: dict | None = None, world: dict[str, Seed] | None = None,
          persona: str | None = None, shadow: str | None = None,
          self_: str | None = None, becoming: str | None = None) -> MetaArchetype:
    """Build a (still odyssey-less) MetaArchetype, filling unknown aspects.

    Precedence per aspect: explicit arg > stdlib seed > generic generator. This is
    the §5 "if-X-known → generate the rest" table collapsed into one resolver.
    """
    knobs = dict(knobs or {})
    seed = seed_for(name, world)
    from_stdlib = seed is not None

    p = persona or (seed.persona if seed else f"{name} (legible role)")
    s = shadow or (seed.shadow if seed else denied_inverse(p))
    i = self_ or (seed.self_ if seed else integrate(p, s))
    b = becoming or (seed.becoming if seed else type_lift(name, knobs))

    return MetaArchetype(name=name, persona=p, shadow=s, self_=i, becoming=b,
                         odyssey=[], knobs=knobs,
                         confidence=_scores(name, from_stdlib, i, b, knobs))
