from __future__ import annotations

from collections import Counter
from typing import Any

from .present import display_prefix, display_token
from .snapshot import SNAPSHOT_FORMAT


def compare_scope_states(
    left_snapshot: dict[str, Any],
    right_snapshot: dict[str, Any],
    *,
    left_source: dict[str, Any],
    right_source: dict[str, Any],
    rule_type: str | None = None,
) -> dict[str, Any]:
    _validate_snapshot(left_snapshot)
    _validate_snapshot(right_snapshot)

    left_rules = _index_rules(left_snapshot, rule_type=rule_type)
    right_rules = _index_rules(right_snapshot, rule_type=rule_type)
    left_transitions = _index_transitions(left_snapshot, rule_type=rule_type)
    right_transitions = _index_transitions(right_snapshot, rule_type=rule_type)
    left_decisions = _index_decisions(left_snapshot, rule_type=rule_type)
    right_decisions = _index_decisions(right_snapshot, rule_type=rule_type)

    artifact_diff = _compare_artifacts(left_snapshot, right_snapshot)
    rule_diff = _compare_maps(left_rules, right_rules, fields=_RULE_CHANGE_FIELDS)
    transition_diff = _compare_maps(left_transitions, right_transitions, fields=_TRANSITION_CHANGE_FIELDS)
    decision_diff = _compare_decisions(left_decisions, right_decisions)

    payload = {
        "left": _source_payload(left_snapshot, left_source, rule_type=rule_type),
        "right": _source_payload(right_snapshot, right_source, rule_type=rule_type),
        "rule_type": rule_type,
        "artifacts": artifact_diff,
        "rules": rule_diff,
        "observed_transitions": transition_diff,
        "decisions": decision_diff,
    }
    payload["summary"] = {
        "artifact_added_count": len(artifact_diff["added"]),
        "artifact_removed_count": len(artifact_diff["removed"]),
        "artifact_changed_path_count": len(artifact_diff["changed_paths"]),
        "rule_added_count": len(rule_diff["added"]),
        "rule_removed_count": len(rule_diff["removed"]),
        "rule_changed_count": len(rule_diff["changed"]),
        "rule_unchanged_count": int(rule_diff["unchanged_count"]),
        "transition_added_count": len(transition_diff["added"]),
        "transition_removed_count": len(transition_diff["removed"]),
        "transition_changed_count": len(transition_diff["changed"]),
        "transition_unchanged_count": int(transition_diff["unchanged_count"]),
        "decision_added_count": len(decision_diff["added"]),
        "decision_removed_count": len(decision_diff["removed"]),
        "decision_unchanged_count": int(decision_diff["unchanged_count"]),
    }
    return payload


def render_compare_report(report: dict[str, Any], *, limit: int = 10) -> str:
    left = report["left"]
    right = report["right"]
    summary = report["summary"]
    decisions = report["decisions"]

    lines = [
        f"compare {left['reference']} -> {right['reference']}",
        (
            f"rules added={summary['rule_added_count']} removed={summary['rule_removed_count']} "
            f"changed={summary['rule_changed_count']} unchanged={summary['rule_unchanged_count']}"
        ),
        (
            f"transitions added={summary['transition_added_count']} removed={summary['transition_removed_count']} "
            f"changed={summary['transition_changed_count']} unchanged={summary['transition_unchanged_count']}"
        ),
        (
            f"decisions added={summary['decision_added_count']} removed={summary['decision_removed_count']} "
            f"unchanged={summary['decision_unchanged_count']} "
            f"left_total={decisions['left_total']} right_total={decisions['right_total']}"
        ),
    ]

    if summary["artifact_added_count"] or summary["artifact_removed_count"] or summary["artifact_changed_path_count"]:
        lines.append(
            (
                f"artifacts added={summary['artifact_added_count']} removed={summary['artifact_removed_count']} "
                f"changed_paths={summary['artifact_changed_path_count']}"
            )
        )

    _append_section(lines, "changed rules", report["rules"]["changed"], limit, _format_changed_rule)
    _append_section(lines, "added rules", report["rules"]["added"], limit, _format_rule_entry)
    _append_section(lines, "removed rules", report["rules"]["removed"], limit, _format_rule_entry)
    _append_section(lines, "changed transitions", report["observed_transitions"]["changed"], limit, _format_changed_transition)
    _append_section(lines, "added transitions", report["observed_transitions"]["added"], limit, _format_transition_entry)
    _append_section(lines, "removed transitions", report["observed_transitions"]["removed"], limit, _format_transition_entry)
    _append_section(lines, "added decisions", report["decisions"]["added"], limit, _format_decision_entry)
    _append_section(lines, "removed decisions", report["decisions"]["removed"], limit, _format_decision_entry)
    _append_section(lines, "changed artifact paths", report["artifacts"]["changed_paths"], limit, _format_changed_artifact_path)
    _append_section(lines, "added artifacts", report["artifacts"]["added"], limit, _format_artifact_entry)
    _append_section(lines, "removed artifacts", report["artifacts"]["removed"], limit, _format_artifact_entry)

    return "\n".join(lines)


_RULE_CHANGE_FIELDS = (
    "status",
    "support",
    "total",
    "confidence",
    "hit_count",
    "violation_count",
    "last_hit_at",
    "last_violation_at",
    "evidence_count",
)

_TRANSITION_CHANGE_FIELDS = (
    "support",
    "total",
    "confidence",
)


def _validate_snapshot(snapshot: dict[str, Any]) -> None:
    if str(snapshot.get("format")) != SNAPSHOT_FORMAT:
        raise ValueError(f"Unsupported snapshot format {snapshot.get('format')!r}")


def _source_payload(snapshot: dict[str, Any], source: dict[str, Any], *, rule_type: str | None) -> dict[str, Any]:
    return {
        "reference": str(source["reference"]),
        "kind": str(source["kind"]),
        "scope": str(snapshot.get("scope", "global")),
        "artifact_count": len(snapshot.get("artifacts", [])),
        "rule_count": len(_index_rules(snapshot, rule_type=rule_type)),
        "transition_count": len(_index_transitions(snapshot, rule_type=rule_type)),
        "decision_count": len(_index_decisions(snapshot, rule_type=rule_type)),
    }


def _index_rules(snapshot: dict[str, Any], *, rule_type: str | None) -> dict[tuple[object, ...], dict[str, Any]]:
    items: dict[tuple[object, ...], dict[str, Any]] = {}
    for rule in snapshot.get("rules", []):
        current_rule_type = str(rule["rule_type"])
        if rule_type is not None and current_rule_type != rule_type:
            continue
        prefix = tuple(str(token) for token in rule["prefix"])
        expected_token = str(rule["expected_token"])
        stats = rule.get("stats", {})
        if not isinstance(stats, dict):
            stats = {}
        item = {
            "rule_type": current_rule_type,
            "prefix": list(prefix),
            "prefix_display": display_prefix(current_rule_type, prefix),
            "expected_token": expected_token,
            "expected_display": display_token(current_rule_type, expected_token),
            "status": str(rule["status"]),
            "support": int(rule["support"]),
            "total": int(rule["total"]),
            "confidence": float(rule["confidence"]),
            "hit_count": int(stats.get("hit_count", 0)),
            "violation_count": int(stats.get("violation_count", 0)),
            "last_hit_at": None if stats.get("last_hit_at") is None else str(stats["last_hit_at"]),
            "last_violation_at": None if stats.get("last_violation_at") is None else str(stats["last_violation_at"]),
            "evidence_count": len(rule.get("evidence", [])),
        }
        items[_rule_signature(current_rule_type, prefix, expected_token)] = item
    return items


def _index_transitions(snapshot: dict[str, Any], *, rule_type: str | None) -> dict[tuple[object, ...], dict[str, Any]]:
    if rule_type == "next_kind":
        return {}

    items: dict[tuple[object, ...], dict[str, Any]] = {}
    for transition in snapshot.get("observed_transitions", []):
        prefix = tuple(str(token) for token in transition["prefix"])
        next_token = str(transition["next_token"])
        item = {
            "rule_type": "next_token",
            "prefix": list(prefix),
            "prefix_display": display_prefix("next_token", prefix),
            "next_token": next_token,
            "next_display": display_token("next_token", next_token),
            "support": int(transition["support"]),
            "total": int(transition["total"]),
            "confidence": float(transition["confidence"]),
        }
        items[_transition_signature(prefix, next_token)] = item
    return items


def _index_decisions(snapshot: dict[str, Any], *, rule_type: str | None) -> dict[tuple[object, ...], dict[str, Any]]:
    items: dict[tuple[object, ...], dict[str, Any]] = {}
    for decision in snapshot.get("decisions", []):
        current_rule_type = str(decision["rule_type"])
        if rule_type is not None and current_rule_type != rule_type:
            continue
        prefix = tuple(str(token) for token in decision["prefix"])
        expected_token = str(decision["expected_token"])
        item = {
            "rule_type": current_rule_type,
            "prefix": list(prefix),
            "prefix_display": display_prefix(current_rule_type, prefix),
            "expected_token": expected_token,
            "expected_display": display_token(current_rule_type, expected_token),
            "previous_status": str(decision["previous_status"]),
            "new_status": str(decision["new_status"]),
            "automatic": bool(decision["automatic"]),
            "actor": None if decision.get("actor") is None else str(decision["actor"]),
            "source": None if decision.get("source") is None else str(decision["source"]),
            "reason": None if decision.get("reason") is None else str(decision["reason"]),
            "created_at": str(decision["created_at"]),
        }
        items[_decision_signature(item)] = item
    return items


def _compare_artifacts(left_snapshot: dict[str, Any], right_snapshot: dict[str, Any]) -> dict[str, Any]:
    left_items = {
        _artifact_signature(str(artifact["path"]), str(artifact["sha256"])): _normalize_artifact(artifact)
        for artifact in left_snapshot.get("artifacts", [])
    }
    right_items = {
        _artifact_signature(str(artifact["path"]), str(artifact["sha256"])): _normalize_artifact(artifact)
        for artifact in right_snapshot.get("artifacts", [])
    }

    left_paths = _artifact_paths(left_snapshot)
    right_paths = _artifact_paths(right_snapshot)
    changed_paths = []
    for path in sorted(set(left_paths) & set(right_paths)):
        if left_paths[path] == right_paths[path]:
            continue
        changed_paths.append(
            {
                "path": path,
                "left_sha256": left_paths[path],
                "right_sha256": right_paths[path],
            }
        )

    return {
        "added": [right_items[key] for key in sorted(set(right_items) - set(left_items))],
        "removed": [left_items[key] for key in sorted(set(left_items) - set(right_items))],
        "changed_paths": changed_paths,
        "unchanged_count": len(set(left_items) & set(right_items)),
    }


def _artifact_paths(snapshot: dict[str, Any]) -> dict[str, str]:
    return {str(artifact["path"]): str(artifact["sha256"]) for artifact in snapshot.get("artifacts", [])}


def _compare_maps(
    left_items: dict[tuple[object, ...], dict[str, Any]],
    right_items: dict[tuple[object, ...], dict[str, Any]],
    *,
    fields: tuple[str, ...],
) -> dict[str, Any]:
    shared_keys = sorted(set(left_items) & set(right_items))
    changed: list[dict[str, Any]] = []
    unchanged_count = 0

    for key in shared_keys:
        left_item = left_items[key]
        right_item = right_items[key]
        field_changes = _field_changes(left_item, right_item, fields=fields)
        if field_changes:
            changed.append(
                {
                    "signature": _signature_payload(right_item),
                    "left": left_item,
                    "right": right_item,
                    "changes": field_changes,
                }
            )
            continue
        unchanged_count += 1

    return {
        "added": [right_items[key] for key in sorted(set(right_items) - set(left_items))],
        "removed": [left_items[key] for key in sorted(set(left_items) - set(right_items))],
        "changed": changed,
        "unchanged_count": unchanged_count,
    }


def _compare_decisions(
    left_items: dict[tuple[object, ...], dict[str, Any]],
    right_items: dict[tuple[object, ...], dict[str, Any]],
) -> dict[str, Any]:
    left_values = list(left_items.values())
    right_values = list(right_items.values())
    return {
        "added": [right_items[key] for key in sorted(set(right_items) - set(left_items))],
        "removed": [left_items[key] for key in sorted(set(left_items) - set(right_items))],
        "unchanged_count": len(set(left_items) & set(right_items)),
        "left_total": len(left_values),
        "right_total": len(right_values),
        "left_by_new_status": dict(sorted(Counter(str(item["new_status"]) for item in left_values).items())),
        "right_by_new_status": dict(sorted(Counter(str(item["new_status"]) for item in right_values).items())),
        "left_automatic_count": sum(1 for item in left_values if item["automatic"]),
        "right_automatic_count": sum(1 for item in right_values if item["automatic"]),
    }


def _field_changes(
    left_item: dict[str, Any],
    right_item: dict[str, Any],
    *,
    fields: tuple[str, ...],
) -> dict[str, dict[str, Any]]:
    changes: dict[str, dict[str, Any]] = {}
    for field in fields:
        if left_item.get(field) == right_item.get(field):
            continue
        changes[field] = {
            "left": left_item.get(field),
            "right": right_item.get(field),
        }
    return changes


def _signature_payload(item: dict[str, Any]) -> dict[str, Any]:
    payload = {
        "rule_type": str(item["rule_type"]),
        "prefix": list(item["prefix"]),
        "prefix_display": list(item["prefix_display"]),
    }
    if "expected_token" in item:
        payload["expected_token"] = str(item["expected_token"])
        payload["expected_display"] = str(item["expected_display"])
    if "next_token" in item:
        payload["next_token"] = str(item["next_token"])
        payload["next_display"] = str(item["next_display"])
    return payload


def _rule_signature(rule_type: str, prefix: tuple[str, ...], expected_token: str) -> tuple[object, ...]:
    return ("rule", rule_type, prefix, expected_token)


def _transition_signature(prefix: tuple[str, ...], next_token: str) -> tuple[object, ...]:
    return ("transition", prefix, next_token)


def _artifact_signature(path: str, sha256: str) -> tuple[str, str, str]:
    return ("artifact", path, sha256)


def _decision_signature(item: dict[str, Any]) -> tuple[object, ...]:
    return (
        "decision",
        str(item["rule_type"]),
        tuple(str(token) for token in item["prefix"]),
        str(item["expected_token"]),
        str(item["previous_status"]),
        str(item["new_status"]),
        bool(item["automatic"]),
        item["actor"],
        item["source"],
        item["reason"],
        str(item["created_at"]),
    )


def _normalize_artifact(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "path": str(item["path"]),
        "sha256": str(item["sha256"]),
    }


def _append_section(
    lines: list[str],
    title: str,
    items: list[dict[str, Any]],
    limit: int,
    formatter,
) -> None:
    if not items:
        return
    lines.append(f"{title}:")
    for item in items[:limit]:
        lines.append(f"  {formatter(item)}")
    remaining = len(items) - min(len(items), limit)
    if remaining > 0:
        lines.append(f"  ... {remaining} more")


def _format_rule_entry(item: dict[str, Any]) -> str:
    return (
        f"{item['rule_type']} {item['prefix_display']!r} -> {item['expected_display']!r} "
        f"status={item['status']} support={item['support']}/{item['total']} "
        f"confidence={item['confidence']:.2f}"
    )


def _format_changed_rule(item: dict[str, Any]) -> str:
    signature = item["signature"]
    return (
        f"{signature['rule_type']} {signature['prefix_display']!r} -> {signature['expected_display']!r} "
        f"{_format_change_map(item['changes'])}"
    )


def _format_transition_entry(item: dict[str, Any]) -> str:
    return (
        f"{item['prefix_display']!r} -> {item['next_display']!r} "
        f"support={item['support']}/{item['total']} confidence={item['confidence']:.2f}"
    )


def _format_changed_transition(item: dict[str, Any]) -> str:
    signature = item["signature"]
    return (
        f"{signature['prefix_display']!r} -> {signature['next_display']!r} "
        f"{_format_change_map(item['changes'])}"
    )


def _format_decision_entry(item: dict[str, Any]) -> str:
    actor_text = "" if item["actor"] is None else f" actor={item['actor']}"
    source_text = "" if item["source"] is None else f" source={item['source']}"
    return (
        f"{item['created_at']} {item['previous_status']}->{item['new_status']} "
        f"{item['rule_type']} {item['prefix_display']!r} -> {item['expected_display']!r}"
        f"{actor_text}{source_text}"
    )


def _format_artifact_entry(item: dict[str, Any]) -> str:
    return f"{item['path']} sha256={item['sha256']}"


def _format_changed_artifact_path(item: dict[str, Any]) -> str:
    return f"{item['path']} {item['left_sha256']} -> {item['right_sha256']}"


def _format_change_map(changes: dict[str, dict[str, Any]]) -> str:
    return " ".join(
        f"{field}={_compact_value(change['left'])}->{_compact_value(change['right'])}"
        for field, change in sorted(changes.items())
    )


def _compact_value(value: object) -> str:
    if isinstance(value, float):
        return f"{value:.2f}"
    return str(value)
