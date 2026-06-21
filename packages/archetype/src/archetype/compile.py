"""The compiler pipeline (§5): source → infer missing aspects → generate Odyssey
(multi-HJ) → generate Becoming → recurse → validate. The headline ChainCompiler move
applied to the psyche: you don't LIST archetypes, you compile the transformation law.
"""
from __future__ import annotations

from .infer import infer
from .model import MetaArchetype
from .odyssey import generate_odyssey
from .stdlib import CYCLE, CYBERNETIC_CITY, Seed, next_in_cycle  # noqa: F401 (re-export)


def _pantheon(name: str, world: dict[str, Seed] | None) -> list[str]:
    p = list(world) if world else list(CYCLE)
    if name not in p:
        p = [name] + p
    return p


def compile_archetype(name: str, *, knobs: dict | None = None,
                      world: dict[str, Seed] | None = None, depth: int | None = None,
                      with_odyssey: bool = True, **aspects) -> MetaArchetype:
    """Compile one archetype: infer the five aspects, then generate its Odyssey."""
    a = infer(name, knobs=knobs, world=world, **aspects)
    if with_odyssey:
        a.odyssey = generate_odyssey(a, _pantheon(name, world), world=world, depth=depth)
    return a


def compile_chain(names: list[str], *, knobs: dict | None = None,
                  world: dict[str, Seed] | None = None, depth: int | None = None,
                  with_odyssey: bool = False) -> list[MetaArchetype]:
    """Compile an individuation chain (Hero => Guardian => King): each archetype's
    Becoming is overridden to point at the NEXT name in the chain (C4 satisfied)."""
    out: list[MetaArchetype] = []
    for i, nm in enumerate(names):
        nxt = names[i + 1] if i + 1 < len(names) else next_in_cycle(nm)
        out.append(compile_archetype(nm, knobs=knobs, world=world, depth=depth,
                                     with_odyssey=with_odyssey, becoming=nxt))
    return out


def compile_world(world: dict[str, Seed], *, knobs: dict | None = None,
                  depth: int | None = None, with_odyssey: bool = True) -> dict[str, MetaArchetype]:
    """Compile a whole substrate world (e.g. the Example World)."""
    return {nm: compile_archetype(nm, knobs=knobs, world=world, depth=depth,
                                  with_odyssey=with_odyssey) for nm in world}
