"""Parse the archetype DSL (§7) into structured requests.

    archetype Hero { substrate:"founder building AI" domain:"startup myth"
                     conflict:"inflation" boundary:"responsibility" integration_mode:"service" }
    chain IndividuationPath { Hero => Guardian => King => Steward => Sage }
    triangulate { X==Shadow  Y==Persona  Z==Self }

Returns a list of `Stmt` (kind ∈ {archetype, chain, triangulate}); the CLI/compiler
consume them. Deliberately tiny — regex over braces, no external grammar.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

_BLOCK = re.compile(r"(archetype|chain|triangulate)\s+([A-Za-z0-9_]+)?\s*\{([^}]*)\}", re.S)
_KV = re.compile(r"([A-Za-z_]+)\s*:\s*\"([^\"]*)\"")
_ARROW = re.compile(r"=>")
_ANCHOR = re.compile(r"([A-Za-z0-9_]+)\s*==\s*(Persona|Shadow|Self)", re.I)


@dataclass
class Stmt:
    kind: str                       # archetype | chain | triangulate
    name: str = ""
    knobs: dict = field(default_factory=dict)        # for `archetype`
    steps: list[str] = field(default_factory=list)   # for `chain`
    anchors: dict = field(default_factory=dict)       # for `triangulate`: {role: var}


def parse(text: str) -> list[Stmt]:
    stmts: list[Stmt] = []
    for kind, name, inner in _BLOCK.findall(text):
        if kind == "archetype":
            stmts.append(Stmt("archetype", name, knobs=dict(_KV.findall(inner))))
        elif kind == "chain":
            steps = [s.strip() for s in _ARROW.split(inner) if s.strip()]
            stmts.append(Stmt("chain", name, steps=steps))
        elif kind == "triangulate":
            anchors = {role.capitalize(): var for var, role in _ANCHOR.findall(inner)}
            stmts.append(Stmt("triangulate", name, anchors=anchors))
    return stmts
