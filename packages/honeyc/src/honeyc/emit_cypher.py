"""Lower normalized statements into Neo4j Cypher MERGE statements (file output)."""
from __future__ import annotations

from .normalize import Statement

_KIND_LABEL = {"entity": "Entity", "glyph": "Glyph", "symbol": "Symbol", "transform": "Transform"}

_REL_TYPE = {
    "equiv": "EQUIV",
    "produces": "PRODUCES",
    "compiles_to": "COMPILES_TO",
    "maps_to": "MAPS_TO",
    "points_to": "POINTS_TO",
    "transitions_to": "TRANSITIONS_TO",
    "runtime_transform": "RUNTIME_TRANSFORM",
    "is_a": "IS_A",
    "assign": "ASSIGN",
}


def _esc(text: str) -> str:
    return text.replace("\\", "\\\\").replace('"', '\\"')


def _var(idx: int) -> str:
    return f"n{idx}"


def emit_cypher(statements: list[Statement]) -> str:
    # 1. decide a label per node id (default :Node), gather all node ids.
    label: dict[str, str] = {}
    ids: list[str] = []

    def see(node_id: str) -> None:
        if node_id not in label:
            label[node_id] = "Node"
            ids.append(node_id)

    for s in statements:
        see(s.subject)
        if s.predicate in _KIND_LABEL:
            label[s.subject] = _KIND_LABEL[s.predicate]
        if s.predicate in ("bounded", "placeholder", "entity", "glyph", "symbol", "transform"):
            continue
        if s.predicate == "has_type":
            see(s.object)
            label[s.object] = "Type"
        elif s.predicate == "mediates":
            see(s.object)
            see(s.meta["target"])
        else:
            see(s.object)

    lines: list[str] = []
    var_of: dict[str, str] = {}
    for i, node_id in enumerate(ids):
        v = _var(i)
        var_of[node_id] = v
        lines.append(f'MERGE ({v}:{label[node_id]} {{id:"{_esc(node_id)}"}})')

    # 2. properties and relationships
    for s in statements:
        sv = var_of[s.subject]
        if s.predicate == "bounded":
            lines.append(f"SET {sv}.bounded = true")
        elif s.predicate == "placeholder":
            lines.append(f'SET {sv}.placeholder = "{_esc(s.object)}"')
        elif s.predicate in ("entity", "glyph", "symbol", "transform"):
            if s.predicate == "glyph" and s.meta.get("name"):
                lines.append(f'SET {sv}.name = "{_esc(s.meta["name"])}"')
        elif s.predicate == "has_type":
            lines.append(f"MERGE ({sv})-[:HAS_TYPE]->({var_of[s.object]})")
        elif s.predicate == "mediates":
            ov, tv = var_of[s.object], var_of[s.meta["target"]]
            lines.append(f'MERGE ({sv})-[:MEDIATES {{target:"{_esc(s.meta["target"])}"}}]->({ov})')
            lines.append(f"MERGE ({sv})-[:MEDIATES_TARGET]->({tv})")
        else:
            rtype = _REL_TYPE.get(s.predicate, s.predicate.upper())
            lines.append(f"MERGE ({sv})-[:{rtype}]->({var_of[s.object]})")

    seen: set[str] = set()
    return "\n".join(l for l in lines if not (l in seen or seen.add(l))) + "\n"
