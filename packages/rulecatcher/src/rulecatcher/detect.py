from __future__ import annotations

from collections import Counter, defaultdict

from .models import ArtifactRecord, CandidateRule, ObservedTransition, RuleEvidence
from .tokenize import line_token_kinds, line_token_texts, tokenize_text


def collect_next_token_rules(
    artifacts: list[ArtifactRecord],
    *,
    scope: str = "global",
    min_support: int = 2,
    min_confidence: float = 0.75,
    max_prefix: int = 2,
    evidence_limit: int = 5,
) -> list[CandidateRule]:
    counts: dict[tuple[str, ...], Counter[str]] = defaultdict(Counter)
    evidence_map: dict[tuple[tuple[str, ...], str], list[RuleEvidence]] = defaultdict(list)

    for artifact in artifacts:
        for token_line in tokenize_text(artifact.content):
            sequence = line_token_texts(token_line)
            for index in range(1, len(sequence)):
                observed = sequence[index]
                for prefix_size in range(1, max_prefix + 1):
                    start = index - prefix_size
                    if start < 0:
                        continue
                    prefix = tuple(sequence[start:index])
                    counts[prefix][observed] += 1
                    key = (prefix, observed)
                    if len(evidence_map[key]) < evidence_limit:
                        evidence_map[key].append(
                            RuleEvidence(
                                artifact_id=artifact.id,
                                artifact_path=artifact.path,
                                line_no=token_line.line_no,
                                observed_token=observed,
                                context=token_line.text,
                            )
                        )

    candidates: list[CandidateRule] = []
    for prefix, observed_counts in counts.items():
        total = sum(observed_counts.values())
        for expected_token, support in observed_counts.items():
            confidence = support / total if total else 0.0
            if support < min_support:
                continue
            if confidence < min_confidence:
                continue
            candidates.append(
                CandidateRule(
                    rule_type="next_token",
                    prefix=prefix,
                    expected_token=expected_token,
                    support=support,
                    total=total,
                    confidence=confidence,
                    evidences=tuple(evidence_map[(prefix, expected_token)]),
                    scope=scope,
                )
            )

    return sorted(
        candidates,
        key=lambda rule: (-len(rule.prefix), -rule.confidence, -rule.support, rule.prefix, rule.expected_token),
    )


def collect_observed_transitions(
    artifacts: list[ArtifactRecord],
    *,
    max_prefix: int = 2,
) -> list[ObservedTransition]:
    counts: dict[tuple[str, ...], Counter[str]] = defaultdict(Counter)

    for artifact in artifacts:
        for token_line in tokenize_text(artifact.content):
            sequence = line_token_texts(token_line)
            for index in range(1, len(sequence)):
                observed = sequence[index]
                for prefix_size in range(1, max_prefix + 1):
                    start = index - prefix_size
                    if start < 0:
                        continue
                    prefix = tuple(sequence[start:index])
                    counts[prefix][observed] += 1

    transitions: list[ObservedTransition] = []
    for prefix, observed_counts in counts.items():
        total = sum(observed_counts.values())
        for next_token, support in observed_counts.items():
            transitions.append(
                ObservedTransition(
                    prefix=prefix,
                    next_token=next_token,
                    support=support,
                    total=total,
                    confidence=support / total if total else 0.0,
                )
            )

    return sorted(
        transitions,
        key=lambda item: (-len(item.prefix), -item.confidence, -item.support, item.prefix, item.next_token),
    )


def collect_next_kind_rules(
    artifacts: list[ArtifactRecord],
    *,
    scope: str = "global",
    min_support: int = 2,
    min_confidence: float = 0.75,
    max_prefix: int = 2,
    evidence_limit: int = 5,
    keywords: frozenset[str] = frozenset(),
) -> list[CandidateRule]:
    counts: dict[tuple[str, ...], Counter[str]] = defaultdict(Counter)
    evidence_map: dict[tuple[tuple[str, ...], str], list[RuleEvidence]] = defaultdict(list)

    for artifact in artifacts:
        for token_line in tokenize_text(artifact.content):
            kind_sequence = line_token_kinds(token_line, keywords)
            text_sequence = line_token_texts(token_line)
            for index in range(1, len(kind_sequence)):
                observed_kind = kind_sequence[index]
                observed_token = text_sequence[index]
                for prefix_size in range(1, max_prefix + 1):
                    start = index - prefix_size
                    if start < 0:
                        continue
                    prefix = tuple(kind_sequence[start:index])
                    counts[prefix][observed_kind] += 1
                    key = (prefix, observed_kind)
                    if len(evidence_map[key]) < evidence_limit:
                        evidence_map[key].append(
                            RuleEvidence(
                                artifact_id=artifact.id,
                                artifact_path=artifact.path,
                                line_no=token_line.line_no,
                                observed_token=observed_token,
                                context=token_line.text,
                            )
                        )

    candidates: list[CandidateRule] = []
    for prefix, observed_counts in counts.items():
        total = sum(observed_counts.values())
        for expected_kind, support in observed_counts.items():
            confidence = support / total if total else 0.0
            if support < min_support:
                continue
            if confidence < min_confidence:
                continue
            candidates.append(
                CandidateRule(
                    rule_type="next_kind",
                    prefix=prefix,
                    expected_token=expected_kind,
                    support=support,
                    total=total,
                    confidence=confidence,
                    evidences=tuple(evidence_map[(prefix, expected_kind)]),
                    scope=scope,
                )
            )

    return sorted(
        candidates,
        key=lambda rule: (-len(rule.prefix), -rule.confidence, -rule.support, rule.prefix, rule.expected_token),
    )
