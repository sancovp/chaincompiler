from __future__ import annotations

import json
from sqlite3 import Connection
from typing import Any

from .db import (
    bind_scope_artifacts,
    clear_scope,
    delete_scope_decisions,
    fetch_artifacts,
    fetch_evidence,
    ingest_artifact_content,
    insert_rule_decision_record,
    list_raw_observed_transitions,
    list_rule_decisions,
    list_rules,
    list_rules_with_stats,
    replace_observed_transitions,
    upsert_rule_stats,
    upsert_candidate_rule,
)
from .engine import decode_prefix
from .models import CandidateRule, RuleEvidence


SNAPSHOT_FORMAT = "rulecatcher-scope-v1"


def export_scope_snapshot(connection: Connection, *, scope: str) -> dict[str, Any]:
    artifacts = fetch_artifacts(connection, scope=scope)
    artifact_payload = [
        {
            "path": artifact.path,
            "sha256": artifact.sha256,
            "content": artifact.content,
        }
        for artifact in artifacts
    ]

    rules = []
    for row in list_rules_with_stats(connection, scope=scope):
        evidence_rows = fetch_evidence(connection, int(row["id"]))
        rules.append(
            {
                "rule_type": str(row["rule_type"]),
                "prefix": list(decode_prefix(str(row["prefix_json"]))),
                "expected_token": str(row["expected_token"]),
                "support": int(row["support"]),
                "total": int(row["total"]),
                "confidence": float(row["confidence"]),
                "status": str(row["status"]),
                "stats": {
                    "hit_count": int(row["hit_count"]),
                    "violation_count": int(row["violation_count"]),
                    "last_hit_at": None if row["last_hit_at"] is None else str(row["last_hit_at"]),
                    "last_violation_at": None if row["last_violation_at"] is None else str(row["last_violation_at"]),
                },
                "evidence": [
                    {
                        "artifact_path": str(evidence["path"]),
                        "artifact_sha256": str(evidence["sha256"]),
                        "line_no": int(evidence["line_no"]),
                        "observed_token": str(evidence["observed_token"]),
                        "context": str(evidence["context"]),
                    }
                    for evidence in evidence_rows
                ],
            }
        )

    decisions = []
    for row in reversed(list_rule_decisions(connection, scope=scope)):
        decisions.append(
            {
                "rule_type": str(row["rule_type"]),
                "prefix": list(decode_prefix(str(row["prefix_json"]))),
                "expected_token": str(row["expected_token"]),
                "previous_status": str(row["previous_status"]),
                "new_status": str(row["new_status"]),
                "automatic": bool(int(row["automatic"])),
                "actor": None if row["actor"] is None else str(row["actor"]),
                "source": None if row["source"] is None else str(row["source"]),
                "reason": None if row["reason"] is None else str(row["reason"]),
                "created_at": str(row["created_at"]),
            }
        )

    transitions = [
        {
            "prefix": list(decode_prefix(str(row["prefix_json"]))),
            "next_token": str(row["next_token"]),
            "support": int(row["support"]),
            "total": int(row["total"]),
            "confidence": float(row["confidence"]),
        }
        for row in list_raw_observed_transitions(connection, scope=scope)
    ]

    return {
        "format": SNAPSHOT_FORMAT,
        "scope": scope,
        "artifacts": artifact_payload,
        "observed_transitions": transitions,
        "rules": rules,
        "decisions": decisions,
    }


def import_scope_snapshot(
    connection: Connection,
    snapshot: dict[str, Any],
    *,
    target_scope: str,
    replace_scope_state: bool = False,
) -> dict[str, Any]:
    snapshot_scope = str(snapshot.get("scope", "global"))
    if str(snapshot.get("format")) != SNAPSHOT_FORMAT:
        raise ValueError(f"Unsupported snapshot format {snapshot.get('format')!r}")

    if replace_scope_state:
        clear_scope(connection, target_scope)
        delete_scope_decisions(connection, target_scope)

    artifact_key_to_id: dict[tuple[str, str], int] = {}
    artifact_ids: list[int] = []
    for artifact in snapshot.get("artifacts", []):
        path = str(artifact["path"])
        content = str(artifact["content"])
        sha256 = str(artifact["sha256"])
        artifact_id = ingest_artifact_content(connection, path, content)
        artifact_key_to_id[(path, sha256)] = artifact_id
        artifact_ids.append(artifact_id)
    bind_scope_artifacts(connection, target_scope, artifact_ids)

    transitions = [
        (
            json.dumps(tuple(item["prefix"]), ensure_ascii=True),
            str(item["next_token"]),
            int(item["support"]),
            int(item["total"]),
            float(item["confidence"]),
        )
        for item in snapshot.get("observed_transitions", [])
    ]
    replace_observed_transitions(connection, target_scope, transitions)

    rule_key_to_id: dict[tuple[str, tuple[str, ...], str], int] = {}
    for item in snapshot.get("rules", []):
        prefix = tuple(str(token) for token in item["prefix"])
        evidences = []
        for evidence in item.get("evidence", []):
            artifact_key = (str(evidence["artifact_path"]), str(evidence["artifact_sha256"]))
            artifact_id = artifact_key_to_id.get(artifact_key)
            if artifact_id is None:
                continue
            evidences.append(
                RuleEvidence(
                    artifact_id=artifact_id,
                    artifact_path=str(evidence["artifact_path"]),
                    line_no=int(evidence["line_no"]),
                    observed_token=str(evidence["observed_token"]),
                    context=str(evidence["context"]),
                )
            )
        rule = CandidateRule(
            rule_type=str(item["rule_type"]),
            prefix=prefix,
            expected_token=str(item["expected_token"]),
            support=int(item["support"]),
            total=int(item["total"]),
            confidence=float(item["confidence"]),
            evidences=tuple(evidences),
            status=str(item["status"]),
            scope=target_scope,
        )
        rule_id = upsert_candidate_rule(connection, rule)
        stats = item.get("stats")
        if isinstance(stats, dict):
            upsert_rule_stats(
                connection,
                rule_id=rule_id,
                hit_count=int(stats.get("hit_count", 0)),
                violation_count=int(stats.get("violation_count", 0)),
                last_hit_at=None if stats.get("last_hit_at") is None else str(stats["last_hit_at"]),
                last_violation_at=None if stats.get("last_violation_at") is None else str(stats["last_violation_at"]),
            )
        rule_key_to_id[(str(item["rule_type"]), prefix, str(item["expected_token"]))] = rule_id

    for item in snapshot.get("decisions", []):
        prefix = tuple(str(token) for token in item["prefix"])
        rule_key = (str(item["rule_type"]), prefix, str(item["expected_token"]))
        rule_id = rule_key_to_id.get(rule_key)
        insert_rule_decision_record(
            connection,
            rule_id=rule_id,
            scope=target_scope,
            rule_type=str(item["rule_type"]),
            prefix_json=json.dumps(prefix, ensure_ascii=True),
            expected_token=str(item["expected_token"]),
            previous_status=str(item["previous_status"]),
            new_status=str(item["new_status"]),
            automatic=bool(item["automatic"]),
            actor=None if item.get("actor") is None else str(item["actor"]),
            source=None if item.get("source") is None else str(item["source"]),
            reason=None if item.get("reason") is None else str(item["reason"]),
            created_at=str(item["created_at"]),
        )

    return {
        "source_scope": snapshot_scope,
        "target_scope": target_scope,
        "artifact_count": len(snapshot.get("artifacts", [])),
        "transition_count": len(snapshot.get("observed_transitions", [])),
        "rule_count": len(snapshot.get("rules", [])),
        "decision_count": len(snapshot.get("decisions", [])),
        "replace_scope": replace_scope_state,
    }
