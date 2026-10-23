"""goldenreq — the acceptance gate. Nothing self-promotes; only an accepted
verdict fires an effect; the verdict record mirrors base/acceptance's schema."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

import goldenreq
from goldenreq import effects
from goldenreq.queue import resolve_verdicts_path


def _q(tmp_path) -> Path:
    return tmp_path / "goldenreq_queue.jsonl"


# ── file → list → accept → effect (chain-golden marker lands in a GBA KB) ────
def test_file_list_accept_chain_golden_marker_lands(tmp_path):
    q = _q(tmp_path)
    # a real GBA KB note, headed with a glyphs grade line (chainaios kb_instructions shape)
    kb = tmp_path / "kb"; kb.mkdir()
    note = kb / "rollback-chain.md"
    original = "glyphs: 🏆🏆\n\n# rollback chain\n\nConstructed chain that earned 🏆 twice.\n"
    note.write_text(original)

    rid = goldenreq.file_request(
        "chain-golden", str(note),
        evidence=[str(note), "round-7 reward log"],
        requested_promotion="golden", requester="triage-bandit", queue_path=q)
    assert rid.startswith("gr-")

    pending = goldenreq.list_pending(q)
    assert len(pending) == 1 and pending[0]["request_id"] == rid
    assert pending[0]["status"] == "pending"

    verdict = goldenreq.accept(rid, "human:alice", "chain proved out twice", queue_path=q)

    # the promotion effect actually ran: marker APPENDED, original NOT rewritten
    body = note.read_text()
    assert body.startswith(original)                     # agent's note untouched
    assert "ACCEPTED-BY: human:alice" in body
    assert "🏆🏆 → golden" in body
    assert verdict["handler"]["verdict"] == "accept"
    assert verdict["outcome"]["effect"] == "chain-golden"

    # once ruled, it leaves the pending inbox
    assert goldenreq.list_pending(q) == []


# ── reject → no effect + reason recorded as a hard negative ──────────────────
def test_reject_records_reason_and_fires_no_effect(tmp_path):
    q = _q(tmp_path)
    kb = tmp_path / "kb"; kb.mkdir()
    note = kb / "flaky-chain.md"
    original = "glyphs: 🏆\n\n# flaky chain\n"
    note.write_text(original)

    rid = goldenreq.file_request("chain-golden", str(note), evidence=[str(note)],
                                 requested_promotion="golden", requester="triage-bandit",
                                 queue_path=q)
    verdict = goldenreq.reject(rid, "human:alice", "only one 🏆, evidence thin", queue_path=q)

    assert verdict["handler"]["verdict"] == "reject"
    assert verdict["handler"]["reasons"] == ["only one 🏆, evidence thin"]
    assert verdict["outcome"] is None
    assert note.read_text() == original                  # NO effect ran
    assert goldenreq.list_pending(q) == []               # ruled → out of inbox


def test_reject_requires_a_reason(tmp_path):
    q = _q(tmp_path)
    rid = goldenreq.file_request("chain-golden", "/x", evidence=[], requested_promotion="golden",
                                 requester="b", queue_path=q)
    with pytest.raises(ValueError):
        goldenreq.reject(rid, "human:alice", "", queue_path=q)


def test_no_double_ruling(tmp_path):
    q = _q(tmp_path)
    note = tmp_path / "n.md"; note.write_text("glyphs: 🏆🏆\n")
    rid = goldenreq.file_request("chain-golden", str(note), evidence=[], requested_promotion="golden",
                                 requester="b", queue_path=q)
    goldenreq.accept(rid, "human:alice", queue_path=q)
    with pytest.raises(ValueError):
        goldenreq.reject(rid, "human:alice", "changed my mind", queue_path=q)


# ── verdict records match the documented base/acceptance field mapping ───────
def test_verdict_record_mirrors_base_acceptance_schema(tmp_path):
    q = _q(tmp_path)
    note = tmp_path / "n.md"; note.write_text("glyphs: 🏆🏆\n")
    rid = goldenreq.file_request(
        "chain-golden", str(note), evidence=["ev-a", "ev-b"],
        requested_promotion="golden", requester="triage-bandit", queue_path=q)
    v = goldenreq.accept(rid, "alice", "ok", queue_path=q)  # bare name → coerced to human:

    # the exact keys base/acceptance.schema.Verdict defines
    assert set(v) == {"id", "ts", "domain", "artifact_ref", "context_ref",
                      "gauge", "handler", "outcome"}
    assert v["id"].startswith("vd-")
    assert v["domain"] == "goldenize"                       # base lists this domain
    assert v["artifact_ref"] == str(note)                   # ← request.candidate_id
    assert v["context_ref"] == rid                          # ← request.request_id
    # gauge = the internal claim (never authority)
    assert set(v["gauge"]) == {"source", "score", "reasons"}
    assert v["gauge"]["source"] == "triage-bandit"          # ← request.requester
    assert v["gauge"]["score"] == "golden"                  # ← request.requested_promotion
    assert v["gauge"]["reasons"] == ["ev-a", "ev-b"]        # ← request.evidence
    # handler = the external authority; actor matches base's ^(human|model):.+$
    assert set(v["handler"]) == {"verdict", "actor", "reasons", "edits_made"}
    assert v["handler"]["actor"] == "human:alice"
    assert v["handler"]["verdict"] in {"accept", "reject"}
    assert v["handler"]["edits_made"] is None

    # it round-trips as a JSONL corpus line (drop-in for the base reader)
    vpath = resolve_verdicts_path(q)
    line = vpath.read_text().splitlines()[-1]
    assert json.loads(line)["id"] == v["id"]


# ── pack-grade-bump is a pure ladder step ────────────────────────────────────
def test_bump_pack_grade_is_pure_and_matches_personapack_ladder():
    # ladder best→worst: tested-with-receipt > proven-in-forge > seed
    assert effects.bump_pack_grade("seed") == "proven-in-forge"
    assert effects.bump_pack_grade("proven-in-forge") == "tested-with-receipt"
    assert effects.bump_pack_grade("tested-with-receipt") == "tested-with-receipt"  # capped at top
    with pytest.raises(ValueError):
        effects.bump_pack_grade("made-up")
    # drift guard: our literal ladder equals personapack's GRADES
    from personapack.entry import GRADES
    assert effects.PACK_GRADES == GRADES


def test_pack_grade_bump_via_accept(tmp_path):
    q = _q(tmp_path)
    rid = goldenreq.file_request("pack-grade-bump", "some-persona", evidence=["gba-receipt"],
                                 requested_promotion="proven-in-forge", requester="personapack",
                                 queue_path=q)
    v = goldenreq.accept(rid, "human:alice", queue_path=q)
    assert v["outcome"]["effect"] == "pack-grade-bump"
    assert v["outcome"]["new_grade"] == "tested-with-receipt"


# ── the honest stubs raise NotImplementedError (no fake integration) ─────────
def test_rule_adopt_and_template_promote_are_honest_stubs(tmp_path):
    q = _q(tmp_path)
    for kind in ("rule-adopt", "template-promote"):
        rid = goldenreq.file_request(kind, "cand", evidence=[], requested_promotion="adopt",
                                     requester="g", queue_path=q)
        with pytest.raises(NotImplementedError):
            goldenreq.accept(rid, "human:alice", queue_path=q)
        # the failed effect left the request PENDING (no half-promotion, no verdict)
        assert any(r["request_id"] == rid for r in goldenreq.list_pending(q))


# ── the chainaios bandit.py rule text no longer self-promotes (grep test) ────
def test_bandit_rule_text_files_a_request_not_self_fold():
    bandit = (Path(__file__).resolve().parents[2] / "chainaios" / "src" / "chainaios" / "bandit.py")
    text = bandit.read_text()
    assert "FILE A GOLDENIZATION REQUEST" in text
    assert "never self-fold to golden" in text
    assert "promotion" in text and "accepted verdict" in text
    # the old self-certifying instruction is gone
    assert "fold it into a golden chain" not in text
