from __future__ import annotations

from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import sqlite3
from typing import Iterator

from .models import ArtifactRecord, CandidateRule


SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS artifacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    path TEXT NOT NULL,
    sha256 TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(path, sha256)
);

CREATE TABLE IF NOT EXISTS artifact_scope_bindings (
    scope TEXT NOT NULL,
    artifact_id INTEGER NOT NULL REFERENCES artifacts(id) ON DELETE CASCADE,
    PRIMARY KEY(scope, artifact_id)
);

CREATE TABLE IF NOT EXISTS candidate_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rule_type TEXT NOT NULL,
    prefix_json TEXT NOT NULL,
    expected_token TEXT NOT NULL,
    support INTEGER NOT NULL,
    total INTEGER NOT NULL,
    confidence REAL NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    scope TEXT NOT NULL DEFAULT 'global',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(rule_type, prefix_json, expected_token, scope)
);

CREATE TABLE IF NOT EXISTS rule_evidence (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rule_id INTEGER NOT NULL REFERENCES candidate_rules(id) ON DELETE CASCADE,
    artifact_id INTEGER NOT NULL REFERENCES artifacts(id) ON DELETE CASCADE,
    line_no INTEGER NOT NULL,
    observed_token TEXT NOT NULL,
    context TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS observed_transitions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scope TEXT NOT NULL DEFAULT 'global',
    prefix_json TEXT NOT NULL,
    next_token TEXT NOT NULL,
    support INTEGER NOT NULL,
    total INTEGER NOT NULL,
    confidence REAL NOT NULL,
    UNIQUE(scope, prefix_json, next_token)
);

CREATE TABLE IF NOT EXISTS rule_stats (
    rule_id INTEGER PRIMARY KEY REFERENCES candidate_rules(id) ON DELETE CASCADE,
    hit_count INTEGER NOT NULL DEFAULT 0,
    violation_count INTEGER NOT NULL DEFAULT 0,
    last_hit_at TEXT,
    last_violation_at TEXT
);

CREATE TABLE IF NOT EXISTS rule_decisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rule_id INTEGER,
    scope TEXT NOT NULL,
    rule_type TEXT NOT NULL,
    prefix_json TEXT NOT NULL,
    expected_token TEXT NOT NULL,
    previous_status TEXT NOT NULL,
    new_status TEXT NOT NULL,
    automatic INTEGER NOT NULL DEFAULT 0,
    actor TEXT,
    source TEXT,
    reason TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS scope_config (
    scope TEXT PRIMARY KEY,
    keywords_json TEXT NOT NULL DEFAULT '[]'
);
"""


@contextmanager
def connect(db_path: Path | str) -> Iterator[sqlite3.Connection]:
    connection = sqlite3.connect(str(db_path))
    connection.row_factory = sqlite3.Row
    try:
        initialize(connection)
        yield connection
        connection.commit()
    finally:
        connection.close()


def initialize(connection: sqlite3.Connection) -> None:
    connection.executescript(SCHEMA)
    _ensure_column(connection, "observed_transitions", "scope", "TEXT NOT NULL DEFAULT 'global'")


def ingest_artifact(connection: sqlite3.Connection, path: Path) -> int:
    content = path.read_text(encoding="utf-8")
    return ingest_artifact_content(connection, str(path), content)


def ingest_artifact_content(connection: sqlite3.Connection, label: str, content: str) -> int:
    sha256 = hashlib.sha256(content.encode("utf-8")).hexdigest()
    row = connection.execute(
        """
        INSERT INTO artifacts(path, sha256, content)
        VALUES (?, ?, ?)
        ON CONFLICT(path, sha256) DO UPDATE SET content=excluded.content
        RETURNING id
        """,
        (label, sha256, content),
    ).fetchone()
    assert row is not None
    return int(row["id"])


def bind_scope_artifacts(connection: sqlite3.Connection, scope: str, artifact_ids: list[int]) -> None:
    connection.executemany(
        "INSERT OR IGNORE INTO artifact_scope_bindings(scope, artifact_id) VALUES (?, ?)",
        [(scope, artifact_id) for artifact_id in artifact_ids],
    )


def fetch_artifacts(connection: sqlite3.Connection, scope: str = "global") -> list[ArtifactRecord]:
    rows = connection.execute(
        """
        SELECT a.id, a.path, a.content, a.sha256
        FROM artifacts AS a
        JOIN artifact_scope_bindings AS b ON b.artifact_id = a.id
        WHERE b.scope = ?
        ORDER BY a.id
        """,
        (scope,),
    ).fetchall()
    return [
        ArtifactRecord(id=int(row["id"]), path=str(row["path"]), content=str(row["content"]), sha256=str(row["sha256"]))
        for row in rows
    ]


def upsert_candidate_rule(connection: sqlite3.Connection, rule: CandidateRule) -> int:
    prefix_json = json.dumps(rule.prefix, ensure_ascii=True)
    row = connection.execute(
        """
        INSERT INTO candidate_rules(
            rule_type,
            prefix_json,
            expected_token,
            support,
            total,
            confidence,
            status,
            scope
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(rule_type, prefix_json, expected_token, scope)
        DO UPDATE SET
            support=excluded.support,
            total=excluded.total,
            confidence=excluded.confidence,
            updated_at=CURRENT_TIMESTAMP
        RETURNING id
        """,
        (
            rule.rule_type,
            prefix_json,
            rule.expected_token,
            rule.support,
            rule.total,
            rule.confidence,
            rule.status,
            rule.scope,
        ),
    ).fetchone()
    assert row is not None
    rule_id = int(row["id"])
    connection.execute("DELETE FROM rule_evidence WHERE rule_id = ?", (rule_id,))
    for evidence in rule.evidences:
        connection.execute(
            """
            INSERT INTO rule_evidence(rule_id, artifact_id, line_no, observed_token, context)
            VALUES (?, ?, ?, ?, ?)
            """,
            (rule_id, evidence.artifact_id, evidence.line_no, evidence.observed_token, evidence.context),
        )
    return rule_id


def list_rules(
    connection: sqlite3.Connection,
    status: str | None = None,
    scope: str = "global",
    rule_type: str | None = None,
) -> list[sqlite3.Row]:
    conditions = ["scope = ?"]
    params: list[object] = [scope]
    if status is not None:
        conditions.append("status = ?")
        params.append(status)
    if rule_type is not None:
        conditions.append("rule_type = ?")
        params.append(rule_type)
    where_clause = " AND ".join(conditions)
    return connection.execute(
        f"SELECT * FROM candidate_rules WHERE {where_clause} ORDER BY status, confidence DESC, support DESC, id ASC",
        tuple(params),
    ).fetchall()


def fetch_rule(connection: sqlite3.Connection, rule_id: int) -> sqlite3.Row | None:
    return connection.execute("SELECT * FROM candidate_rules WHERE id = ?", (rule_id,)).fetchone()


def fetch_rule_with_stats(connection: sqlite3.Connection, rule_id: int) -> sqlite3.Row | None:
    return connection.execute(
        """
        SELECT
            cr.*,
            COALESCE(rs.hit_count, 0) AS hit_count,
            COALESCE(rs.violation_count, 0) AS violation_count,
            rs.last_hit_at AS last_hit_at,
            rs.last_violation_at AS last_violation_at
        FROM candidate_rules AS cr
        LEFT JOIN rule_stats AS rs ON rs.rule_id = cr.id
        WHERE cr.id = ?
        """,
        (rule_id,),
    ).fetchone()


def find_rule_by_signature(
    connection: sqlite3.Connection,
    *,
    scope: str,
    rule_type: str,
    prefix_json: str,
    expected_token: str,
) -> sqlite3.Row | None:
    return connection.execute(
        """
        SELECT * 
        FROM candidate_rules
        WHERE scope = ? AND rule_type = ? AND prefix_json = ? AND expected_token = ?
        LIMIT 1
        """,
        (scope, rule_type, prefix_json, expected_token),
    ).fetchone()


def set_rule_status(
    connection: sqlite3.Connection,
    rule_id: int,
    status: str,
    *,
    actor: str | None = None,
    source: str | None = None,
    reason: str | None = None,
) -> None:
    row = fetch_rule(connection, rule_id)
    if row is None:
        raise ValueError(f"Unknown rule id {rule_id}")
    previous_status = str(row["status"])
    if previous_status == status:
        return
    if status == "adopted":
        displaced_rows = connection.execute(
            """
            SELECT *
            FROM candidate_rules
            WHERE rule_type = ? AND prefix_json = ? AND scope = ? AND id != ? AND status = 'adopted'
            ORDER BY id
            """,
            (row["rule_type"], row["prefix_json"], row["scope"], rule_id),
        ).fetchall()
        connection.execute(
            """
            UPDATE candidate_rules
            SET status = 'rejected', updated_at = CURRENT_TIMESTAMP
            WHERE rule_type = ? AND prefix_json = ? AND scope = ? AND id != ? AND status = 'adopted'
            """,
            (row["rule_type"], row["prefix_json"], row["scope"], rule_id),
        )
        for displaced_row in displaced_rows:
            _record_rule_decision(
                connection,
                displaced_row,
                previous_status="adopted",
                new_status="rejected",
                automatic=True,
                actor=actor,
                source=None if source is None else f"{source}:auto-displace",
                reason=f"superseded by adopted rule {rule_id}",
            )
    connection.execute(
        "UPDATE candidate_rules SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (status, rule_id),
    )
    _record_rule_decision(
        connection,
        row,
        previous_status=previous_status,
        new_status=status,
        automatic=False,
        actor=actor,
        source=source,
        reason=reason,
    )


def fetch_evidence(connection: sqlite3.Connection, rule_id: int) -> list[sqlite3.Row]:
    return connection.execute(
        """
        SELECT re.line_no, re.observed_token, re.context, a.id AS artifact_id, a.path, a.sha256
        FROM rule_evidence AS re
        JOIN artifacts AS a ON a.id = re.artifact_id
        WHERE re.rule_id = ?
        ORDER BY re.id
        """,
        (rule_id,),
    ).fetchall()


def record_rule_evaluations(connection: sqlite3.Connection, hit_rule_ids: list[int], violation_rule_ids: list[int]) -> None:
    for rule_id in hit_rule_ids:
        connection.execute(
            """
            INSERT INTO rule_stats(rule_id, hit_count, violation_count, last_hit_at)
            VALUES (?, 1, 0, CURRENT_TIMESTAMP)
            ON CONFLICT(rule_id) DO UPDATE SET
                hit_count = rule_stats.hit_count + 1,
                last_hit_at = CURRENT_TIMESTAMP
            """,
            (rule_id,),
        )
    for rule_id in violation_rule_ids:
        connection.execute(
            """
            INSERT INTO rule_stats(rule_id, hit_count, violation_count, last_violation_at)
            VALUES (?, 0, 1, CURRENT_TIMESTAMP)
            ON CONFLICT(rule_id) DO UPDATE SET
                violation_count = rule_stats.violation_count + 1,
                last_violation_at = CURRENT_TIMESTAMP
            """,
            (rule_id,),
        )


def list_rules_with_stats(
    connection: sqlite3.Connection,
    *,
    scope: str = "global",
    status: str | None = None,
    rule_type: str | None = None,
) -> list[sqlite3.Row]:
    conditions = ["cr.scope = ?"]
    params: list[object] = [scope]
    if status is not None:
        conditions.append("cr.status = ?")
        params.append(status)
    if rule_type is not None:
        conditions.append("cr.rule_type = ?")
        params.append(rule_type)
    where_clause = " AND ".join(conditions)
    return connection.execute(
        f"""
        SELECT
            cr.*,
            COALESCE(rs.hit_count, 0) AS hit_count,
            COALESCE(rs.violation_count, 0) AS violation_count,
            rs.last_hit_at AS last_hit_at,
            rs.last_violation_at AS last_violation_at
        FROM candidate_rules AS cr
        LEFT JOIN rule_stats AS rs ON rs.rule_id = cr.id
        WHERE {where_clause}
        ORDER BY cr.status, cr.confidence DESC, cr.support DESC, cr.id ASC
        """,
        tuple(params),
    ).fetchall()


def list_rule_decisions(
    connection: sqlite3.Connection,
    *,
    scope: str = "global",
    rule_type: str | None = None,
    new_status: str | None = None,
    limit: int | None = None,
) -> list[sqlite3.Row]:
    conditions = ["scope = ?"]
    params: list[object] = [scope]
    if rule_type is not None:
        conditions.append("rule_type = ?")
        params.append(rule_type)
    if new_status is not None:
        conditions.append("new_status = ?")
        params.append(new_status)
    where_clause = " AND ".join(conditions)
    limit_clause = ""
    if limit is not None:
        limit_clause = " LIMIT ?"
        params.append(limit)
    return connection.execute(
        f"""
        SELECT *
        FROM rule_decisions
        WHERE {where_clause}
        ORDER BY id DESC
        {limit_clause}
        """,
        tuple(params),
    ).fetchall()


def list_raw_observed_transitions(connection: sqlite3.Connection, scope: str = "global") -> list[sqlite3.Row]:
    return connection.execute(
        """
        SELECT scope, prefix_json, next_token, support, total, confidence
        FROM observed_transitions
        WHERE scope = ?
        ORDER BY LENGTH(prefix_json) DESC, confidence DESC, support DESC, id ASC
        """,
        (scope,),
    ).fetchall()


def delete_scope_decisions(connection: sqlite3.Connection, scope: str) -> None:
    connection.execute("DELETE FROM rule_decisions WHERE scope = ?", (scope,))


def upsert_rule_stats(
    connection: sqlite3.Connection,
    *,
    rule_id: int,
    hit_count: int,
    violation_count: int,
    last_hit_at: str | None,
    last_violation_at: str | None,
) -> None:
    connection.execute(
        """
        INSERT INTO rule_stats(rule_id, hit_count, violation_count, last_hit_at, last_violation_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(rule_id) DO UPDATE SET
            hit_count = excluded.hit_count,
            violation_count = excluded.violation_count,
            last_hit_at = excluded.last_hit_at,
            last_violation_at = excluded.last_violation_at
        """,
        (rule_id, hit_count, violation_count, last_hit_at, last_violation_at),
    )


def replace_observed_transitions(
    connection: sqlite3.Connection,
    scope: str,
    transitions: list[tuple[str, str, int, int, float]],
) -> None:
    connection.execute("DELETE FROM observed_transitions WHERE scope = ?", (scope,))
    connection.executemany(
        """
        INSERT INTO observed_transitions(scope, prefix_json, next_token, support, total, confidence)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        [(scope, *transition) for transition in transitions],
    )


def list_observed_transitions(connection: sqlite3.Connection, scope: str = "global") -> list[sqlite3.Row]:
    return connection.execute(
        """
        SELECT
            ot.prefix_json,
            ot.next_token,
            ot.support,
            ot.total,
            ot.confidence,
            cr.id AS rule_id,
            cr.status AS rule_status
        FROM observed_transitions AS ot
        LEFT JOIN candidate_rules AS cr
          ON cr.rule_type = 'next_token'
         AND cr.prefix_json = ot.prefix_json
         AND cr.expected_token = ot.next_token
         AND cr.scope = ot.scope
        WHERE ot.scope = ?
        ORDER BY LENGTH(ot.prefix_json) DESC, ot.confidence DESC, ot.support DESC, ot.id ASC
        """,
        (scope,),
    ).fetchall()


def clear_scope(connection: sqlite3.Connection, scope: str) -> None:
    connection.execute("DELETE FROM artifact_scope_bindings WHERE scope = ?", (scope,))
    connection.execute("DELETE FROM observed_transitions WHERE scope = ?", (scope,))
    connection.execute("DELETE FROM candidate_rules WHERE scope = ?", (scope,))


def set_scope_keywords(connection: sqlite3.Connection, scope: str, keywords: list[str]) -> None:
    """Persist the keyword set used to tokenize a scope's corpus.

    Stored sorted+deduped so lint reconstructs the exact same token classes
    that catch used when building the rules.
    """
    payload = json.dumps(sorted(set(keywords)), ensure_ascii=True)
    connection.execute(
        """
        INSERT INTO scope_config(scope, keywords_json) VALUES (?, ?)
        ON CONFLICT(scope) DO UPDATE SET keywords_json = excluded.keywords_json
        """,
        (scope, payload),
    )


def get_scope_keywords(connection: sqlite3.Connection, scope: str) -> frozenset[str]:
    row = connection.execute(
        "SELECT keywords_json FROM scope_config WHERE scope = ?", (scope,)
    ).fetchone()
    if row is None:
        return frozenset()
    return frozenset(json.loads(str(row["keywords_json"])))


def _ensure_column(connection: sqlite3.Connection, table_name: str, column_name: str, column_spec: str) -> None:
    columns = {
        row["name"]
        for row in connection.execute(f"PRAGMA table_info({table_name})").fetchall()
    }
    if column_name not in columns:
        connection.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_spec}")


def _record_rule_decision(
    connection: sqlite3.Connection,
    row: sqlite3.Row,
    *,
    previous_status: str,
    new_status: str,
    automatic: bool,
    actor: str | None,
    source: str | None,
    reason: str | None,
) -> None:
    connection.execute(
        """
        INSERT INTO rule_decisions(
            rule_id,
            scope,
            rule_type,
            prefix_json,
            expected_token,
            previous_status,
            new_status,
            automatic,
            actor,
            source,
            reason
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            int(row["id"]),
            str(row["scope"]),
            str(row["rule_type"]),
            str(row["prefix_json"]),
            str(row["expected_token"]),
            previous_status,
            new_status,
            1 if automatic else 0,
            actor,
            source,
            reason,
        ),
    )


def insert_rule_decision_record(
    connection: sqlite3.Connection,
    *,
    rule_id: int | None,
    scope: str,
    rule_type: str,
    prefix_json: str,
    expected_token: str,
    previous_status: str,
    new_status: str,
    automatic: bool,
    actor: str | None,
    source: str | None,
    reason: str | None,
    created_at: str,
) -> None:
    existing = connection.execute(
        """
        SELECT id
        FROM rule_decisions
        WHERE
            scope = ?
            AND rule_type = ?
            AND prefix_json = ?
            AND expected_token = ?
            AND previous_status = ?
            AND new_status = ?
            AND automatic = ?
            AND created_at = ?
            AND ((rule_id IS NULL AND ? IS NULL) OR rule_id = ?)
            AND ((actor IS NULL AND ? IS NULL) OR actor = ?)
            AND ((source IS NULL AND ? IS NULL) OR source = ?)
            AND ((reason IS NULL AND ? IS NULL) OR reason = ?)
        LIMIT 1
        """,
        (
            scope,
            rule_type,
            prefix_json,
            expected_token,
            previous_status,
            new_status,
            1 if automatic else 0,
            created_at,
            rule_id,
            rule_id,
            actor,
            actor,
            source,
            source,
            reason,
            reason,
        ),
    ).fetchone()
    if existing is not None:
        return
    connection.execute(
        """
        INSERT INTO rule_decisions(
            rule_id,
            scope,
            rule_type,
            prefix_json,
            expected_token,
            previous_status,
            new_status,
            automatic,
            actor,
            source,
            reason,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            rule_id,
            scope,
            rule_type,
            prefix_json,
            expected_token,
            previous_status,
            new_status,
            1 if automatic else 0,
            actor,
            source,
            reason,
            created_at,
        ),
    )
