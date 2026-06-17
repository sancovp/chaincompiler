from __future__ import annotations

from sqlite3 import Connection

from .db import list_rule_decisions
from .engine import decode_prefix
from .models import RuleDecision


def read_rule_history(
    connection: Connection,
    *,
    scope: str = "global",
    rule_type: str | None = None,
    new_status: str | None = None,
    limit: int | None = None,
) -> list[RuleDecision]:
    rows = list_rule_decisions(
        connection,
        scope=scope,
        rule_type=rule_type,
        new_status=new_status,
        limit=limit,
    )
    return [summarize_rule_decision(row) for row in rows]


def summarize_rule_decision(row: object) -> RuleDecision:
    return RuleDecision(
        id=int(row["id"]),
        rule_id=None if row["rule_id"] is None else int(row["rule_id"]),
        scope=str(row["scope"]),
        rule_type=str(row["rule_type"]),
        prefix=decode_prefix(str(row["prefix_json"])),
        expected_token=str(row["expected_token"]),
        previous_status=str(row["previous_status"]),
        new_status=str(row["new_status"]),
        automatic=bool(int(row["automatic"])),
        actor=_optional_string(row["actor"]),
        source=_optional_string(row["source"]),
        reason=_optional_string(row["reason"]),
        created_at=str(row["created_at"]),
    )


def _optional_string(value: object) -> str | None:
    return None if value is None else str(value)
