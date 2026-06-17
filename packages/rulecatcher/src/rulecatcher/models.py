from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ArtifactRecord:
    id: int
    path: str
    content: str
    sha256: str


@dataclass(frozen=True)
class ArtifactInput:
    label: str
    content: str


@dataclass(frozen=True)
class RuleEvidence:
    artifact_id: int
    artifact_path: str
    line_no: int
    observed_token: str
    context: str


@dataclass(frozen=True)
class CandidateRule:
    rule_type: str
    prefix: tuple[str, ...]
    expected_token: str
    support: int
    total: int
    confidence: float
    evidences: tuple[RuleEvidence, ...] = field(default_factory=tuple)
    status: str = "pending"
    scope: str = "global"
    id: int | None = None


@dataclass(frozen=True)
class ObservedTransition:
    prefix: tuple[str, ...]
    next_token: str
    support: int
    total: int
    confidence: float


@dataclass(frozen=True)
class LintViolation:
    rule_id: int
    rule_type: str
    path: str
    line_no: int
    prefix: tuple[str, ...]
    expected_token: str
    found_token: str
    found_kind: str
    confidence: float
    context: str
    start: int | None
    end: int | None
    candidate_tokens: tuple[str, ...] = field(default_factory=tuple)
    suggested_action: str = "replace"
    # Two-axis verdict (executable form of CSGN's CHECK):
    #   "orthogonal"   = the found token IS in the language, wrong slot/grain -> steerable (ROTATE)
    #   "syntax_break" = the found token is foreign to the language -> fatal (X)
    verdict: str = "syntax_break"


@dataclass(frozen=True)
class NormalizationSuggestion:
    path: str
    line_no: int
    expected_token: str
    found_token: str
    start: int | None
    end: int | None
    replacement: str | None
    reason: str
    candidate_tokens: tuple[str, ...] = field(default_factory=tuple)
    suggested_action: str = "replace"
    verdict: str = "syntax_break"


@dataclass(frozen=True)
class RuleHealth:
    rule_id: int
    scope: str
    rule_type: str
    status: str
    prefix: tuple[str, ...]
    expected_token: str
    support: int
    total: int
    confidence: float
    hit_count: int
    violation_count: int
    evaluation_count: int
    violation_rate: float
    last_hit_at: str | None
    last_violation_at: str | None
    recommendation: str


@dataclass(frozen=True)
class RuleProposal:
    rule_id: int
    scope: str
    rule_type: str
    prefix: tuple[str, ...]
    expected_token: str
    support: int
    total: int
    confidence: float
    competing_pending_rule_ids: tuple[int, ...] = field(default_factory=tuple)
    conflicting_adopted_rule_ids: tuple[int, ...] = field(default_factory=tuple)
    recommendation: str = "review"
    reasons: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class RuleDecision:
    id: int
    rule_id: int | None
    scope: str
    rule_type: str
    prefix: tuple[str, ...]
    expected_token: str
    previous_status: str
    new_status: str
    automatic: bool
    actor: str | None
    source: str | None
    reason: str | None
    created_at: str
