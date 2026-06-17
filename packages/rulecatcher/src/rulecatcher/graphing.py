from __future__ import annotations

import json
from sqlite3 import Connection
from typing import Any

from .db import list_observed_transitions, list_rules
from .governance import list_rule_health
from .history import read_rule_history
from .present import (
    display_prefix,
    display_token,
    serialize_observed_transition_row,
    serialize_rule_decision,
    serialize_rule_health,
    serialize_rule_row,
)


def build_transition_graph(
    connection: Connection,
    *,
    scope: str = "global",
    layer: str = "observed",
    rule_type: str | None = None,
    status: str | None = None,
    decision_limit: int = 20,
) -> dict[str, Any]:
    if layer == "observed":
        return _build_observed_graph(connection, scope=scope)
    if layer == "rules":
        return _build_rule_graph(connection, scope=scope, rule_type=rule_type, status=status)
    if layer == "metasystem":
        return _build_metasystem_graph(
            connection,
            scope=scope,
            rule_type=rule_type,
            status=status,
            decision_limit=decision_limit,
        )
    raise ValueError(f"Unsupported graph layer {layer!r}")


def render_transition_graph(
    connection: Connection,
    *,
    scope: str = "global",
    format_name: str = "mermaid",
    layer: str = "observed",
    rule_type: str | None = None,
    status: str | None = None,
    decision_limit: int = 20,
) -> str:
    if layer == "observed":
        rows = list_observed_transitions(connection, scope=scope)
        if format_name == "table":
            return _render_transition_table(rows)
        if format_name == "mermaid":
            return _render_transition_mermaid(rows)
        if format_name == "dot":
            return _render_graph_dot(
                build_transition_graph(
                    connection,
                    scope=scope,
                    layer=layer,
                    rule_type=rule_type,
                    status=status,
                    decision_limit=decision_limit,
                )
            )
        raise ValueError(f"Unsupported graph format {format_name!r}")

    if layer == "rules":
        rows = list_rules(connection, status=status, scope=scope, rule_type=rule_type)
        if format_name == "table":
            return _render_rule_table(rows)
        if format_name == "mermaid":
            return _render_rule_mermaid(rows)
        if format_name == "dot":
            return _render_graph_dot(
                build_transition_graph(
                    connection,
                    scope=scope,
                    layer=layer,
                    rule_type=rule_type,
                    status=status,
                    decision_limit=decision_limit,
                )
            )
        raise ValueError(f"Unsupported graph format {format_name!r}")

    if layer == "metasystem":
        graph = build_transition_graph(
            connection,
            scope=scope,
            layer=layer,
            rule_type=rule_type,
            status=status,
            decision_limit=decision_limit,
        )
        if format_name == "table":
            return _render_metasystem_table(graph)
        if format_name == "mermaid":
            return _render_graph_mermaid(graph)
        if format_name == "dot":
            return _render_graph_dot(graph)
        raise ValueError(f"Unsupported graph format {format_name!r}")

    raise ValueError(f"Unsupported graph layer {layer!r}")


def _build_observed_graph(connection: Connection, *, scope: str) -> dict[str, Any]:
    graph = _seed_graph(scope=scope, layer="observed", rule_type=None, status=None)
    rows = list_observed_transitions(connection, scope=scope)
    for row in rows:
        item = serialize_observed_transition_row(row)
        prefix = tuple(str(token) for token in item["prefix"])
        prefix_id = _prefix_node_id("next_token", prefix)
        token = str(item["next_token"])
        token_id = _token_node_id("next_token", token)

        _upsert_node(
            graph,
            {
                "id": prefix_id,
                "kind": "prefix",
                "scope": scope,
                "rule_type": "next_token",
                "prefix": list(prefix),
                "prefix_display": display_prefix("next_token", prefix),
                "label": _prefix_label("next_token", prefix),
            },
        )
        _upsert_node(
            graph,
            {
                "id": token_id,
                "kind": "token",
                "scope": scope,
                "rule_type": "next_token",
                "token": token,
                "display": item["next_display"],
                "label": str(item["next_display"]),
            },
        )
        graph["edges"].append(
            {
                "source": prefix_id,
                "target": token_id,
                "kind": "observed_transition",
                "scope": scope,
                "rule_type": "next_token",
                "support": int(item["support"]),
                "total": int(item["total"]),
                "confidence": float(item["confidence"]),
                "rule_id": item["rule_id"],
                "rule_status": item["rule_status"],
                "label": _transition_edge_label(item),
            }
        )

    return _finalize_graph(graph)


def _build_rule_graph(
    connection: Connection,
    *,
    scope: str,
    rule_type: str | None,
    status: str | None,
) -> dict[str, Any]:
    graph = _seed_graph(scope=scope, layer="rules", rule_type=rule_type, status=status)
    rows = list_rules(connection, status=status, scope=scope, rule_type=rule_type)
    for row in rows:
        item = serialize_rule_row(row)
        _append_rule_structure(graph, item)
    return _finalize_graph(graph)


def _build_metasystem_graph(
    connection: Connection,
    *,
    scope: str,
    rule_type: str | None,
    status: str | None,
    decision_limit: int,
) -> dict[str, Any]:
    graph = _seed_graph(scope=scope, layer="metasystem", rule_type=rule_type, status=status)

    if rule_type in {None, "next_token"}:
        _merge_graph(graph, _build_observed_graph(connection, scope=scope))

    health_items = list_rule_health(connection, scope=scope, status=status, rule_type=rule_type)
    allowed_rule_ids = {int(item.rule_id) for item in health_items}
    for health in health_items:
        item = serialize_rule_health(health)
        _append_rule_structure(graph, item, health=item)

    decisions = read_rule_history(connection, scope=scope, rule_type=rule_type, limit=decision_limit)
    for decision in decisions:
        item = serialize_rule_decision(decision)
        if allowed_rule_ids and item["rule_id"] is not None and int(item["rule_id"]) not in allowed_rule_ids:
            continue
        _append_decision_structure(graph, item)

    return _finalize_graph(graph)


def _append_rule_structure(
    graph: dict[str, Any],
    item: dict[str, Any],
    *,
    health: dict[str, Any] | None = None,
) -> None:
    scope = str(item["scope"])
    current_rule_type = str(item["rule_type"])
    prefix = tuple(str(token) for token in item["prefix"])
    prefix_id = _prefix_node_id(current_rule_type, prefix)
    rule_id = int(item["rule_id"]) if "rule_id" in item else int(item["id"])
    rule_node_id = _rule_node_id(rule_id)
    expected_token = str(item["expected_token"])
    target_id = _token_node_id(current_rule_type, expected_token)

    _upsert_node(
        graph,
        {
            "id": prefix_id,
            "kind": "prefix",
            "scope": scope,
            "rule_type": current_rule_type,
            "prefix": list(prefix),
            "prefix_display": list(item["prefix_display"]),
            "label": _prefix_label(current_rule_type, prefix),
        },
    )
    _upsert_node(
        graph,
        {
            "id": rule_node_id,
            "kind": "rule",
            "scope": scope,
            "rule_id": rule_id,
            "status": item["status"],
            "rule_type": current_rule_type,
            "prefix": list(prefix),
            "prefix_display": list(item["prefix_display"]),
            "expected_token": expected_token,
            "expected_display": item["expected_display"],
            "support": int(item["support"]),
            "total": int(item["total"]),
            "confidence": float(item["confidence"]),
            "label": _rule_label(rule_id=rule_id, status=str(item["status"]), rule_type=current_rule_type),
            "health": None if health is None else _health_payload(health),
        },
    )
    _upsert_node(
        graph,
        {
            "id": target_id,
            "kind": "token" if current_rule_type == "next_token" else "token_class",
            "scope": scope,
            "rule_type": current_rule_type,
            "token": expected_token,
            "display": item["expected_display"],
            "label": str(item["expected_display"]),
        },
    )

    graph["edges"].append(
        {
            "source": prefix_id,
            "target": rule_node_id,
            "kind": "governs",
            "scope": scope,
            "rule_id": rule_id,
            "status": item["status"],
            "rule_type": current_rule_type,
            "label": f"{current_rule_type} {item['status']}",
        }
    )
    expects_edge = {
        "source": rule_node_id,
        "target": target_id,
        "kind": "expects",
        "scope": scope,
        "rule_id": rule_id,
        "status": item["status"],
        "rule_type": current_rule_type,
        "support": int(item["support"]),
        "total": int(item["total"]),
        "confidence": float(item["confidence"]),
        "label": _rule_expectation_label(item, health=health),
    }
    if health is not None:
        expects_edge["health_recommendation"] = health["recommendation"]
        expects_edge["hit_count"] = int(health["hit_count"])
        expects_edge["violation_count"] = int(health["violation_count"])
    graph["edges"].append(expects_edge)


def _append_decision_structure(graph: dict[str, Any], item: dict[str, Any]) -> None:
    scope = str(item["scope"])
    decision_node_id = _decision_node_id(int(item["id"]))
    target_rule_id = _history_target_rule_node_id(item)

    _upsert_node(
        graph,
        {
            "id": decision_node_id,
            "kind": "decision",
            "scope": scope,
            "decision_id": int(item["id"]),
            "rule_id": item["rule_id"],
            "previous_status": item["previous_status"],
            "new_status": item["new_status"],
            "automatic": bool(item["automatic"]),
            "actor": item["actor"],
            "source": item["source"],
            "reason": item["reason"],
            "created_at": item["created_at"],
            "label": _decision_label(item),
        },
    )

    if item["rule_id"] is None:
        prefix = tuple(str(token) for token in item["prefix"])
        rule_type = str(item["rule_type"])
        _upsert_node(
            graph,
            {
                "id": target_rule_id,
                "kind": "rule_signature",
                "scope": scope,
                "rule_type": rule_type,
                "prefix": list(prefix),
                "prefix_display": list(item["prefix_display"]),
                "expected_token": item["expected_token"],
                "expected_display": item["expected_display"],
                "label": _rule_signature_label(item),
            },
        )

    graph["edges"].append(
        {
            "source": decision_node_id,
            "target": target_rule_id,
            "kind": "decision",
            "scope": scope,
            "rule_id": item["rule_id"],
            "rule_type": item["rule_type"],
            "previous_status": item["previous_status"],
            "new_status": item["new_status"],
            "automatic": bool(item["automatic"]),
            "actor": item["actor"],
            "decision_source": item["source"],
            "reason": item["reason"],
            "created_at": item["created_at"],
            "label": _decision_edge_label(item),
        }
    )


def _seed_graph(
    *,
    scope: str,
    layer: str,
    rule_type: str | None,
    status: str | None,
) -> dict[str, Any]:
    return {
        "scope": scope,
        "layer": layer,
        "rule_type": rule_type,
        "status": status,
        "nodes": [],
        "edges": [],
    }


def _merge_graph(target: dict[str, Any], source: dict[str, Any]) -> None:
    for node in source["nodes"]:
        _upsert_node(target, node)
    target["edges"].extend(source["edges"])


def _upsert_node(graph: dict[str, Any], node: dict[str, Any]) -> None:
    index = graph.setdefault("_node_index", {})
    node_id = str(node["id"])
    if node_id not in index:
        graph["nodes"].append(node)
        index[node_id] = node
        return

    existing = index[node_id]
    for key, value in node.items():
        if key not in existing or existing[key] in (None, "", [], {}):
            existing[key] = value


def _finalize_graph(graph: dict[str, Any]) -> dict[str, Any]:
    index = graph.pop("_node_index", {})
    node_map = index if index else {str(node["id"]): node for node in graph["nodes"]}
    for edge in graph["edges"]:
        edge["source_label"] = str(node_map.get(str(edge["source"]), {}).get("label", edge["source"]))
        edge["target_label"] = str(node_map.get(str(edge["target"]), {}).get("label", edge["target"]))

    graph["nodes"] = sorted(graph["nodes"], key=lambda item: (str(item["kind"]), str(item["id"])))
    graph["edges"] = sorted(
        graph["edges"],
        key=lambda item: (
            str(item["kind"]),
            str(item["source"]),
            str(item["target"]),
            str(item.get("label", "")),
        ),
    )
    graph["summary"] = {
        "node_count": len(graph["nodes"]),
        "edge_count": len(graph["edges"]),
        "observed_transition_count": sum(1 for edge in graph["edges"] if edge["kind"] == "observed_transition"),
        "rule_count": sum(1 for node in graph["nodes"] if node["kind"] == "rule"),
        "decision_count": sum(1 for node in graph["nodes"] if node["kind"] == "decision"),
    }
    return graph


def _render_transition_table(rows: list[object]) -> str:
    if not rows:
        return "no transitions"

    lines: list[str] = []
    for row in rows:
        item = serialize_observed_transition_row(row)
        lines.append(
            f"{item['prefix_display']!r} -> {item['next_display']!r} "
            f"support={item['support']}/{item['total']} "
            f"confidence={item['confidence']:.2f} "
            f"status={item['rule_status']}"
        )
    return "\n".join(lines)


def _render_transition_mermaid(rows: list[object]) -> str:
    if not rows:
        return 'graph TD\n  empty["no transitions"]'

    lines = ["graph TD"]
    seen_prefixes: set[tuple[str, ...]] = set()
    seen_tokens: set[str] = set()
    prefix_ids: dict[tuple[str, ...], str] = {}
    token_ids: dict[str, str] = {}

    for row in rows:
        prefix = tuple(str(token) for token in json.loads(str(row["prefix_json"])))
        if prefix not in prefix_ids:
            prefix_ids[prefix] = f"p{len(prefix_ids) + 1}"
        prefix_id = prefix_ids[prefix]

        token = str(row["next_token"])
        if token not in token_ids:
            token_ids[token] = f"t{len(token_ids) + 1}"
        token_id = token_ids[token]

        if prefix not in seen_prefixes:
            seen_prefixes.add(prefix)
            lines.append(f'  {prefix_id}["{_escape(_prefix_label("next_token", prefix))}"]')

        if token not in seen_tokens:
            seen_tokens.add(token)
            lines.append(f'  {token_id}["{_escape(token)}"]')

        status = str(row["rule_status"]) if row["rule_status"] is not None else "observed"
        marker = " *" if status == "adopted" else ""
        label = f'{row["support"]}/{row["total"]} {float(row["confidence"]):.2f} {status}{marker}'
        lines.append(f'  {prefix_id} -->|"{_escape(label)}"| {token_id}')

    return "\n".join(lines)


def _render_rule_table(rows: list[object]) -> str:
    if not rows:
        return "no rules"

    lines: list[str] = []
    for row in rows:
        item = serialize_rule_row(row)
        lines.append(
            f"{item['rule_type']} {item['prefix_display']!r} -> {item['expected_display']!r} "
            f"support={item['support']}/{item['total']} "
            f"confidence={item['confidence']:.2f} "
            f"status={item['status']}"
        )
    return "\n".join(lines)


def _render_rule_mermaid(rows: list[object]) -> str:
    if not rows:
        return 'graph TD\n  empty["no rules"]'

    lines = ["graph TD"]
    seen_prefixes: set[tuple[str, tuple[str, ...]]] = set()
    seen_targets: set[tuple[str, str]] = set()
    prefix_ids: dict[tuple[str, tuple[str, ...]], str] = {}
    target_ids: dict[tuple[str, str], str] = {}

    for row in rows:
        rule_type = str(row["rule_type"])
        prefix = tuple(str(token) for token in json.loads(str(row["prefix_json"])))
        prefix_key = (rule_type, prefix)
        if prefix_key not in prefix_ids:
            prefix_ids[prefix_key] = f"rp{len(prefix_ids) + 1}"
        prefix_id = prefix_ids[prefix_key]

        target = str(row["expected_token"])
        target_key = (rule_type, target)
        if target_key not in target_ids:
            target_ids[target_key] = f"rt{len(target_ids) + 1}"
        target_id = target_ids[target_key]

        if prefix_key not in seen_prefixes:
            seen_prefixes.add(prefix_key)
            lines.append(f'  {prefix_id}["{_escape(_prefix_label(rule_type, prefix))}"]')

        if target_key not in seen_targets:
            seen_targets.add(target_key)
            lines.append(f'  {target_id}["{_escape(display_token(rule_type, target))}"]')

        label = f'{rule_type} {row["support"]}/{row["total"]} {float(row["confidence"]):.2f} {row["status"]}'
        lines.append(f'  {prefix_id} -->|"{_escape(label)}"| {target_id}')

    return "\n".join(lines)


def _render_metasystem_table(graph: dict[str, Any]) -> str:
    if not graph["edges"]:
        return "no graph"

    lines: list[str] = []
    for edge in graph["edges"]:
        if edge["kind"] == "observed_transition":
            lines.append(
                f"observed {edge['source_label']!r} -> {edge['target_label']!r} "
                f"support={edge['support']}/{edge['total']} "
                f"confidence={edge['confidence']:.2f} "
                f"status={edge['rule_status']}"
            )
            continue
        if edge["kind"] == "governs":
            lines.append(
                f"governs {edge['source_label']!r} -> {edge['target_label']!r} "
                f"rule_type={edge['rule_type']} status={edge['status']}"
            )
            continue
        if edge["kind"] == "expects":
            suffix = ""
            if edge.get("health_recommendation") is not None:
                suffix = f" health={edge['health_recommendation']}"
            lines.append(
                f"expects {edge['source_label']!r} -> {edge['target_label']!r} "
                f"support={edge['support']}/{edge['total']} "
                f"confidence={edge['confidence']:.2f} "
                f"status={edge['status']}{suffix}"
            )
            continue
        if edge["kind"] == "decision":
            actor = "" if edge["actor"] is None else f" actor={edge['actor']}"
            source = "" if edge["decision_source"] is None else f" source={edge['decision_source']}"
            lines.append(
                f"decision {edge['source_label']!r} -> {edge['target_label']!r} "
                f"{edge['previous_status']}->{edge['new_status']} "
                f"automatic={edge['automatic']}{actor}{source}"
            )
            continue
        lines.append(f"{edge['kind']} {edge['source_label']!r} -> {edge['target_label']!r}")
    return "\n".join(lines)


def _render_graph_mermaid(graph: dict[str, Any]) -> str:
    if not graph["nodes"]:
        return 'graph TD\n  empty["no graph"]'

    lines = ["graph TD"]
    alias_map = {str(node["id"]): f"n{index}" for index, node in enumerate(graph["nodes"], start=1)}

    for node in graph["nodes"]:
        alias = alias_map[str(node["id"])]
        lines.append(f'  {alias}["{_escape(str(node["label"]))}"]')

    for edge in graph["edges"]:
        source = alias_map[str(edge["source"])]
        target = alias_map[str(edge["target"])]
        arrow = _mermaid_arrow(edge["kind"])
        label = str(edge.get("label", ""))
        if label:
            lines.append(f'  {source} {arrow}|"{_escape(label)}"| {target}')
        else:
            lines.append(f"  {source} {arrow} {target}")

    return "\n".join(lines)


def _render_graph_dot(graph: dict[str, Any]) -> str:
    if not graph["nodes"]:
        return 'digraph rulecatcher {\n  empty [label="no graph"];\n}'

    lines = ["digraph rulecatcher {", "  rankdir=LR;"]
    for node in graph["nodes"]:
        node_id = _escape_dot(str(node["id"]))
        label = _escape_dot(str(node["label"]))
        shape = _dot_shape(str(node["kind"]))
        lines.append(f'  "{node_id}" [label="{label}", shape={shape}];')
    for edge in graph["edges"]:
        source = _escape_dot(str(edge["source"]))
        target = _escape_dot(str(edge["target"]))
        label = _escape_dot(str(edge.get("label", "")))
        style = _dot_style(str(edge["kind"]))
        lines.append(f'  "{source}" -> "{target}" [label="{label}", style={style}];')
    lines.append("}")
    return "\n".join(lines)


def _prefix_node_id(rule_type: str, prefix: tuple[str, ...]) -> str:
    return f"prefix:{rule_type}:{json.dumps(prefix, ensure_ascii=True, separators=(',', ':'))}"


def _token_node_id(rule_type: str, token: str) -> str:
    return f"token:{rule_type}:{token}"


def _rule_node_id(rule_id: int) -> str:
    return f"rule:{rule_id}"


def _decision_node_id(decision_id: int) -> str:
    return f"decision:{decision_id}"


def _history_target_rule_node_id(item: dict[str, Any]) -> str:
    if item["rule_id"] is not None:
        return _rule_node_id(int(item["rule_id"]))
    prefix = tuple(str(token) for token in item["prefix"])
    return (
        "rule-signature:"
        f"{item['rule_type']}:"
        f"{json.dumps(prefix, ensure_ascii=True, separators=(',', ':'))}:"
        f"{item['expected_token']}"
    )


def _prefix_label(rule_type: str, prefix: tuple[str, ...]) -> str:
    return " ".join(display_prefix(rule_type, prefix))


def _rule_label(*, rule_id: int, status: str, rule_type: str) -> str:
    return f"rule#{rule_id} {rule_type} {status}"


def _rule_signature_label(item: dict[str, Any]) -> str:
    prefix = " ".join(str(token) for token in item["prefix_display"])
    return f"rule? {item['rule_type']} {prefix} -> {item['expected_display']}"


def _decision_label(item: dict[str, Any]) -> str:
    return f"decision#{item['id']} {item['previous_status']}->{item['new_status']}"


def _transition_edge_label(item: dict[str, Any]) -> str:
    return f"{item['support']}/{item['total']} {item['confidence']:.2f} {item['rule_status']}"


def _rule_expectation_label(item: dict[str, Any], *, health: dict[str, Any] | None) -> str:
    base = f"{item['support']}/{item['total']} {item['confidence']:.2f} {item['status']}"
    if health is None:
        return base
    return f"{base} {health['recommendation']}"


def _decision_edge_label(item: dict[str, Any]) -> str:
    parts = [f"{item['previous_status']}->{item['new_status']}"]
    if item["automatic"]:
        parts.append("automatic")
    if item["actor"] is not None:
        parts.append(f"actor={item['actor']}")
    return " ".join(parts)


def _health_payload(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "recommendation": item["recommendation"],
        "hit_count": int(item["hit_count"]),
        "violation_count": int(item["violation_count"]),
        "evaluation_count": int(item["evaluation_count"]),
        "violation_rate": float(item["violation_rate"]),
        "last_hit_at": item["last_hit_at"],
        "last_violation_at": item["last_violation_at"],
    }


def _mermaid_arrow(kind: str) -> str:
    if kind == "decision":
        return "-.->"
    if kind == "expects":
        return "==>"
    return "-->"


def _dot_shape(kind: str) -> str:
    if kind == "token":
        return "ellipse"
    if kind == "token_class":
        return "ellipse"
    if kind == "rule":
        return "diamond"
    if kind == "decision":
        return "note"
    return "box"


def _dot_style(kind: str) -> str:
    if kind == "decision":
        return "dashed"
    if kind == "expects":
        return "bold"
    return "solid"


def _escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _escape_dot(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')
