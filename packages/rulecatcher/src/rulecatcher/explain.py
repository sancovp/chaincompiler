from __future__ import annotations

import json
from sqlite3 import Connection
from typing import Any

from .db import (
    fetch_evidence,
    fetch_rule,
    fetch_rule_with_stats,
    find_rule_by_signature,
    list_raw_observed_transitions,
    list_rule_decisions,
    list_rules,
)
from .governance import summarize_rule_health
from .history import summarize_rule_decision
from .present import (
    serialize_evidence_row,
    serialize_observed_transition_row,
    serialize_rule_decision,
    serialize_rule_health,
    serialize_rule_row,
)


def explain_rule(
    connection: Connection,
    *,
    rule_id: int | None = None,
    scope: str = "global",
    rule_type: str | None = None,
    prefix_tokens: tuple[str, ...] = (),
    expected_token: str | None = None,
    history_limit: int = 10,
) -> dict[str, Any]:
    target_row = _resolve_rule_row(
        connection,
        rule_id=rule_id,
        scope=scope,
        rule_type=rule_type,
        prefix_tokens=prefix_tokens,
        expected_token=expected_token,
    )
    if target_row is None:
        raise ValueError("No matching rule found")

    current_rule_id = int(target_row["id"])
    stats_row = fetch_rule_with_stats(connection, current_rule_id)
    assert stats_row is not None

    rule_payload = serialize_rule_row(stats_row)
    health_payload = serialize_rule_health(summarize_rule_health(stats_row))
    evidence_payload = [serialize_evidence_row(item) for item in fetch_evidence(connection, current_rule_id)]
    history_payload = _rule_history_payload(connection, row=target_row, limit=history_limit)
    competing_rules = _competing_rule_payload(connection, row=target_row)
    transition_payload = _observed_transition_payload(connection, row=target_row)

    return {
        "selector": {
            "rule_id": current_rule_id,
            "scope": rule_payload["scope"],
            "rule_type": rule_payload["rule_type"],
            "prefix": list(rule_payload["prefix"]),
            "prefix_display": list(rule_payload["prefix_display"]),
            "expected_token": rule_payload["expected_token"],
            "expected_display": rule_payload["expected_display"],
        },
        "rule": rule_payload,
        "health": health_payload,
        "evidence": evidence_payload,
        "history": history_payload,
        "competing_rules": competing_rules,
        "observed_transitions": transition_payload,
        "summary": {
            "evidence_count": len(evidence_payload),
            "history_count": len(history_payload),
            "competing_rule_count": len(competing_rules),
            "observed_transition_count": len(transition_payload),
        },
    }


def render_rule_explanation(payload: dict[str, Any]) -> str:
    rule = payload["rule"]
    health = payload["health"]

    lines = [
        (
            f"[{rule['id']}] scope={rule['scope']} {rule['status']} {rule['rule_type']} "
            f"{rule['prefix_display']!r} -> {rule['expected_display']!r} "
            f"support={rule['support']}/{rule['total']} confidence={rule['confidence']:.2f}"
        ),
        (
            f"health recommendation={health['recommendation']} "
            f"evals={health['evaluation_count']} hits={health['hit_count']} "
            f"violations={health['violation_count']} violation_rate={health['violation_rate']:.2f}"
        ),
    ]

    if payload["evidence"]:
        lines.append("evidence:")
        for item in payload["evidence"]:
            lines.append(
                f"  {item['path']}:{item['line_no']} observed={item['observed_token']!r} context={item['context']!r}"
            )

    if payload["history"]:
        lines.append("history:")
        for item in payload["history"]:
            actor_text = "" if item["actor"] is None else f" actor={item['actor']}"
            source_text = "" if item["source"] is None else f" source={item['source']}"
            reason_text = "" if item["reason"] is None else f" reason={item['reason']!r}"
            auto_text = " automatic" if item["automatic"] else ""
            lines.append(
                f"  {item['created_at']}{auto_text} {item['previous_status']}->{item['new_status']}"
                f"{actor_text}{source_text}{reason_text}"
            )

    if payload["competing_rules"]:
        lines.append("competing_rules:")
        for item in payload["competing_rules"]:
            lines.append(
                f"  [{item['id']}] {item['status']} {item['expected_display']!r} "
                f"support={item['support']}/{item['total']} confidence={item['confidence']:.2f}"
            )

    if payload["observed_transitions"]:
        lines.append("observed_transitions:")
        for item in payload["observed_transitions"]:
            marker = " match" if item["next_token"] == rule["expected_token"] else ""
            lines.append(
                f"  {item['prefix_display']!r} -> {item['next_display']!r} "
                f"support={item['support']}/{item['total']} confidence={item['confidence']:.2f}{marker}"
            )

    return "\n".join(lines)


def _resolve_rule_row(
    connection: Connection,
    *,
    rule_id: int | None,
    scope: str,
    rule_type: str | None,
    prefix_tokens: tuple[str, ...],
    expected_token: str | None,
) -> object | None:
    if rule_id is not None:
        row = fetch_rule(connection, rule_id)
        if row is None:
            raise ValueError(f"Unknown rule id {rule_id}")
        return row

    if rule_type is None or expected_token is None or not prefix_tokens:
        raise ValueError(
            "explain requires either a rule id or the full signature: --rule-type, one or more --prefix-token, and --expected-token"
        )

    prefix_json = json.dumps(prefix_tokens, ensure_ascii=True)
    row = find_rule_by_signature(
        connection,
        scope=scope,
        rule_type=rule_type,
        prefix_json=prefix_json,
        expected_token=expected_token,
    )
    if row is None:
        raise ValueError(
            f"No matching rule found for scope={scope!r} rule_type={rule_type!r} prefix={list(prefix_tokens)!r} expected_token={expected_token!r}"
        )
    return row


def _rule_history_payload(connection: Connection, *, row: object, limit: int) -> list[dict[str, Any]]:
    prefix_json = str(row["prefix_json"])
    target_rule_id = int(row["id"])
    all_rows = list_rule_decisions(
        connection,
        scope=str(row["scope"]),
        rule_type=str(row["rule_type"]),
        limit=None,
    )
    matching_rows = [
        item
        for item in all_rows
        if str(item["prefix_json"]) == prefix_json
        and str(item["expected_token"]) == str(row["expected_token"])
        and (item["rule_id"] is None or int(item["rule_id"]) == target_rule_id)
    ]
    return [serialize_rule_decision(summarize_rule_decision(item)) for item in matching_rows[:limit]]


def _competing_rule_payload(connection: Connection, *, row: object) -> list[dict[str, Any]]:
    items = []
    target_prefix_json = str(row["prefix_json"])
    target_rule_type = str(row["rule_type"])
    target_expected_token = str(row["expected_token"])
    for candidate in list_rules(connection, None, scope=str(row["scope"]), rule_type=target_rule_type):
        if int(candidate["id"]) == int(row["id"]):
            continue
        if str(candidate["prefix_json"]) != target_prefix_json:
            continue
        if str(candidate["expected_token"]) == target_expected_token:
            continue
        items.append(serialize_rule_row(candidate))
    return items


def _observed_transition_payload(connection: Connection, *, row: object) -> list[dict[str, Any]]:
    if str(row["rule_type"]) != "next_token":
        return []

    transitions = []
    target_prefix_json = str(row["prefix_json"])
    for item in list_raw_observed_transitions(connection, scope=str(row["scope"])):
        if str(item["prefix_json"]) != target_prefix_json:
            continue
        transitions.append(
            serialize_observed_transition_row(
                {
                    "prefix_json": item["prefix_json"],
                    "next_token": item["next_token"],
                    "support": item["support"],
                    "total": item["total"],
                    "confidence": item["confidence"],
                    "rule_id": None,
                    "rule_status": None,
                }
            )
        )
    return transitions
