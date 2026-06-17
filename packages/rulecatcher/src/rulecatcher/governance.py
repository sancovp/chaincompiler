from __future__ import annotations

from sqlite3 import Connection

from .db import list_rules_with_stats
from .engine import decode_prefix
from .models import RuleHealth


RECOMMENDATION_CHOICES = ("untested", "tentative", "healthy", "watch", "review")

_RECOMMENDATION_ORDER = {
    "review": 0,
    "watch": 1,
    "tentative": 2,
    "untested": 3,
    "healthy": 4,
}


def list_rule_health(
    connection: Connection,
    *,
    scope: str = "global",
    status: str | None = "adopted",
    rule_type: str | None = None,
    recommendation: str | None = None,
) -> list[RuleHealth]:
    rows = list_rules_with_stats(connection, scope=scope, status=status, rule_type=rule_type)
    items = [summarize_rule_health(row) for row in rows]
    if recommendation is not None:
        items = [item for item in items if item.recommendation == recommendation]
    return sorted(items, key=_sort_key)


def summarize_rule_health(row: object) -> RuleHealth:
    prefix = decode_prefix(str(row["prefix_json"]))
    hit_count = int(row["hit_count"])
    violation_count = int(row["violation_count"])
    evaluation_count = hit_count + violation_count
    violation_rate = 0.0 if evaluation_count == 0 else violation_count / evaluation_count
    return RuleHealth(
        rule_id=int(row["id"]),
        scope=str(row["scope"]),
        rule_type=str(row["rule_type"]),
        status=str(row["status"]),
        prefix=prefix,
        expected_token=str(row["expected_token"]),
        support=int(row["support"]),
        total=int(row["total"]),
        confidence=float(row["confidence"]),
        hit_count=hit_count,
        violation_count=violation_count,
        evaluation_count=evaluation_count,
        violation_rate=violation_rate,
        last_hit_at=_optional_string(row["last_hit_at"]),
        last_violation_at=_optional_string(row["last_violation_at"]),
        recommendation=recommendation_for_counts(
            hit_count=hit_count,
            violation_count=violation_count,
            evaluation_count=evaluation_count,
            violation_rate=violation_rate,
        ),
    )


def recommendation_for_counts(
    *,
    hit_count: int,
    violation_count: int,
    evaluation_count: int,
    violation_rate: float,
) -> str:
    if evaluation_count == 0:
        return "untested"
    if violation_count == 0:
        return "healthy" if hit_count >= 3 else "tentative"
    if violation_count >= 2 and violation_rate >= 0.5:
        return "review"
    return "watch"


def _sort_key(item: RuleHealth) -> tuple[object, ...]:
    return (
        _RECOMMENDATION_ORDER.get(item.recommendation, len(_RECOMMENDATION_ORDER)),
        -item.violation_rate,
        -item.violation_count,
        -item.evaluation_count,
        item.rule_id,
    )


def _optional_string(value: object) -> str | None:
    return None if value is None else str(value)
