from __future__ import annotations

from collections import Counter
from sqlite3 import Connection
from typing import Any

from .db import fetch_artifacts, list_observed_transitions, list_rules
from .governance import list_rule_health
from .history import read_rule_history
from .present import build_conflict_groups, serialize_rule_decision, serialize_rule_health, serialize_rule_proposal, serialize_rule_row
from .triage import triage_pending_rules


def build_scope_report(
    connection: Connection,
    *,
    scope: str = "global",
    rule_type: str | None = None,
    triage_focus: str = "auto",
    stack_limit: int = 10,
    proposal_limit: int = 10,
    health_limit: int = 10,
    conflict_limit: int = 10,
    history_limit: int = 10,
) -> dict[str, Any]:
    artifacts = fetch_artifacts(connection, scope=scope)
    all_rules = list_rules(connection, None, scope=scope, rule_type=rule_type)
    stack_rows = list_rules(connection, "adopted", scope=scope, rule_type=rule_type)
    transition_rows = [] if rule_type == "next_kind" else list_observed_transitions(connection, scope=scope)
    proposals = triage_pending_rules(connection, scope=scope, rule_type=rule_type, focus=triage_focus)
    health_items = list_rule_health(connection, scope=scope, status="adopted", rule_type=rule_type)
    conflicts = build_conflict_groups(all_rules)
    history_items = read_rule_history(connection, scope=scope, rule_type=rule_type, limit=history_limit)
    all_history_items = read_rule_history(connection, scope=scope, rule_type=rule_type, limit=None)

    stack = [serialize_rule_row(row) for row in stack_rows[:stack_limit]]
    triage_payload = [serialize_rule_proposal(item) for item in proposals[:proposal_limit]]
    health_payload = [serialize_rule_health(item) for item in health_items]
    health_attention = [item for item in health_payload if item["recommendation"] in {"review", "watch"}][:health_limit]
    history_payload = [serialize_rule_decision(item) for item in history_items]

    status_counts = Counter(str(row["status"]) for row in all_rules)
    triage_counts = Counter(item.recommendation for item in proposals)
    health_counts = Counter(item.recommendation for item in health_items)

    next_actions = _build_next_actions(
        stack=stack,
        proposals=triage_payload,
        health_attention=health_attention,
        conflicts=conflicts,
        pending_rule_count=int(status_counts.get("pending", 0)),
    )

    return {
        "scope": scope,
        "rule_type": rule_type,
        "triage_focus": triage_focus,
        "summary": {
            "artifact_count": len(artifacts),
            "observed_transition_count": len(transition_rows),
            "rule_count": len(all_rules),
            "pending_rule_count": int(status_counts.get("pending", 0)),
            "adopted_rule_count": int(status_counts.get("adopted", 0)),
            "rejected_rule_count": int(status_counts.get("rejected", 0)),
            "conflict_count": len(conflicts),
            "decision_count": len(all_history_items),
            "triage_counts": {
                "adopt": int(triage_counts.get("adopt", 0)),
                "review": int(triage_counts.get("review", 0)),
                "reject": int(triage_counts.get("reject", 0)),
            },
            "health_counts": {
                "untested": int(health_counts.get("untested", 0)),
                "tentative": int(health_counts.get("tentative", 0)),
                "healthy": int(health_counts.get("healthy", 0)),
                "watch": int(health_counts.get("watch", 0)),
                "review": int(health_counts.get("review", 0)),
            },
        },
        "next_actions": next_actions,
        "stack": stack,
        "triage": {
            "focus": triage_focus,
            "proposal_count": len(proposals),
            "rules": triage_payload,
        },
        "health_attention": health_attention,
        "conflicts": conflicts[:conflict_limit],
        "recent_history": history_payload,
    }


def render_scope_report(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        f"report scope={report['scope']} rule_type={report['rule_type'] or 'all'} triage_focus={report['triage_focus']}",
        (
            f"artifacts={summary['artifact_count']} transitions={summary['observed_transition_count']} "
            f"rules={summary['rule_count']} adopted={summary['adopted_rule_count']} "
            f"pending={summary['pending_rule_count']} rejected={summary['rejected_rule_count']}"
        ),
        (
            f"triage adopt={summary['triage_counts']['adopt']} review={summary['triage_counts']['review']} "
            f"reject={summary['triage_counts']['reject']} conflicts={summary['conflict_count']} "
            f"decisions={summary['decision_count']}"
        ),
        (
            f"health healthy={summary['health_counts']['healthy']} tentative={summary['health_counts']['tentative']} "
            f"watch={summary['health_counts']['watch']} review={summary['health_counts']['review']} "
            f"untested={summary['health_counts']['untested']}"
        ),
    ]

    if report["next_actions"]:
        lines.append("next_actions:")
        for action in report["next_actions"]:
            lines.append(f"  [P{action['priority']}] {action['message']}")

    if report["stack"]:
        lines.append("stack:")
        for item in report["stack"]:
            lines.append(
                f"  [{item['id']}] {item['status']} {item['rule_type']} "
                f"{item['prefix_display']!r} -> {item['expected_display']!r} "
                f"support={item['support']}/{item['total']} confidence={item['confidence']:.2f}"
            )

    if report["triage"]["rules"]:
        lines.append("triage:")
        for item in report["triage"]["rules"]:
            lines.append(
                f"  [{item['id']}] recommend={item['recommendation']} {item['rule_type']} "
                f"{item['prefix_display']!r} -> {item['expected_display']!r}"
            )

    if report["health_attention"]:
        lines.append("health_attention:")
        for item in report["health_attention"]:
            lines.append(
                f"  [{item['id']}] recommendation={item['recommendation']} "
                f"{item['prefix_display']!r} -> {item['expected_display']!r} "
                f"violations={item['violation_count']} evals={item['evaluation_count']}"
            )

    if report["conflicts"]:
        lines.append("conflicts:")
        for item in report["conflicts"]:
            lines.append(
                f"  scope={item['scope']} rule_type={item['rule_type']} "
                f"prefix={item['prefix_display']!r} options={item['expected_options']!r}"
            )

    if report["recent_history"]:
        lines.append("recent_history:")
        for item in report["recent_history"]:
            actor_text = "" if item["actor"] is None else f" actor={item['actor']}"
            source_text = "" if item["source"] is None else f" source={item['source']}"
            lines.append(
                f"  {item['created_at']} {item['previous_status']}->{item['new_status']} "
                f"{item['rule_type']} {item['prefix_display']!r} -> {item['expected_display']!r}"
                f"{actor_text}{source_text}"
            )

    return "\n".join(lines)


def _build_next_actions(
    *,
    stack: list[dict[str, Any]],
    proposals: list[dict[str, Any]],
    health_attention: list[dict[str, Any]],
    conflicts: list[dict[str, Any]],
    pending_rule_count: int,
) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []

    review_health = [item for item in health_attention if item["recommendation"] == "review"]
    watch_health = [item for item in health_attention if item["recommendation"] == "watch"]
    adopt_proposals = [item for item in proposals if item["recommendation"] == "adopt"]
    review_proposals = [item for item in proposals if item["recommendation"] == "review"]
    reject_proposals = [item for item in proposals if item["recommendation"] == "reject"]

    if review_health:
        actions.append(
            {
                "kind": "review_active_rules",
                "priority": 0,
                "count": len(review_health),
                "rule_ids": [item["id"] for item in review_health],
                "message": f"Review {len(review_health)} adopted rule(s) that are drifting badly.",
            }
        )

    if not stack and pending_rule_count > 0:
        actions.append(
            {
                "kind": "bootstrap_stack",
                "priority": 0,
                "count": pending_rule_count,
                "rule_ids": [item["id"] for item in adopt_proposals[:5]],
                "message": f"Bootstrap the scope by deciding among {pending_rule_count} pending rule(s).",
            }
        )

    if review_proposals:
        actions.append(
            {
                "kind": "resolve_pending_review",
                "priority": 1,
                "count": len(review_proposals),
                "rule_ids": [item["id"] for item in review_proposals],
                "message": f"Resolve {len(review_proposals)} pending rule(s) that need deliberate review.",
            }
        )

    if adopt_proposals:
        actions.append(
            {
                "kind": "adopt_pending_rules",
                "priority": 1,
                "count": len(adopt_proposals),
                "rule_ids": [item["id"] for item in adopt_proposals],
                "message": f"Consider adopting {len(adopt_proposals)} strong pending rule(s).",
            }
        )

    if conflicts:
        actions.append(
            {
                "kind": "inspect_conflicts",
                "priority": 1,
                "count": len(conflicts),
                "rule_ids": [],
                "message": f"Inspect {len(conflicts)} conflicting prefix group(s).",
            }
        )

    if reject_proposals:
        actions.append(
            {
                "kind": "clear_shadowed_pending_rules",
                "priority": 2,
                "count": len(reject_proposals),
                "rule_ids": [item["id"] for item in reject_proposals],
                "message": f"Reject or revisit {len(reject_proposals)} shadowed pending rule(s).",
            }
        )

    if watch_health:
        actions.append(
            {
                "kind": "monitor_active_rules",
                "priority": 2,
                "count": len(watch_health),
                "rule_ids": [item["id"] for item in watch_health],
                "message": f"Monitor {len(watch_health)} adopted rule(s) showing early drift.",
            }
        )

    return sorted(actions, key=lambda item: (int(item["priority"]), -int(item["count"]), item["kind"]))
