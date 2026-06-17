from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from sqlite3 import Connection

from .db import fetch_evidence, get_scope_keywords, record_rule_evaluations
from .engine import decode_prefix
from .models import LintViolation, NormalizationSuggestion
from .tokenize import EOL, line_token_kinds, line_token_texts, token_for_sequence_index, tokenize_text


def lint_path(connection: Connection, path: Path, *, scope: str = "global") -> list[LintViolation]:
    text = path.read_text(encoding="utf-8")
    return lint_text(connection, text, label=str(path), scope=scope)


def lint_text(
    connection: Connection,
    text: str,
    *,
    label: str = "<stdin>",
    scope: str = "global",
    record_stats: bool = True,
) -> list[LintViolation]:
    # Reconstruct the same token classes catch used (keywords are per-scope).
    keywords = get_scope_keywords(connection, scope)
    adopted_rules = connection.execute(
        """
        SELECT id, rule_type, prefix_json, expected_token, confidence
        FROM candidate_rules
        WHERE status = 'adopted' AND rule_type IN ('next_token', 'next_kind') AND scope = ?
        ORDER BY id
        """,
        (scope,),
    ).fetchall()

    literal_by_prefix: dict[tuple[str, ...], list[tuple[int, str, float]]] = defaultdict(list)
    kind_by_prefix: dict[tuple[str, ...], list[tuple[int, str, float]]] = defaultdict(list)
    kind_candidates_by_rule_id: dict[int, tuple[str, ...]] = {}
    prefix_lengths: set[int] = set()
    # The "vocabulary" of the language: which kinds and which literal tokens the
    # adopted grammar actually uses anywhere. A violation whose found element is
    # in this vocabulary is ORTHOGONAL (right language, wrong slot -> steerable);
    # one that is foreign is a SYNTAX_BREAK (-> fatal). This is the grain axis.
    known_kinds: set[str] = set()
    known_tokens: set[str] = set()
    for row in adopted_rules:
        rule_id = int(row["id"])
        prefix = decode_prefix(str(row["prefix_json"]))
        if row["rule_type"] == "next_token":
            literal_by_prefix[prefix].append((rule_id, str(row["expected_token"]), float(row["confidence"])))
            known_tokens.update(prefix)
            known_tokens.add(str(row["expected_token"]))
        else:
            kind_by_prefix[prefix].append((rule_id, str(row["expected_token"]), float(row["confidence"])))
            kind_candidates_by_rule_id[rule_id] = _candidate_tokens_for_kind_rule(connection, rule_id)
            known_kinds.update(prefix)
            known_kinds.add(str(row["expected_token"]))
        prefix_lengths.add(len(prefix))

    violations: list[LintViolation] = []
    hit_rule_ids: list[int] = []
    violation_rule_ids: list[int] = []
    for token_line in tokenize_text(text):
        text_sequence = line_token_texts(token_line)
        kind_sequence = line_token_kinds(token_line, keywords)
        for index in range(1, len(text_sequence)):
            actual = text_sequence[index]
            actual_kind = kind_sequence[index]
            matching_rules: list[tuple[int, str, tuple[str, ...], str, float]] = []
            for prefix_length in prefix_lengths:
                start = index - prefix_length
                if start < 0:
                    continue
                literal_prefix = tuple(text_sequence[start:index])
                for rule_id, expected, confidence in literal_by_prefix.get(literal_prefix, []):
                    matching_rules.append((rule_id, "next_token", literal_prefix, expected, confidence))
                kind_prefix = tuple(kind_sequence[start:index])
                for rule_id, expected, confidence in kind_by_prefix.get(kind_prefix, []):
                    matching_rules.append((rule_id, "next_kind", kind_prefix, expected, confidence))

            if not matching_rules:
                continue

            longest = max(len(prefix) for _, _, prefix, _, _ in matching_rules)
            most_specific = max(1 if rule_type == "next_token" else 0 for _, rule_type, _, _, _ in matching_rules)
            for rule_id, rule_type, prefix, expected, confidence in matching_rules:
                if len(prefix) != longest:
                    continue
                if (1 if rule_type == "next_token" else 0) != most_specific:
                    continue
                if rule_type == "next_token":
                    satisfied = expected == actual
                    candidate_tokens = (expected,)
                    suggested_action = _literal_suggested_action(expected=expected, found=actual)
                else:
                    satisfied = expected == actual_kind
                    candidate_tokens = kind_candidates_by_rule_id.get(rule_id, ())
                    suggested_action = "insert" if actual == EOL else "insert_before"
                if satisfied:
                    hit_rule_ids.append(rule_id)
                    continue
                violation_rule_ids.append(rule_id)
                token = token_for_sequence_index(token_line, index)
                # Grain axis: is the found element in the language at all?
                in_language = actual_kind in known_kinds or actual in known_tokens
                verdict = "orthogonal" if in_language else "syntax_break"
                violations.append(
                    LintViolation(
                        rule_id=rule_id,
                        rule_type=rule_type,
                        path=label,
                        line_no=token_line.line_no,
                        prefix=prefix,
                        expected_token=expected,
                        found_token=actual,
                        found_kind=actual_kind,
                        confidence=confidence,
                        context=token_line.text,
                        start=None if token is None else token.absolute_start,
                        end=None if token is None else token.absolute_end,
                        candidate_tokens=candidate_tokens,
                        suggested_action=suggested_action,
                        verdict=verdict,
                    )
                )
    if record_stats and (hit_rule_ids or violation_rule_ids):
        record_rule_evaluations(connection, hit_rule_ids, violation_rule_ids)
    return violations


def build_normalization_suggestions(violations: list[LintViolation]) -> list[NormalizationSuggestion]:
    suggestions: list[NormalizationSuggestion] = []
    for violation in violations:
        if violation.rule_type == "next_kind":
            replacement = None
            expected_display = _kind_display(violation.expected_token)
            candidate_tokens = tuple(violation.candidate_tokens)
            if candidate_tokens:
                reason = (
                    f"History predicted {expected_display} after {[_kind_display(p) for p in violation.prefix]!r}; "
                    f"found {violation.found_token!r} of class {_kind_display(violation.found_kind)}. "
                    f"Observed concrete tokens for {expected_display}: {list(candidate_tokens)!r}"
                )
            else:
                reason = (
                    f"History predicted {expected_display} after {[_kind_display(p) for p in violation.prefix]!r}; "
                    f"found {violation.found_token!r} of class {_kind_display(violation.found_kind)}"
                )
        elif violation.found_token == EOL:
            replacement = violation.expected_token
            expected_display = violation.expected_token
            candidate_tokens = tuple(violation.candidate_tokens)
            reason = f"History predicted {violation.expected_token!r} after {list(violation.prefix)!r}"
        elif violation.expected_token == EOL:
            replacement = None
            expected_display = violation.expected_token
            candidate_tokens = tuple(violation.candidate_tokens)
            reason = f"History predicted {violation.expected_token!r} after {list(violation.prefix)!r}"
        else:
            replacement = violation.expected_token
            expected_display = violation.expected_token
            candidate_tokens = tuple(violation.candidate_tokens)
            reason = f"History predicted {violation.expected_token!r} after {list(violation.prefix)!r}"
        suggestions.append(
            NormalizationSuggestion(
                path=violation.path,
                line_no=violation.line_no,
                expected_token=expected_display,
                found_token=violation.found_token,
                start=violation.start,
                end=violation.end,
                replacement=replacement,
                reason=reason,
                candidate_tokens=candidate_tokens,
                suggested_action=violation.suggested_action,
                verdict=violation.verdict,  # additive: orthogonal vs syntax_break
            )
        )
    return suggestions


def apply_normalization(text: str, suggestions: list[NormalizationSuggestion]) -> str:
    edits = [
        suggestion
        for suggestion in suggestions
        if suggestion.replacement is not None and suggestion.start is not None and suggestion.end is not None
    ]
    normalized = text
    for suggestion in sorted(edits, key=lambda item: item.start or 0, reverse=True):
        assert suggestion.start is not None
        assert suggestion.end is not None
        normalized = normalized[: suggestion.start] + suggestion.replacement + normalized[suggestion.end :]
    return normalized


def _kind_display(kind: str) -> str:
    if kind in {"<BOS>", "<EOL>"}:
        return kind
    return f"<{kind}>"


def _candidate_tokens_for_kind_rule(connection: Connection, rule_id: int) -> tuple[str, ...]:
    seen: set[str] = set()
    candidates: list[str] = []
    for row in fetch_evidence(connection, rule_id):
        token = str(row["observed_token"])
        if token in seen:
            continue
        seen.add(token)
        candidates.append(token)
    return tuple(candidates)


def _literal_suggested_action(*, expected: str, found: str) -> str:
    if found == EOL:
        return "insert"
    if expected == EOL:
        return "remove"
    return "replace"
