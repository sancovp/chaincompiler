"""Emit a compiled archetype through lenses (§5, §7) — readable / triples / Prolog /
Cypher / JSON — and, crucially, as the ONE TYPE: a `<name>/SKILL.md` skill dir, so an
archetype is a first-class citizen of ChainCompiler's closed algebra (an archetype
compiled to a loadable persona). Becoming = TypeLift = the recursion that, via the
bandit, can roll the archetype up into a domain persona.
"""
from __future__ import annotations

import json
from pathlib import Path

from .model import MetaArchetype
from .odyssey import aut_web, quines


def readable(a: MetaArchetype, pantheon: list[str] | None = None) -> str:
    lines = [
        f"# {a.name} — a recursive individuation circuit",
        "",
        f"- **Persona**  (mask):        {a.persona}",
        f"- **Shadow**   (denied inv.): {a.shadow}",
        f"- **Self**     (integrated):  {a.self_}",
        f"- **Becoming** (type-lift →): {a.becoming}",
    ]
    if a.knobs:
        lines += ["", "**Knobs:** " + ", ".join(f"{k}={v}" for k, v in a.knobs.items())]
    if a.odyssey:
        lines += ["", f"## Odyssey ({len(a.odyssey)} hero's journeys)"]
        for i, hj in enumerate(a.odyssey):
            lines.append(f"{i}. {hj}")
        web = aut_web(a.odyssey)
        lines += ["", f"**Aut-web:** {', '.join(web) if web else '—'}"]
        if pantheon:
            lines.append(f"**Quines the pantheon:** {quines(a.odyssey, pantheon, a.name)}")
    if a.confidence:
        lines += ["", "**Confidence:** " + ", ".join(f"{k}={v}" for k, v in a.confidence.items())]
    return "\n".join(lines)


def triples(a: MetaArchetype) -> list[tuple[str, str, str]]:
    t = [
        (a.name, "HAS_PERSONA", a.persona),
        (a.name, "HAS_SHADOW", a.shadow),
        (a.name, "HAS_SELF", a.self_),
        (a.name, "BECOMES", a.becoming),
        (a.shadow, "DENIED_INVERSE_OF", a.persona),
        (a.self_, "INTEGRATES", a.persona),
        (a.self_, "INTEGRATES", a.shadow),
    ]
    for hj in a.odyssey:
        if hj.encounter:
            t.append((a.name, "AUTOMORPHISM_EDGE", hj.encounter))
    return t


def prolog(a: MetaArchetype) -> str:
    def q(s: str) -> str:
        return s.replace("'", "\\'")
    lines = [
        f"persona('{q(a.name)}', '{q(a.persona)}').",
        f"shadow('{q(a.name)}', '{q(a.shadow)}').",
        f"self('{q(a.name)}', '{q(a.self_)}').",
        f"becomes('{q(a.name)}', '{q(a.becoming)}').",
        f"denied_inverse('{q(a.shadow)}', '{q(a.persona)}').",
    ]
    for hj in a.odyssey:
        if hj.encounter:
            lines.append(f"aut_edge('{q(a.name)}', '{q(hj.encounter)}').")
    return "\n".join(lines)


def cypher(a: MetaArchetype) -> str:
    n = a.name
    lines = [
        f"MERGE (a:Archetype {{name:'{n}'}})",
        f"SET a.persona='{a.persona}', a.shadow='{a.shadow}', a.self='{a.self_}'",
        f"MERGE (b:Archetype {{name:'{a.becoming}'}})",
        f"MERGE (a)-[:BECOMES]->(b)",
    ]
    for hj in a.odyssey:
        if hj.encounter:
            lines.append(f"MERGE (m:Archetype {{name:'{hj.encounter}'}}) "
                         f"MERGE (a)-[:AUT_EDGE]->(m)")
    return "\n".join(lines)


def to_json(a: MetaArchetype) -> str:
    return json.dumps({
        "name": a.name, **a.aspects, "knobs": a.knobs,
        "odyssey": [{"persona": h.persona, "shadow": h.shadow, "self": h.self_,
                     "encounter": h.encounter, "post_return": h.post_return} for h in a.odyssey],
        "aut_web": aut_web(a.odyssey), "confidence": a.confidence,
    }, indent=2)


def emit_skill(a: MetaArchetype, *, out_dir: str | Path, pantheon: list[str] | None = None) -> Path:
    """Compile the archetype to the ONE type — `<name>/SKILL.md` — so it loads as a
    persona. The body is the readable individuation circuit + its emitted graph."""
    from chaincompiler.skillpack import write_skill
    body = readable(a, pantheon) + "\n\n## Triples\n" + "\n".join(
        f"- {s} —{p}→ {o}" for s, p, o in triples(a))
    return write_skill(
        f"{a.name}-archetype",
        f"The {a.name} archetype as an individuation circuit (Persona/Shadow/Self → Becoming {a.becoming}).",
        body, out_dir=out_dir, extra={"kind": "archetype", "becomes": a.becoming})


def emit(a: MetaArchetype, fmt: str, *, pantheon: list[str] | None = None):
    """Dispatch one lens by name."""
    return {
        "readable": lambda: readable(a, pantheon),
        "triples": lambda: triples(a),
        "prolog": lambda: prolog(a),
        "cypher": lambda: cypher(a),
        "json": lambda: to_json(a),
    }[fmt]()
