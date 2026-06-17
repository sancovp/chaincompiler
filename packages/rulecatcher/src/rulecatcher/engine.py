from __future__ import annotations

import json
from pathlib import Path
from sqlite3 import Connection

from .db import (
    bind_scope_artifacts,
    clear_scope,
    fetch_artifacts,
    get_scope_keywords,
    ingest_artifact,
    ingest_artifact_content,
    replace_observed_transitions,
    set_rule_status,
    set_scope_keywords,
    upsert_candidate_rule,
)
from .detect import collect_next_kind_rules, collect_next_token_rules, collect_observed_transitions
from .models import ArtifactInput


def catch_patterns(
    connection: Connection,
    paths: list[Path | ArtifactInput],
    *,
    scope: str = "global",
    replace_scope: bool = False,
    min_support: int = 2,
    min_confidence: float = 0.75,
    max_prefix: int = 2,
    keywords: list[str] | None = None,
) -> int:
    if replace_scope:
        clear_scope(connection, scope)

    # Keywords are a catch-time tokenization decision. If provided, persist them
    # for this scope so lint/normalize reconstruct the same token classes later.
    # If omitted, reuse whatever the scope was last caught with.
    if keywords:
        set_scope_keywords(connection, scope, keywords)
    effective_keywords = get_scope_keywords(connection, scope)

    artifact_ids: list[int] = []
    for path in paths:
        if isinstance(path, ArtifactInput):
            artifact_ids.append(ingest_artifact_content(connection, path.label, path.content))
        else:
            artifact_ids.append(ingest_artifact(connection, path.resolve()))

    bind_scope_artifacts(connection, scope, artifact_ids)

    artifacts = fetch_artifacts(connection, scope=scope)
    transitions = collect_observed_transitions(artifacts, max_prefix=max_prefix)
    replace_observed_transitions(
        connection,
        scope,
        [
            (
                json.dumps(transition.prefix, ensure_ascii=True),
                transition.next_token,
                transition.support,
                transition.total,
                transition.confidence,
            )
            for transition in transitions
        ],
    )
    candidates = collect_next_token_rules(
        artifacts,
        scope=scope,
        min_support=min_support,
        min_confidence=min_confidence,
        max_prefix=max_prefix,
    )
    kind_candidates = collect_next_kind_rules(
        artifacts,
        scope=scope,
        min_support=min_support,
        min_confidence=min_confidence,
        max_prefix=max_prefix,
        keywords=effective_keywords,
    )
    all_candidates = [*candidates, *kind_candidates]
    for candidate in all_candidates:
        upsert_candidate_rule(connection, candidate)
    return len(all_candidates)


def adopt_rules(
    connection: Connection,
    rule_ids: list[int],
    *,
    actor: str | None = None,
    source: str | None = None,
    reason: str | None = None,
) -> None:
    for rule_id in rule_ids:
        set_rule_status(connection, rule_id, "adopted", actor=actor, source=source, reason=reason)


def reject_rules(
    connection: Connection,
    rule_ids: list[int],
    *,
    actor: str | None = None,
    source: str | None = None,
    reason: str | None = None,
) -> None:
    for rule_id in rule_ids:
        set_rule_status(connection, rule_id, "rejected", actor=actor, source=source, reason=reason)


def decode_prefix(prefix_json: str) -> tuple[str, ...]:
    return tuple(json.loads(prefix_json))
