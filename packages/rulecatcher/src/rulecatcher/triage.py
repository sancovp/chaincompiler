from __future__ import annotations

from collections import defaultdict
from sqlite3 import Connection

from .db import list_rules
from .engine import adopt_rules, reject_rules
from .engine import decode_prefix
from .models import RuleProposal
from .tokenize import BOS, EOL


TRIAGE_RECOMMENDATIONS = ("adopt", "review", "reject")
APPLYABLE_TRIAGE_RECOMMENDATIONS = ("adopt", "reject")
TRIAGE_FOCUS_CHOICES = ("auto", "core", "all")

_TRIAGE_ORDER = {
    "review": 0,
    "adopt": 1,
    "reject": 2,
}


def triage_pending_rules(
    connection: Connection,
    *,
    scope: str = "global",
    rule_type: str | None = None,
    recommendation: str | None = None,
    limit: int | None = None,
    frontier_only: bool = True,
    focus: str = "auto",
) -> list[RuleProposal]:
    pending_rows = list_rules(connection, "pending", scope=scope, rule_type=rule_type)
    adopted_rows = list_rules(connection, "adopted", scope=scope, rule_type=rule_type)

    pending_groups = _group_rows_by_prefix(pending_rows)
    adopted_groups = _group_rows_by_prefix(adopted_rows)

    items = [
        summarize_pending_rule(
            row,
            pending_group=pending_groups[_group_key(row)],
            adopted_group=adopted_groups.get(_group_key(row), []),
        )
        for row in pending_rows
    ]
    if frontier_only:
        items = [item for item in items if not _is_shadowed(item, items)]
    items = _apply_focus(items, focus)
    if recommendation is not None:
        items = [item for item in items if item.recommendation == recommendation]
    items = sorted(items, key=_sort_key)
    if limit is not None:
        return items[:limit]
    return items


def apply_triage_recommendations(
    connection: Connection,
    *,
    scope: str = "global",
    recommendation: str = "adopt",
    rule_type: str | None = None,
    limit: int | None = None,
    frontier_only: bool = True,
    focus: str = "auto",
    dry_run: bool = False,
    actor: str | None = None,
    source: str = "triage",
    reason_prefix: str | None = None,
) -> list[RuleProposal]:
    if recommendation not in APPLYABLE_TRIAGE_RECOMMENDATIONS:
        raise ValueError(f"Unsupported triage application recommendation {recommendation!r}")

    proposals = triage_pending_rules(
        connection,
        scope=scope,
        rule_type=rule_type,
        recommendation=recommendation,
        limit=limit,
        frontier_only=frontier_only,
        focus=focus,
    )
    if dry_run:
        return proposals

    effective_source = _effective_source(source, recommendation)
    for proposal in proposals:
        reason = _application_reason(proposal, recommendation, reason_prefix)
        if recommendation == "adopt":
            adopt_rules(
                connection,
                [proposal.rule_id],
                actor=actor,
                source=effective_source,
                reason=reason,
            )
            continue
        reject_rules(
            connection,
            [proposal.rule_id],
            actor=actor,
            source=effective_source,
            reason=reason,
        )
    return proposals


def summarize_pending_rule(
    row: object,
    *,
    pending_group: list[object],
    adopted_group: list[object],
) -> RuleProposal:
    prefix = decode_prefix(str(row["prefix_json"]))
    competing_pending = [item for item in pending_group if int(item["id"]) != int(row["id"])]
    conflicting_adopted = list(adopted_group)
    recommendation, reasons = recommendation_for_pending_rule(
        row,
        competing_pending=competing_pending,
        pending_group=pending_group,
        conflicting_adopted=conflicting_adopted,
    )
    return RuleProposal(
        rule_id=int(row["id"]),
        scope=str(row["scope"]),
        rule_type=str(row["rule_type"]),
        prefix=prefix,
        expected_token=str(row["expected_token"]),
        support=int(row["support"]),
        total=int(row["total"]),
        confidence=float(row["confidence"]),
        competing_pending_rule_ids=tuple(sorted(int(item["id"]) for item in competing_pending)),
        conflicting_adopted_rule_ids=tuple(sorted(int(item["id"]) for item in conflicting_adopted)),
        recommendation=recommendation,
        reasons=tuple(reasons),
    )


def recommendation_for_pending_rule(
    row: object,
    *,
    competing_pending: list[object],
    pending_group: list[object],
    conflicting_adopted: list[object],
) -> tuple[str, list[str]]:
    ordered_pending = sorted(pending_group, key=_row_rank_key)
    rule_id = int(row["id"])
    support = int(row["support"])
    confidence = float(row["confidence"])
    reasons: list[str] = []

    if conflicting_adopted:
        adopted_ids = sorted(int(item["id"]) for item in conflicting_adopted)
        reasons.append(f"conflicts with adopted rule(s) {adopted_ids}")
        if confidence >= 0.9 and support >= 3:
            reasons.append("strong evidence suggests the active language may have shifted")
        else:
            reasons.append("new evidence is not strong enough to replace the active stack automatically")
        return "review", reasons

    if competing_pending:
        leader = ordered_pending[0]
        leader_id = int(leader["id"])
        competing_ids = sorted(int(item["id"]) for item in competing_pending)
        if leader_id == rule_id:
            reasons.append(f"competes with pending rule(s) {competing_ids}")
            if _leader_dominates_group(ordered_pending):
                reasons.append("strongest pending option for this prefix")
            else:
                reasons.append("needs a deliberate choice among competing pending rules")
            return "review", reasons
        reasons.append(f"competes with pending rule(s) {[leader_id, *competing_ids]}")
        if _leader_dominates_group(ordered_pending):
            reasons.append(f"weaker than pending rule {leader_id} for the same prefix")
            return "reject", reasons
        reasons.append("competition is unresolved and still needs review")
        return "review", reasons

    if confidence >= 0.9 and support >= 3:
        reasons.append("high confidence and support with no known conflicts")
        return "adopt", reasons

    reasons.append("clean candidate, but evidence is not yet overwhelming")
    return "review", reasons


def _group_rows_by_prefix(rows: list[object]) -> dict[tuple[str, str, str], list[object]]:
    grouped: dict[tuple[str, str, str], list[object]] = defaultdict(list)
    for row in rows:
        grouped[_group_key(row)].append(row)
    return grouped


def _group_key(row: object) -> tuple[str, str, str]:
    return (str(row["scope"]), str(row["rule_type"]), str(row["prefix_json"]))


def _leader_dominates_group(rows: list[object]) -> bool:
    if len(rows) <= 1:
        return True
    leader = rows[0]
    challenger = rows[1]
    leader_confidence = float(leader["confidence"])
    challenger_confidence = float(challenger["confidence"])
    leader_support = int(leader["support"])
    challenger_support = int(challenger["support"])
    return (
        leader_confidence >= challenger_confidence + 0.15
        or leader_support >= challenger_support + 2
    )


def _sort_key(item: RuleProposal) -> tuple[object, ...]:
    return (
        _TRIAGE_ORDER.get(item.recommendation, len(_TRIAGE_ORDER)),
        -item.confidence,
        -item.support,
        -len(item.prefix),
        item.rule_id,
    )


def _is_shadowed(item: RuleProposal, items: list[RuleProposal]) -> bool:
    for other in items:
        if other.rule_id == item.rule_id:
            continue
        if other.scope != item.scope or other.rule_type != item.rule_type:
            continue
        if other.expected_token != item.expected_token:
            continue
        if other.support != item.support or other.total != item.total:
            continue
        if len(other.prefix) <= len(item.prefix):
            continue
        if other.prefix[-len(item.prefix) :] != item.prefix:
            continue
        return True
    return False


def _row_rank_key(row: object) -> tuple[object, ...]:
    prefix = decode_prefix(str(row["prefix_json"]))
    return (
        -float(row["confidence"]),
        -int(row["support"]),
        -len(prefix),
        int(row["id"]),
    )


def _apply_focus(items: list[RuleProposal], focus: str) -> list[RuleProposal]:
    if focus == "all":
        return items
    core_items = [item for item in items if _is_core_proposal(item)]
    if focus == "core":
        return core_items
    if focus == "auto":
        return core_items if core_items else items
    raise ValueError(f"Unsupported triage focus {focus!r}")


def _is_core_proposal(item: RuleProposal) -> bool:
    # A rule is boundary boilerplate only if it PREDICTS a boundary (line-ender)
    # or carries no real context at all. A leading <BOS> is positional anchoring —
    # the line-opener grammar — and for line-oriented notations that is the most
    # load-bearing rule, not boilerplate. So keep any rule that predicts a real
    # token and has at least one non-boundary token in its prefix.
    boundary_tokens = {BOS, EOL}
    if item.expected_token in boundary_tokens:
        return False
    return any(token not in boundary_tokens for token in item.prefix)


def _application_reason(
    proposal: RuleProposal,
    recommendation: str,
    reason_prefix: str | None,
) -> str:
    detail = "; ".join(proposal.reasons) if proposal.reasons else "no additional triage detail"
    reason = f"triage recommend {recommendation}: {detail}"
    if reason_prefix is None:
        return reason
    return f"{reason_prefix}; {reason}"


def _effective_source(source: str, recommendation: str) -> str:
    return f"{source}:{recommendation}"
