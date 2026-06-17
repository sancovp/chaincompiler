from __future__ import annotations

from collections.abc import Iterable
from sqlite3 import Connection

from .engine import catch_patterns
from .linting import apply_normalization, build_normalization_suggestions, lint_text
from .models import ArtifactInput
from .present import serialize_rule_proposal, serialize_suggestion, serialize_violation
from .triage import apply_triage_recommendations, triage_pending_rules


def process_session_stream(
    connection: Connection,
    lines: Iterable[str],
    *,
    scope: str,
    label: str,
    learn: bool = False,
    triage: bool = False,
    apply_triage: tuple[str, ...] = (),
    triage_focus: str = "auto",
    min_support: int = 2,
    min_confidence: float = 0.75,
    max_prefix: int = 2,
) -> list[dict[str, object]]:
    events: list[dict[str, object]] = []
    buffered_lines: list[str] = []
    violation_count = 0

    for stream_line_no, raw_line in enumerate(lines, start=1):
        text = raw_line if raw_line.endswith("\n") else f"{raw_line}\n"
        line_label = f"{label}:{stream_line_no}"
        violations = lint_text(connection, text, label=line_label, scope=scope)
        suggestions = build_normalization_suggestions(violations)
        normalized_text = apply_normalization(text, suggestions).rstrip("\n")

        violation_count += len(violations)
        buffered_lines.append(text)
        events.append(
            {
                "event": "line",
                "scope": scope,
                "label": label,
                "line_label": line_label,
                "stream_line_no": stream_line_no,
                "input": text.rstrip("\n"),
                "violations": [serialize_violation(violation) for violation in violations],
                "suggestions": [serialize_suggestion(suggestion) for suggestion in suggestions],
                "normalized_text": normalized_text,
                "changed": normalized_text != text.rstrip("\n"),
            }
        )

    candidate_rule_count = 0
    if learn and buffered_lines:
        candidate_rule_count = catch_patterns(
            connection,
            [ArtifactInput(label=label, content="".join(buffered_lines))],
            scope=scope,
            replace_scope=False,
            min_support=min_support,
            min_confidence=min_confidence,
            max_prefix=max_prefix,
        )

    triage_count = 0
    should_triage = triage or bool(apply_triage)
    if should_triage:
        proposals = triage_pending_rules(connection, scope=scope, focus=triage_focus)
        triage_count = len(proposals)
        events.append(
            {
                "event": "triage",
                "scope": scope,
                "label": label,
                "focus": triage_focus,
                "proposal_count": triage_count,
                "rules": [serialize_rule_proposal(proposal) for proposal in proposals],
            }
        )

    applied_triage_counts: dict[str, int] = {}
    for recommendation in apply_triage:
        applied = apply_triage_recommendations(
            connection,
            scope=scope,
            recommendation=recommendation,
            focus=triage_focus,
            actor=label,
            source="session",
            reason_prefix=f"session apply-triage from {label}",
        )
        applied_triage_counts[recommendation] = len(applied)
        events.append(
            {
                "event": "apply_triage",
                "scope": scope,
                "label": label,
                "recommendation": recommendation,
                "focus": triage_focus,
                "applied_count": len(applied),
                "applied_rule_ids": [proposal.rule_id for proposal in applied],
            }
        )

    events.append(
        {
            "event": "summary",
            "scope": scope,
            "label": label,
            "line_count": len(buffered_lines),
            "violation_count": violation_count,
            "learn": learn,
            "candidate_rule_count": candidate_rule_count,
            "triage": triage,
            "triage_count": triage_count,
            "triage_focus": triage_focus,
            "applied_triage_counts": applied_triage_counts,
        }
    )
    return events
