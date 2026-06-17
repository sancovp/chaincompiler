from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any

from .models import RuleDecision, RuleHealth, RuleProposal


def display_prefix(rule_type: str, prefix: tuple[str, ...]) -> list[str]:
    return [display_token(rule_type, token) for token in prefix]


def display_token(rule_type: str, token: str) -> str:
    if rule_type == "next_kind" and token not in {"<BOS>", "<EOL>"}:
        return f"<{token}>"
    return token


def serialize_rule_row(row: object) -> dict[str, Any]:
    rule_type = str(row["rule_type"])
    prefix = tuple(_coerce_prefix(row["prefix_json"]))
    expected = str(row["expected_token"])
    display_pre = display_prefix(rule_type, prefix)
    display_exp = display_token(rule_type, expected)
    # `prefix` / `expected_token` are the CONSISTENT presentation form (matches the
    # human `review` output: next_kind classes are bracketed like <IDENTIFIER>, the
    # same as <BOS>/<EOL>). The raw storage form (bare classes, for signature
    # matching and round-trip) is exposed explicitly as `*_signature`.
    return {
        "id": int(row["id"]),
        "scope": str(row["scope"]),
        "status": str(row["status"]),
        "rule_type": rule_type,
        "prefix": list(display_pre),
        "prefix_display": list(display_pre),
        "prefix_signature": list(prefix),
        "expected_token": display_exp,
        "expected_display": display_exp,
        "expected_signature": expected,
        "support": int(row["support"]),
        "total": int(row["total"]),
        "confidence": float(row["confidence"]),
    }


def serialize_evidence_row(row: object) -> dict[str, Any]:
    return {
        "path": str(row["path"]),
        "line_no": int(row["line_no"]),
        "observed_token": str(row["observed_token"]),
        "context": str(row["context"]),
    }


def serialize_violation(violation: object) -> dict[str, Any]:
    payload = _dataclass_dict(violation)
    payload["prefix_display"] = display_prefix(payload["rule_type"], tuple(payload["prefix"]))
    payload["expected_display"] = display_token(payload["rule_type"], payload["expected_token"])
    return payload


def serialize_suggestion(suggestion: object) -> dict[str, Any]:
    return _dataclass_dict(suggestion)


def serialize_observed_transition_row(row: object) -> dict[str, Any]:
    prefix = tuple(_coerce_prefix(row["prefix_json"]))
    status = str(row["rule_status"]) if row["rule_status"] is not None else "observed"
    return {
        "prefix": list(prefix),
        "prefix_display": list(prefix),
        "next_token": str(row["next_token"]),
        "next_display": str(row["next_token"]),
        "support": int(row["support"]),
        "total": int(row["total"]),
        "confidence": float(row["confidence"]),
        "rule_id": None if row["rule_id"] is None else int(row["rule_id"]),
        "rule_status": status,
    }


def serialize_rule_health(health: RuleHealth) -> dict[str, Any]:
    return {
        "id": health.rule_id,
        "rule_id": health.rule_id,
        "scope": health.scope,
        "status": health.status,
        "rule_type": health.rule_type,
        "prefix": list(health.prefix),
        "prefix_display": display_prefix(health.rule_type, health.prefix),
        "expected_token": health.expected_token,
        "expected_display": display_token(health.rule_type, health.expected_token),
        "support": health.support,
        "total": health.total,
        "confidence": health.confidence,
        "hit_count": health.hit_count,
        "violation_count": health.violation_count,
        "evaluation_count": health.evaluation_count,
        "violation_rate": health.violation_rate,
        "last_hit_at": health.last_hit_at,
        "last_violation_at": health.last_violation_at,
        "recommendation": health.recommendation,
    }


def serialize_rule_proposal(proposal: RuleProposal) -> dict[str, Any]:
    return {
        "id": proposal.rule_id,
        "rule_id": proposal.rule_id,
        "scope": proposal.scope,
        "rule_type": proposal.rule_type,
        "prefix": list(proposal.prefix),
        "prefix_display": display_prefix(proposal.rule_type, proposal.prefix),
        "expected_token": proposal.expected_token,
        "expected_display": display_token(proposal.rule_type, proposal.expected_token),
        "support": proposal.support,
        "total": proposal.total,
        "confidence": proposal.confidence,
        "competing_pending_rule_ids": list(proposal.competing_pending_rule_ids),
        "conflicting_adopted_rule_ids": list(proposal.conflicting_adopted_rule_ids),
        "recommendation": proposal.recommendation,
        "reasons": list(proposal.reasons),
    }


def serialize_rule_decision(decision: RuleDecision) -> dict[str, Any]:
    return {
        "id": decision.id,
        "rule_id": decision.rule_id,
        "scope": decision.scope,
        "rule_type": decision.rule_type,
        "prefix": list(decision.prefix),
        "prefix_display": display_prefix(decision.rule_type, decision.prefix),
        "expected_token": decision.expected_token,
        "expected_display": display_token(decision.rule_type, decision.expected_token),
        "previous_status": decision.previous_status,
        "new_status": decision.new_status,
        "automatic": decision.automatic,
        "actor": decision.actor,
        "source": decision.source,
        "reason": decision.reason,
        "created_at": decision.created_at,
    }


def build_conflict_groups(rule_rows: list[object]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, tuple[str, ...], str], list[object]] = {}
    for row in rule_rows:
        rule_type = str(row["rule_type"])
        prefix = tuple(_coerce_prefix(row["prefix_json"]))
        scope = str(row["scope"])
        groups.setdefault((rule_type, prefix, scope), []).append(row)

    conflicts: list[dict[str, Any]] = []
    for (rule_type, prefix, scope), members in groups.items():
        expected_tokens = {str(member["expected_token"]) for member in members}
        if len(expected_tokens) <= 1:
            continue
        serialized_members = [serialize_rule_row(member) for member in sorted(members, key=lambda item: (-float(item["confidence"]), -int(item["support"]), int(item["id"])))]
        conflicts.append(
            {
                "scope": scope,
                "rule_type": rule_type,
                "prefix": list(prefix),
                "prefix_display": display_prefix(rule_type, prefix),
                "expected_options": sorted(display_token(rule_type, token) for token in expected_tokens),
                "members": serialized_members,
            }
        )

    return sorted(conflicts, key=lambda item: (item["scope"], item["rule_type"], item["prefix"]))


def _coerce_prefix(prefix_json: object) -> list[str]:
    import json

    if isinstance(prefix_json, str):
        return list(json.loads(prefix_json))
    raise TypeError(f"Unsupported prefix value {prefix_json!r}")


def _dataclass_dict(value: object) -> dict[str, Any]:
    if not is_dataclass(value):
        raise TypeError(f"Expected dataclass instance, got {type(value)!r}")
    return asdict(value)
