"""verdict.py — the HANDLER ruling on a goldenization request.

`accept` / `reject` are the ONLY authority in this package. Nothing self-promotes:
a promotion effect (effects.py) fires only when a handler `accept`s. A `reject`
carries a reason — those reasons are the HARD NEGATIVES for the learned
acceptance model that later staffs this gate.

Verdict record shape — MIRRORS base/acceptance's `acceptance.schema.Verdict`
(read via `git show acceptance-handler:base/acceptance/acceptance/schema.py`).
We do NOT import across branches; we reproduce the shape as a plain dict so the
verdicts corpus is drop-in compatible with that reader. Field mapping:

    base/acceptance Verdict field   ← goldenreq source
    ------------------------------    ----------------------------------------
    id                              ← a fresh verdict id ("vd-…")
    ts                              ← ruling timestamp (ISO-8601)
    domain                          ← "goldenize"  (base lists this exact domain)
    artifact_ref                    ← request.candidate_id (what was judged)
    context_ref                     ← request.request_id   (the request it belongs to)
    gauge.source                    ← request.requester    (the self-claiming gauge)
    gauge.score                     ← request.requested_promotion (the gauge's claim)
    gauge.reasons                   ← request.evidence     (the receipts it filed)
    handler.verdict                 ← "accept" | "reject"  (base also has "escalate"
                                       = still-pending; a pending request is exactly
                                       that state, so it has NO verdict record yet)
    handler.actor                   ← `by`, coerced to "human:<who>" / "model:<id>"
    handler.reasons                 ← [reason]  (rejections MUST carry one)
    handler.edits_made              ← None (goldenreq handlers rule, they don't edit)
    outcome                         ← the promotion effect's result on accept, else None
"""
from __future__ import annotations

import os
import re
import uuid

from . import effects
from .queue import (
    get_request, now_iso, resolve_queue_path, resolve_verdicts_path,
    ruled_request_ids, _append, _read_all,
)

ACTOR_PATTERN = re.compile(r"^(human|model):.+$")  # base/acceptance schema.ACTOR_PATTERN


def new_verdict_id() -> str:
    return "vd-" + uuid.uuid4().hex[:24]


def _actor(by: str) -> str:
    """Coerce `by` to the base schema's `^(human|model):.+$` actor form.
    A bare name is assumed human (the default handler is a person doing QA)."""
    by = (by or "").strip()
    if not by:
        raise ValueError("a verdict requires `by` (the ruling actor)")
    return by if ACTOR_PATTERN.match(by) else f"human:{by}"


def _build_verdict(request: dict, decision: str, by: str,
                   reasons: list[str], outcome: dict | None) -> dict:
    """One acceptance event, in base/acceptance Verdict shape (see module docstring)."""
    return {
        "id": new_verdict_id(),
        "ts": now_iso(),
        "domain": "goldenize",
        "artifact_ref": request["candidate_id"],
        "context_ref": request["request_id"],
        "gauge": {
            "source": request.get("requester", ""),
            "score": request.get("requested_promotion"),
            "reasons": list(request.get("evidence", [])),
        },
        "handler": {
            "verdict": decision,
            "actor": _actor(by),
            "reasons": list(reasons),
            "edits_made": None,
        },
        "outcome": outcome,
    }


def _guard(request_id: str, queue_path) -> dict:
    request = get_request(request_id, queue_path=queue_path)
    if request is None:
        raise ValueError(f"no such request: {request_id}")
    if request_id in ruled_request_ids(queue_path):
        raise ValueError(f"request {request_id} already has a verdict (no double-ruling)")
    return request


def accept(request_id: str, by: str, reason: str = "", *,
           queue_path: str | os.PathLike | None = None,
           verdicts_path: str | os.PathLike | None = None,
           effect_kwargs: dict | None = None) -> dict:
    """ACCEPT a request → fire its promotion effect, then record the verdict.

    The effect runs BEFORE the record is written so its result is captured in
    `outcome` (the audit trail). If the effect raises, nothing is recorded and
    the request stays pending — no half-promotion. Returns the verdict record.
    """
    from pathlib import Path
    request = _guard(request_id, queue_path)
    outcome = effects.dispatch(request, by=_actor(by), **(effect_kwargs or {}))
    verdict = _build_verdict(request, "accept", by, [reason] if reason else [], outcome)
    vpath = Path(verdicts_path) if verdicts_path is not None else resolve_verdicts_path(queue_path)
    _append(vpath, verdict)
    return verdict


def reject(request_id: str, by: str, reason: str, *,
           queue_path: str | os.PathLike | None = None,
           verdicts_path: str | os.PathLike | None = None) -> dict:
    """REJECT a request → NO effect, record the verdict with its reason.

    The reason is mandatory: rejections are the hard negatives the learned
    acceptance model trains on. Nothing is promoted.
    """
    if not (reason or "").strip():
        raise ValueError("reject requires a reason (it is the hard negative)")
    request = _guard(request_id, queue_path)
    verdict = _build_verdict(request, "reject", by, [reason], None)
    from pathlib import Path
    vpath = Path(verdicts_path) if verdicts_path is not None else resolve_verdicts_path(queue_path)
    _append(vpath, verdict)
    return verdict


def list_verdicts(queue_path: str | os.PathLike | None = None,
                  verdicts_path: str | os.PathLike | None = None) -> list[dict]:
    from pathlib import Path
    vpath = Path(verdicts_path) if verdicts_path is not None else resolve_verdicts_path(queue_path)
    return _read_all(vpath)
