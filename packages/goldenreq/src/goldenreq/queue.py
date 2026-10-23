"""queue.py — the goldenization request queue (append-only JSONL).

Same append-only ledger idiom as the KB reward record and base/acceptance's
verdict corpus (a `write` is one JSON line; nothing is ever mutated in place).

A REQUEST is a *gauge-passed, handler-pending* event: a gauge — the bandit's
2×🏆 on a constructed chain, a rulecatcher candidate rule, a forged
language/template, a personapack `activation_grade` claim — asks for a
promotion it may NOT grant itself. The request carries its RECEIPTS (evidence)
and sits pending until a handler rules on it (see ``verdict.py``). This is
JobWorld's ``supposedly_done`` made explicit, and base/acceptance's
``handler.verdict == "escalate"`` (gauge-passed, handler-pending) as a queue.

THE LAW: the gauge never certifies itself. Filing a request is the ONLY thing a
gauge may do toward promotion; the promotion effect fires only on an accepted
verdict.
"""
from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

# the four things that can be promoted (each has a real gauge upstream)
KINDS: tuple[str, ...] = (
    "chain-golden",      # a constructed bandit chain earned 🏆 twice (chainaios)
    "rule-adopt",        # a rulecatcher candidate rule wants adoption
    "template-promote",  # a forged language / template wants to become canon
    "pack-grade-bump",   # a personapack PackEntry wants a higher activation_grade
)

QUEUE_ENV = "GOLDENREQ_QUEUE_PATH"
VERDICTS_ENV = "GOLDENREQ_VERDICTS_PATH"
DEFAULT_QUEUE = "goldenreq_queue.jsonl"
DEFAULT_VERDICTS = "verdicts.jsonl"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def resolve_queue_path(path: str | os.PathLike | None = None) -> Path:
    return Path(path or os.environ.get(QUEUE_ENV) or DEFAULT_QUEUE)


def resolve_verdicts_path(queue_path: str | os.PathLike | None = None) -> Path:
    """The verdicts corpus sits beside the queue (or at $GOLDENREQ_VERDICTS_PATH).
    Mirrors base/acceptance's `resolve_corpus_path` — env override, else default."""
    env = os.environ.get(VERDICTS_ENV)
    if env:
        return Path(env)
    return resolve_queue_path(queue_path).parent / DEFAULT_VERDICTS


def _append(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, sort_keys=True) + "\n")


def _read_all(path: Path) -> list[dict]:
    out: list[dict] = []
    if not Path(path).exists():
        return out
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except Exception:
                continue
    return out


def new_request_id() -> str:
    return "gr-" + uuid.uuid4().hex[:24]


def file_request(kind: str, candidate_id: str, evidence: list[str],
                 requested_promotion: str, requester: str,
                 queue_path: str | os.PathLike | None = None) -> str:
    """Append one goldenization request to the queue. Returns its request_id.

    `evidence` = the receipts (graded KB note paths, cert ids, forge reports).
    A request with no evidence is still filed (honest — an unevidenced ask is a
    weak ask a handler will likely reject), but evidence is what an acceptance
    model later learns from, so gauges SHOULD attach it.
    """
    if kind not in KINDS:
        raise ValueError(f"kind {kind!r} not in {KINDS}")
    rid = new_request_id()
    rec = {
        "request_id": rid,
        "ts": now_iso(),
        "kind": kind,
        "candidate_id": candidate_id,
        "evidence": list(evidence or []),
        "requested_promotion": requested_promotion,
        "requester": requester,
        "status": "pending",
    }
    _append(resolve_queue_path(queue_path), rec)
    return rid


def get_request(request_id: str, queue_path: str | os.PathLike | None = None) -> dict | None:
    for rec in _read_all(resolve_queue_path(queue_path)):
        if rec.get("request_id") == request_id:
            return rec
    return None


def ruled_request_ids(queue_path: str | os.PathLike | None = None) -> set[str]:
    """request_ids that already carry a handler verdict (accept OR reject)."""
    vpath = resolve_verdicts_path(queue_path)
    return {v.get("context_ref") for v in _read_all(vpath) if v.get("context_ref")}


def list_pending(queue_path: str | os.PathLike | None = None) -> list[dict]:
    """Requests with no handler verdict yet — the handler's inbox.

    A request is pending ⇔ no verdict record points at it (verdict.context_ref
    == request_id). That is base/acceptance's `escalate` state: gauge-passed,
    handler-pending.
    """
    ruled = ruled_request_ids(queue_path)
    return [r for r in _read_all(resolve_queue_path(queue_path))
            if r.get("request_id") not in ruled]
