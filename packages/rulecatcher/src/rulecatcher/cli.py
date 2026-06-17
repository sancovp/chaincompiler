from __future__ import annotations

import argparse
import json
from pathlib import Path
from sqlite3 import Connection
import sys

from .compare import compare_scope_states, render_compare_report
from .db import connect, fetch_evidence, list_observed_transitions, list_rules
from .engine import adopt_rules, catch_patterns, reject_rules
from .explain import explain_rule, render_rule_explanation
from .governance import RECOMMENDATION_CHOICES, list_rule_health
from .graphing import build_transition_graph, render_transition_graph
from .history import read_rule_history
from .linting import apply_normalization, build_normalization_suggestions, lint_path, lint_text
from .models import ArtifactInput
from .present import (
    build_conflict_groups,
    display_prefix,
    display_token,
    serialize_rule_decision,
    serialize_evidence_row,
    serialize_observed_transition_row,
    serialize_rule_health,
    serialize_rule_proposal,
    serialize_rule_row,
    serialize_suggestion,
    serialize_violation,
)
from .report import build_scope_report, render_scope_report
from .session import process_session_stream
from .snapshot import export_scope_snapshot, import_scope_snapshot
from .tokenize import EOL
from .triage import (
    APPLYABLE_TRIAGE_RECOMMENDATIONS,
    TRIAGE_FOCUS_CHOICES,
    TRIAGE_RECOMMENDATIONS,
    apply_triage_recommendations,
    triage_pending_rules,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="rulecatcher", description="Catch and govern emergent syntax rules.")
    parser.add_argument("--db", default=".rulecatcher.db", help="SQLite database path.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    catch_parser = subparsers.add_parser("catch", help="Catch candidate rules from text files.")
    catch_parser.add_argument("paths", nargs="+", help="Input text files.")
    catch_parser.add_argument("--min-support", type=int, default=2)
    catch_parser.add_argument("--min-confidence", type=float, default=0.75)
    catch_parser.add_argument("--max-prefix", type=int, default=2)
    catch_parser.add_argument("--label", default="<stdin>", help="Label to use when ingesting stdin via '-'.")
    catch_parser.add_argument("--scope", default="global", help="Rule scope to replace and rebuild.")
    catch_parser.add_argument("--replace-scope", action="store_true", help="Clear the scope before ingesting new artifacts.")
    catch_parser.add_argument(
        "--keyword",
        action="append",
        default=None,
        dest="keywords",
        metavar="WORD",
        help="Treat WORD as a KEYWORD token class (repeatable). Persisted per scope and "
        "reused by lint/normalize. Lets the catcher separate language keywords (e.g. "
        "'state') from ordinary identifiers.",
    )
    catch_parser.add_argument("--json", action="store_true", help="Emit structured JSON output.")

    review_parser = subparsers.add_parser("review", help="Review candidate rules.")
    review_parser.add_argument("--status", choices=["pending", "adopted", "rejected"], default=None)
    review_parser.add_argument("--with-evidence", action="store_true")
    review_parser.add_argument("--scope", default="global", help="Scope to inspect.")
    review_parser.add_argument("--rule-type", choices=["next_token", "next_kind"], default=None)
    review_parser.add_argument("--json", action="store_true", help="Emit structured JSON output.")

    adopt_parser = subparsers.add_parser("adopt", help="Adopt one or more rule ids.")
    adopt_parser.add_argument("rule_ids", nargs="+", type=int)
    adopt_parser.add_argument("--actor", default=None, help="Actor label for the decision.")
    adopt_parser.add_argument("--source", default="cli", help="Decision source label.")
    adopt_parser.add_argument("--reason", default=None, help="Optional decision rationale.")
    adopt_parser.add_argument("--json", action="store_true", help="Emit structured JSON output.")

    reject_parser = subparsers.add_parser("reject", help="Reject one or more rule ids.")
    reject_parser.add_argument("rule_ids", nargs="+", type=int)
    reject_parser.add_argument("--actor", default=None, help="Actor label for the decision.")
    reject_parser.add_argument("--source", default="cli", help="Decision source label.")
    reject_parser.add_argument("--reason", default=None, help="Optional decision rationale.")
    reject_parser.add_argument("--json", action="store_true", help="Emit structured JSON output.")

    stack_parser = subparsers.add_parser("stack", help="Show the active rule stack.")
    stack_parser.add_argument("--with-evidence", action="store_true")
    stack_parser.add_argument("--scope", default="global", help="Scope to inspect.")
    stack_parser.add_argument("--rule-type", choices=["next_token", "next_kind"], default=None)
    stack_parser.add_argument("--json", action="store_true", help="Emit structured JSON output.")

    explain_parser = subparsers.add_parser("explain", help="Explain one rule with evidence, health, and history.")
    explain_parser.add_argument("rule_id", nargs="?", type=int, help="Rule id to inspect.")
    explain_parser.add_argument("--scope", default="global", help="Scope to inspect when resolving by signature.")
    explain_parser.add_argument("--rule-type", choices=["next_token", "next_kind"], default=None)
    explain_parser.add_argument(
        "--prefix-token",
        action="append",
        default=[],
        help="Repeat to provide the prefix tokens when resolving by signature.",
    )
    explain_parser.add_argument("--expected-token", default=None, help="Expected token when resolving by signature.")
    explain_parser.add_argument("--history-limit", type=int, default=10, help="Maximum history events to include.")
    explain_parser.add_argument("--json", action="store_true", help="Emit structured JSON output.")

    export_parser = subparsers.add_parser("export-scope", help="Export a scope snapshot as JSON.")
    export_parser.add_argument("--scope", default="global", help="Scope to export.")
    export_parser.add_argument("--output", default="-", help="Output path or '-' for stdout.")

    import_parser = subparsers.add_parser("import-scope", help="Import a scope snapshot from JSON.")
    import_parser.add_argument("path", help="Snapshot path or '-' for stdin.")
    import_parser.add_argument("--scope", default=None, help="Target scope override.")
    import_parser.add_argument("--replace-scope", action="store_true", help="Replace the target scope state and history before import.")
    import_parser.add_argument("--json", action="store_true", help="Emit structured JSON output.")

    compare_parser = subparsers.add_parser("compare", help="Compare two local scopes or exported snapshots.")
    compare_parser.add_argument("left", help="Left reference: scope name, scope:<name>, snapshot path, or snapshot:<path>.")
    compare_parser.add_argument("right", help="Right reference: scope name, scope:<name>, snapshot path, or snapshot:<path>.")
    compare_parser.add_argument("--rule-type", choices=["next_token", "next_kind"], default=None)
    compare_parser.add_argument("--limit", type=int, default=10, help="Maximum entries per text section.")
    compare_parser.add_argument("--json", action="store_true", help="Emit structured JSON output.")

    report_parser = subparsers.add_parser("report", help="Summarize one scope and the highest-priority next actions.")
    report_parser.add_argument("--scope", default="global", help="Scope to inspect.")
    report_parser.add_argument("--rule-type", choices=["next_token", "next_kind"], default=None)
    report_parser.add_argument("--triage-focus", choices=list(TRIAGE_FOCUS_CHOICES), default="auto", help="Proposal focus policy for report triage.")
    report_parser.add_argument("--stack-limit", type=int, default=10, help="Maximum adopted rules to include.")
    report_parser.add_argument("--proposal-limit", type=int, default=10, help="Maximum triage proposals to include.")
    report_parser.add_argument("--health-limit", type=int, default=10, help="Maximum health-attention rows to include.")
    report_parser.add_argument("--conflict-limit", type=int, default=10, help="Maximum conflict groups to include.")
    report_parser.add_argument("--history-limit", type=int, default=10, help="Maximum recent history events to include.")
    report_parser.add_argument("--json", action="store_true", help="Emit structured JSON output.")

    triage_parser = subparsers.add_parser("triage", help="Rank pending rules and suggest next actions.")
    triage_parser.add_argument("--scope", default="global", help="Scope to inspect.")
    triage_parser.add_argument("--rule-type", choices=["next_token", "next_kind"], default=None)
    triage_parser.add_argument("--recommendation", choices=list(TRIAGE_RECOMMENDATIONS), default=None)
    triage_parser.add_argument("--limit", type=int, default=None, help="Maximum number of proposals to emit.")
    triage_parser.add_argument("--all", action="store_true", help="Include shadowed proposals instead of only the frontier.")
    triage_parser.add_argument("--focus", choices=list(TRIAGE_FOCUS_CHOICES), default="auto", help="Proposal focus policy.")
    triage_parser.add_argument("--json", action="store_true", help="Emit structured JSON output.")

    apply_triage_parser = subparsers.add_parser("apply-triage", help="Apply triage recommendations in batch.")
    apply_triage_parser.add_argument("--scope", default="global", help="Scope to inspect.")
    apply_triage_parser.add_argument("--recommendation", choices=list(APPLYABLE_TRIAGE_RECOMMENDATIONS), default="adopt")
    apply_triage_parser.add_argument("--rule-type", choices=["next_token", "next_kind"], default=None)
    apply_triage_parser.add_argument("--limit", type=int, default=None, help="Maximum number of proposals to apply.")
    apply_triage_parser.add_argument("--all", action="store_true", help="Include shadowed proposals instead of only the frontier.")
    apply_triage_parser.add_argument("--focus", choices=list(TRIAGE_FOCUS_CHOICES), default="auto", help="Proposal focus policy.")
    apply_triage_parser.add_argument("--dry-run", action="store_true", help="Preview matching proposals without mutating the stack.")
    apply_triage_parser.add_argument("--actor", default=None, help="Actor label for the resulting decisions.")
    apply_triage_parser.add_argument("--source", default="triage", help="Decision source label.")
    apply_triage_parser.add_argument("--reason-prefix", default=None, help="Optional text to prepend to generated triage reasons.")
    apply_triage_parser.add_argument("--json", action="store_true", help="Emit structured JSON output.")

    history_parser = subparsers.add_parser("history", help="Show rule decision history.")
    history_parser.add_argument("--scope", default="global", help="Scope to inspect.")
    history_parser.add_argument("--rule-type", choices=["next_token", "next_kind"], default=None)
    history_parser.add_argument("--new-status", choices=["adopted", "rejected"], default=None)
    history_parser.add_argument("--limit", type=int, default=20, help="Maximum number of history events to emit.")
    history_parser.add_argument("--json", action="store_true", help="Emit structured JSON output.")

    govern_parser = subparsers.add_parser("govern", help="Show rule health and triage recommendations.")
    govern_parser.add_argument("--scope", default="global", help="Scope to inspect.")
    govern_parser.add_argument("--status", choices=["pending", "adopted", "rejected", "all"], default="adopted")
    govern_parser.add_argument("--rule-type", choices=["next_token", "next_kind"], default=None)
    govern_parser.add_argument("--recommendation", choices=list(RECOMMENDATION_CHOICES), default=None)
    govern_parser.add_argument("--json", action="store_true", help="Emit structured JSON output.")

    conflicts_parser = subparsers.add_parser("conflicts", help="Show competing rules with the same scope and prefix.")
    conflicts_parser.add_argument("--status", choices=["pending", "adopted", "rejected"], default=None)
    conflicts_parser.add_argument("--scope", default="global", help="Scope to inspect.")
    conflicts_parser.add_argument("--rule-type", choices=["next_token", "next_kind"], default=None)
    conflicts_parser.add_argument("--json", action="store_true", help="Emit structured JSON output.")

    graph_parser = subparsers.add_parser("graph", help="Build and render the transition graph.")
    graph_parser.add_argument("--format", choices=["mermaid", "table", "dot"], default="mermaid")
    graph_parser.add_argument("--scope", default="global", help="Scope to inspect.")
    graph_parser.add_argument("--layer", choices=["observed", "rules", "metasystem"], default="observed")
    graph_parser.add_argument("--rule-type", choices=["next_token", "next_kind"], default=None)
    graph_parser.add_argument("--status", choices=["pending", "adopted", "rejected"], default=None)
    graph_parser.add_argument("--decision-limit", type=int, default=20, help="Maximum history events to include in metasystem graphs.")
    graph_parser.add_argument("--json", action="store_true", help="Emit structured JSON output.")

    lint_parser = subparsers.add_parser("lint", help="Lint a file against adopted rules.")
    lint_parser.add_argument("path")
    lint_parser.add_argument("--label", default="<stdin>", help="Label to use when reading input from stdin via '-'.")
    lint_parser.add_argument("--scope", default="global", help="Scope to lint against.")
    lint_parser.add_argument("--json", action="store_true", help="Emit structured JSON output.")

    normalize_parser = subparsers.add_parser("normalize", help="Suggest or apply normalization from adopted rules.")
    normalize_parser.add_argument("path")
    normalize_parser.add_argument("--label", default="<stdin>", help="Label to use when reading input from stdin via '-'.")
    normalize_parser.add_argument("--apply", action="store_true", help="Emit normalized text to stdout.")
    normalize_parser.add_argument("--in-place", action="store_true", help="Rewrite the file in place.")
    normalize_parser.add_argument("--scope", default="global", help="Scope to normalize against.")
    normalize_parser.add_argument("--json", action="store_true", help="Emit structured JSON output.")

    session_parser = subparsers.add_parser("session", help="Process a live line stream and emit governance events.")
    session_parser.add_argument("--scope", default="global", help="Scope to lint against and optionally learn into.")
    session_parser.add_argument("--label", default="session", help="Base label for emitted events and learned artifacts.")
    session_parser.add_argument("--learn", action="store_true", help="Learn from the full stream after emitting line events.")
    session_parser.add_argument("--triage", action="store_true", help="Emit candidate triage after the stream is processed.")
    session_parser.add_argument(
        "--apply-triage",
        action="append",
        choices=list(APPLYABLE_TRIAGE_RECOMMENDATIONS),
        default=[],
        help="Apply matching triage recommendations after processing.",
    )
    session_parser.add_argument("--triage-focus", choices=list(TRIAGE_FOCUS_CHOICES), default="auto", help="Proposal focus policy.")
    session_parser.add_argument("--min-support", type=int, default=2)
    session_parser.add_argument("--min-confidence", type=float, default=0.75)
    session_parser.add_argument("--max-prefix", type=int, default=2)
    session_parser.add_argument("--format", choices=["jsonl", "text"], default="jsonl")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    db_path = Path(args.db)

    if args.command == "compare":
        try:
            if _compare_reference_needs_connection(args.left) or _compare_reference_needs_connection(args.right):
                with connect(db_path) as connection:
                    return _run_compare_command(connection, args)
            return _run_compare_command(None, args)
        except ValueError as exc:
            parser.error(str(exc))

    with connect(db_path) as connection:
        if args.command == "catch":
            try:
                inputs = _resolve_catch_inputs(args.paths, stdin_label=args.label)
            except ValueError as exc:
                parser.error(str(exc))
            count = catch_patterns(
                connection,
                inputs,
                scope=args.scope,
                replace_scope=args.replace_scope,
                min_support=args.min_support,
                min_confidence=args.min_confidence,
                max_prefix=args.max_prefix,
                keywords=args.keywords,
            )
            if args.json:
                _emit_json(
                    {
                        "scope": args.scope,
                        "replace_scope": bool(args.replace_scope),
                        "candidate_rule_count": count,
                        "input_labels": [item.label if isinstance(item, ArtifactInput) else str(item) for item in inputs],
                    }
                )
                return 0
            print(f"caught {count} candidate rules")
            return 0

        if args.command == "review":
            rows = list_rules(connection, args.status, scope=args.scope, rule_type=args.rule_type)
            if args.json:
                payload = {
                    "scope": args.scope,
                    "status": args.status,
                    "rule_type": args.rule_type,
                    "rules": [],
                }
                for row in rows:
                    item = serialize_rule_row(row)
                    if args.with_evidence:
                        item["evidence"] = [serialize_evidence_row(ev) for ev in fetch_evidence(connection, int(row["id"]))]
                    payload["rules"].append(item)
                _emit_json(payload)
                return 0
            if not rows:
                print("no rules")
                return 0
            for row in rows:
                print(_format_rule_row(row))
                if args.with_evidence:
                    for evidence in fetch_evidence(connection, int(row["id"])):
                        print(
                            f"  evidence {evidence['path']}:{evidence['line_no']} "
                            f"observed={evidence['observed_token']!r} context={evidence['context']!r}"
                        )
            return 0

        if args.command == "adopt":
            adopt_rules(
                connection,
                list(args.rule_ids),
                actor=args.actor,
                source=args.source,
                reason=args.reason,
            )
            if args.json:
                _emit_json(
                    {
                        "action": "adopt",
                        "rule_ids": list(args.rule_ids),
                        "count": len(args.rule_ids),
                        "actor": args.actor,
                        "source": args.source,
                        "reason": args.reason,
                    }
                )
                return 0
            print(f"adopted {len(args.rule_ids)} rule(s)")
            return 0

        if args.command == "reject":
            reject_rules(
                connection,
                list(args.rule_ids),
                actor=args.actor,
                source=args.source,
                reason=args.reason,
            )
            if args.json:
                _emit_json(
                    {
                        "action": "reject",
                        "rule_ids": list(args.rule_ids),
                        "count": len(args.rule_ids),
                        "actor": args.actor,
                        "source": args.source,
                        "reason": args.reason,
                    }
                )
                return 0
            print(f"rejected {len(args.rule_ids)} rule(s)")
            return 0

        if args.command == "stack":
            rows = list_rules(connection, "adopted", scope=args.scope, rule_type=args.rule_type)
            if args.json:
                payload = {
                    "scope": args.scope,
                    "rule_type": args.rule_type,
                    "rules": [],
                }
                for row in rows:
                    item = serialize_rule_row(row)
                    if args.with_evidence:
                        item["evidence"] = [serialize_evidence_row(ev) for ev in fetch_evidence(connection, int(row["id"]))]
                    payload["rules"].append(item)
                _emit_json(payload)
                return 0
            if not rows:
                print("no adopted rules")
                return 0
            for row in rows:
                print(_format_rule_row(row))
                if args.with_evidence:
                    for evidence in fetch_evidence(connection, int(row["id"])):
                        print(
                            f"  evidence {evidence['path']}:{evidence['line_no']} "
                            f"observed={evidence['observed_token']!r} context={evidence['context']!r}"
                        )
            return 0

        if args.command == "explain":
            try:
                payload = explain_rule(
                    connection,
                    rule_id=args.rule_id,
                    scope=args.scope,
                    rule_type=args.rule_type,
                    prefix_tokens=tuple(args.prefix_token),
                    expected_token=args.expected_token,
                    history_limit=args.history_limit,
                )
            except ValueError as exc:
                parser.error(str(exc))
            if args.json:
                _emit_json(payload)
                return 0
            print(render_rule_explanation(payload))
            return 0

        if args.command == "export-scope":
            payload = export_scope_snapshot(connection, scope=args.scope)
            rendered = json.dumps(payload, indent=2, sort_keys=True)
            if args.output == "-":
                sys.stdout.write(rendered)
                sys.stdout.write("\n")
                return 0
            Path(args.output).write_text(rendered + "\n", encoding="utf-8")
            print(f"exported {args.scope} to {args.output}")
            return 0

        if args.command == "import-scope":
            snapshot = _read_json_path_or_stdin(args.path)
            target_scope = str(args.scope) if args.scope is not None else str(snapshot.get("scope", "global"))
            summary = import_scope_snapshot(
                connection,
                snapshot,
                target_scope=target_scope,
                replace_scope_state=bool(args.replace_scope),
            )
            if args.json:
                _emit_json(summary)
                return 0
            print(
                f"imported {summary['rule_count']} rule(s), {summary['artifact_count']} artifact(s), "
                f"and {summary['decision_count']} decision(s) into scope {summary['target_scope']}"
            )
            return 0

        if args.command == "report":
            payload = build_scope_report(
                connection,
                scope=args.scope,
                rule_type=args.rule_type,
                triage_focus=args.triage_focus,
                stack_limit=args.stack_limit,
                proposal_limit=args.proposal_limit,
                health_limit=args.health_limit,
                conflict_limit=args.conflict_limit,
                history_limit=args.history_limit,
            )
            if args.json:
                _emit_json(payload)
                return 0
            print(render_scope_report(payload))
            return 0

        if args.command == "triage":
            items = triage_pending_rules(
                connection,
                scope=args.scope,
                rule_type=args.rule_type,
                recommendation=args.recommendation,
                limit=args.limit,
                frontier_only=not args.all,
                focus=args.focus,
            )
            if args.json:
                _emit_json(
                    {
                        "scope": args.scope,
                        "rule_type": args.rule_type,
                        "recommendation": args.recommendation,
                        "limit": args.limit,
                        "frontier_only": not args.all,
                        "focus": args.focus,
                        "rules": [serialize_rule_proposal(item) for item in items],
                    }
                )
                return 0
            if not items:
                print("no pending rules")
                return 0
            for item in items:
                print(_format_rule_proposal(item))
            return 0

        if args.command == "apply-triage":
            items = apply_triage_recommendations(
                connection,
                scope=args.scope,
                recommendation=args.recommendation,
                rule_type=args.rule_type,
                limit=args.limit,
                frontier_only=not args.all,
                focus=args.focus,
                dry_run=bool(args.dry_run),
                actor=args.actor,
                source=args.source,
                reason_prefix=args.reason_prefix,
            )
            if args.json:
                _emit_json(
                    {
                        "scope": args.scope,
                        "recommendation": args.recommendation,
                        "rule_type": args.rule_type,
                        "limit": args.limit,
                        "frontier_only": not args.all,
                        "focus": args.focus,
                        "dry_run": bool(args.dry_run),
                        "actor": args.actor,
                        "source": args.source,
                        "reason_prefix": args.reason_prefix,
                        "applied_count": 0 if args.dry_run else len(items),
                        "applied_rule_ids": [] if args.dry_run else [item.rule_id for item in items],
                        "rules": [serialize_rule_proposal(item) for item in items],
                    }
                )
                return 0
            if not items:
                print("no triage matches")
                return 0
            verb = "would apply" if args.dry_run else "applied"
            print(f"{verb} {len(items)} {args.recommendation} decision(s)")
            for item in items:
                print(_format_rule_proposal(item))
            return 0

        if args.command == "history":
            items = read_rule_history(
                connection,
                scope=args.scope,
                rule_type=args.rule_type,
                new_status=args.new_status,
                limit=args.limit,
            )
            if args.json:
                _emit_json(
                    {
                        "scope": args.scope,
                        "rule_type": args.rule_type,
                        "new_status": args.new_status,
                        "limit": args.limit,
                        "events": [serialize_rule_decision(item) for item in items],
                    }
                )
                return 0
            if not items:
                print("no history")
                return 0
            for item in items:
                print(_format_rule_decision(item))
            return 0

        if args.command == "govern":
            status = None if args.status == "all" else args.status
            items = list_rule_health(
                connection,
                scope=args.scope,
                status=status,
                rule_type=args.rule_type,
                recommendation=args.recommendation,
            )
            if args.json:
                _emit_json(
                    {
                        "scope": args.scope,
                        "status": args.status,
                        "rule_type": args.rule_type,
                        "recommendation": args.recommendation,
                        "rules": [serialize_rule_health(item) for item in items],
                    }
                )
                return 0
            if not items:
                print("no rules")
                return 0
            for item in items:
                print(_format_rule_health(item))
            return 0

        if args.command == "conflicts":
            rows = list_rules(connection, args.status, scope=args.scope, rule_type=args.rule_type)
            conflicts = build_conflict_groups(rows)
            if args.json:
                _emit_json(
                    {
                        "scope": args.scope,
                        "status": args.status,
                        "rule_type": args.rule_type,
                        "conflicts": conflicts,
                    }
                )
                return 0
            if not conflicts:
                print("no conflicts")
                return 0
            for conflict in conflicts:
                print(
                    f"scope={conflict['scope']} rule_type={conflict['rule_type']} "
                    f"prefix={conflict['prefix_display']!r} options={conflict['expected_options']!r}"
                )
                for member in conflict["members"]:
                    print(
                        f"  [{member['id']}] {member['status']} "
                        f"{member['expected_display']!r} support={member['support']}/{member['total']} "
                        f"confidence={member['confidence']:.2f}"
                    )
            return 0

        if args.command == "graph":
            graph = build_transition_graph(
                connection,
                scope=args.scope,
                layer=args.layer,
                rule_type=args.rule_type,
                status=args.status,
                decision_limit=args.decision_limit,
            )
            rendered = render_transition_graph(
                connection,
                scope=args.scope,
                format_name=args.format,
                layer=args.layer,
                rule_type=args.rule_type,
                status=args.status,
                decision_limit=args.decision_limit,
            )
            if args.json:
                if args.layer == "observed":
                    items = [serialize_observed_transition_row(row) for row in list_observed_transitions(connection, scope=args.scope)]
                elif args.layer == "rules":
                    items = [serialize_rule_row(row) for row in list_rules(connection, args.status, scope=args.scope, rule_type=args.rule_type)]
                else:
                    items = list(graph["edges"])
                _emit_json(
                    {
                        "scope": args.scope,
                        "layer": args.layer,
                        "rule_type": args.rule_type,
                        "status": args.status,
                        "decision_limit": args.decision_limit,
                        "format": args.format,
                        "items": items,
                        "graph": graph,
                        "summary": graph["summary"],
                        "rendered": rendered,
                    }
                )
                return 0
            print(rendered)
            return 0

        if args.command == "lint":
            violations = _lint_from_path_or_stdin(connection, args.path, stdin_label=args.label, scope=args.scope)
            if args.json:
                _emit_json(
                    {
                        "scope": args.scope,
                        "path": args.path,
                        "label": args.label if args.path == "-" else args.path,
                        "violations": [serialize_violation(violation) for violation in violations],
                    }
                )
                return 1 if violations else 0
            if not violations:
                print("clean")
                return 0
            for violation in violations:
                print(
                    f"{violation.path}:{violation.line_no} [{violation.verdict}] rule={violation.rule_id} "
                    f"type={violation.rule_type} "
                    f"expected={display_token(violation.rule_type, violation.expected_token)!r} "
                    f"found={violation.found_token!r} "
                    f"after={display_prefix(violation.rule_type, violation.prefix)!r}"
                )
                print(f"  context: {violation.context}")
            return 1

        if args.command == "normalize":
            if args.in_place and args.path == "-":
                parser.error("--in-place cannot be used with stdin")
            text, label, suggestions = _normalize_inputs(connection, args.path, stdin_label=args.label, scope=args.scope)
            normalized_text = apply_normalization(text, suggestions)
            if args.json:
                changed = normalized_text != text
                if args.in_place and changed:
                    Path(args.path).write_text(normalized_text, encoding="utf-8")
                _emit_json(
                    {
                        "scope": args.scope,
                        "label": label,
                        "apply": bool(args.apply),
                        "in_place": bool(args.in_place),
                        "changed": changed,
                        "suggestions": [serialize_suggestion(suggestion) for suggestion in suggestions],
                        "normalized_text": normalized_text if args.apply or args.path == "-" else None,
                    }
                )
                return 1 if suggestions and not args.in_place and not args.apply else 0
            if not suggestions:
                print("clean")
                return 0
            if args.in_place:
                Path(args.path).write_text(normalized_text, encoding="utf-8")
                print(f"normalized {args.path}")
                return 0
            if args.apply:
                sys.stdout.write(normalized_text)
                return 0
            for suggestion in suggestions:
                action = _format_normalization_action(suggestion)
                print(f"{label}:{suggestion.line_no} {action}")
                print(f"  reason: {suggestion.reason}")
            return 1

        if args.command == "session":
            events = process_session_stream(
                connection,
                sys.stdin,
                scope=args.scope,
                label=args.label,
                learn=bool(args.learn),
                triage=bool(args.triage),
                apply_triage=tuple(args.apply_triage),
                triage_focus=args.triage_focus,
                min_support=args.min_support,
                min_confidence=args.min_confidence,
                max_prefix=args.max_prefix,
            )
            if args.format == "jsonl":
                for event in events:
                    _emit_json_line(event)
                return 0 if events[-1]["violation_count"] == 0 else 1
            for event in events:
                if event["event"] == "summary":
                    print(
                        f"summary scope={event['scope']} label={event['label']} "
                        f"lines={event['line_count']} violations={event['violation_count']} "
                        f"learn={event['learn']} candidate_rules={event['candidate_rule_count']} "
                        f"triage={event['triage_count']}"
                    )
                    continue
                if event["event"] == "triage":
                    print(
                        f"triage scope={event['scope']} label={event['label']} "
                        f"focus={event['focus']} proposals={event['proposal_count']}"
                    )
                    for rule in event["rules"]:
                        print(
                            f"  [{rule['rule_id']}] recommend={rule['recommendation']} "
                            f"{rule['rule_type']} {rule['prefix_display']!r} -> {rule['expected_display']!r}"
                        )
                    continue
                if event["event"] == "apply_triage":
                    print(
                        f"apply-triage scope={event['scope']} label={event['label']} "
                        f"focus={event['focus']} recommendation={event['recommendation']} applied={event['applied_count']}"
                    )
                    continue
                status = "changed" if event["changed"] else "clean"
                if event["violations"]:
                    status = "violation"
                print(f"[{event['stream_line_no']}] {status}: {event['input']}")
                for violation in event["violations"]:
                    print(
                        f"  rule={violation['rule_id']} type={violation['rule_type']} "
                        f"expected={violation['expected_display']!r} "
                        f"after={violation['prefix_display']!r}"
                    )
            return 0 if events[-1]["violation_count"] == 0 else 1

    return 0


def _run_compare_command(connection: Connection | None, args: argparse.Namespace) -> int:
    stdin_state = {"consumed": False}
    left_source, left_snapshot = _load_compare_reference(connection, args.left, stdin_state=stdin_state)
    right_source, right_snapshot = _load_compare_reference(connection, args.right, stdin_state=stdin_state)
    report = compare_scope_states(
        left_snapshot,
        right_snapshot,
        left_source=left_source,
        right_source=right_source,
        rule_type=args.rule_type,
    )
    if args.json:
        _emit_json(report)
        return 0
    print(render_compare_report(report, limit=args.limit))
    return 0


def _format_rule_row(row: object) -> str:
    item = serialize_rule_row(row)
    return (
        f"[{item['id']}] scope={item['scope']} {item['status']} {item['rule_type']} "
        f"{item['prefix_display']!r} -> {item['expected_display']!r} "
        f"support={item['support']}/{item['total']} "
        f"confidence={item['confidence']:.2f}"
    )


def _format_rule_health(health: object) -> str:
    item = serialize_rule_health(health)
    return (
        f"[{item['id']}] scope={item['scope']} {item['status']} {item['rule_type']} "
        f"{item['prefix_display']!r} -> {item['expected_display']!r} "
        f"learned={item['support']}/{item['total']} confidence={item['confidence']:.2f} "
        f"evals={item['evaluation_count']} hits={item['hit_count']} "
        f"violations={item['violation_count']} violation_rate={item['violation_rate']:.2f} "
        f"recommendation={item['recommendation']}"
    )


def _format_rule_proposal(proposal: object) -> str:
    item = serialize_rule_proposal(proposal)
    reason_text = "; ".join(item["reasons"])
    return (
        f"[{item['id']}] scope={item['scope']} recommend={item['recommendation']} {item['rule_type']} "
        f"{item['prefix_display']!r} -> {item['expected_display']!r} "
        f"support={item['support']}/{item['total']} confidence={item['confidence']:.2f} "
        f"reasons={reason_text}"
    )


def _format_rule_decision(decision: object) -> str:
    item = serialize_rule_decision(decision)
    auto_text = " automatic" if item["automatic"] else ""
    reason_text = f" reason={item['reason']!r}" if item["reason"] is not None else ""
    source_text = f" source={item['source']!r}" if item["source"] is not None else ""
    actor_text = f" actor={item['actor']!r}" if item["actor"] is not None else ""
    return (
        f"[{item['id']}] {item['created_at']} scope={item['scope']}{auto_text} "
        f"{item['previous_status']} -> {item['new_status']} "
        f"{item['rule_type']} {item['prefix_display']!r} -> {item['expected_display']!r}"
        f"{actor_text}{source_text}{reason_text}"
    )


def _format_normalization_action(suggestion: object) -> str:
    candidate_tokens = list(getattr(suggestion, "candidate_tokens", ()))
    suggested_action = str(getattr(suggestion, "suggested_action", "replace"))
    replacement = getattr(suggestion, "replacement", None)
    found_token = str(getattr(suggestion, "found_token"))
    expected_token = str(getattr(suggestion, "expected_token"))

    if suggested_action == "replace" and replacement is not None:
        return f"replace {found_token!r} with {replacement!r}"
    if suggested_action == "insert":
        if replacement is not None:
            return f"insert {replacement!r}"
        if candidate_tokens:
            return f"consider inserting one of {candidate_tokens!r}"
        return f"consider inserting {expected_token!r}"
    if suggested_action == "insert_before":
        if candidate_tokens:
            return f"consider inserting one of {candidate_tokens!r} before {found_token!r}"
        return f"consider inserting {expected_token!r} before {found_token!r}"
    if suggested_action == "remove":
        return f"remove {found_token!r}"
    return f"review {found_token!r} against {expected_token!r}"


def _resolve_catch_inputs(paths: list[str], *, stdin_label: str) -> list[Path | ArtifactInput]:
    if paths.count("-") > 1:
        raise ValueError("stdin '-' may only appear once")

    inputs: list[Path | ArtifactInput] = []
    stdin_consumed = False
    for raw_path in paths:
        if raw_path == "-":
            if stdin_consumed:
                raise ValueError("stdin '-' may only appear once")
            stdin_consumed = True
            inputs.append(ArtifactInput(label=stdin_label, content=sys.stdin.read()))
        else:
            inputs.append(Path(raw_path))
    return inputs


def _lint_from_path_or_stdin(connection: Connection, raw_path: str, *, stdin_label: str, scope: str):
    if raw_path == "-":
        return lint_text(connection, sys.stdin.read(), label=stdin_label, scope=scope)
    return lint_path(connection, Path(raw_path), scope=scope)


def _normalize_inputs(connection: Connection, raw_path: str, *, stdin_label: str, scope: str):
    if raw_path == "-":
        text = sys.stdin.read()
        label = stdin_label
        suggestions = build_normalization_suggestions(lint_text(connection, text, label=label, scope=scope))
        return text, label, suggestions

    path = Path(raw_path)
    text = path.read_text(encoding="utf-8")
    suggestions = build_normalization_suggestions(lint_path(connection, path, scope=scope))
    return text, str(path), suggestions


def _compare_reference_needs_connection(reference: str) -> bool:
    if reference.startswith("scope:"):
        return True
    if reference.startswith("snapshot:"):
        return False
    if reference == "-":
        return False
    path = Path(reference)
    if path.exists() or path.suffix == ".json":
        return False
    return True


def _load_compare_reference(
    connection: Connection | None,
    reference: str,
    *,
    stdin_state: dict[str, bool],
) -> tuple[dict[str, str], dict[str, object]]:
    if reference.startswith("scope:"):
        scope = reference.removeprefix("scope:")
        if connection is None:
            raise ValueError(f"Reference {reference!r} requires a database connection")
        return {"reference": f"scope:{scope}", "kind": "scope"}, export_scope_snapshot(connection, scope=scope)

    if reference.startswith("snapshot:"):
        path = reference.removeprefix("snapshot:")
        snapshot = _read_json_path_or_stdin_once(path, stdin_state=stdin_state)
        return {"reference": f"snapshot:{path}", "kind": "snapshot"}, snapshot

    if reference == "-":
        snapshot = _read_json_path_or_stdin_once(reference, stdin_state=stdin_state)
        return {"reference": "snapshot:-", "kind": "snapshot"}, snapshot

    path = Path(reference)
    if path.exists() or path.suffix == ".json":
        snapshot = _read_json_path_or_stdin_once(reference, stdin_state=stdin_state)
        return {"reference": f"snapshot:{reference}", "kind": "snapshot"}, snapshot

    if connection is None:
        raise ValueError(f"Reference {reference!r} requires a database connection")
    return {"reference": f"scope:{reference}", "kind": "scope"}, export_scope_snapshot(connection, scope=reference)


def _read_json_path_or_stdin(path: str):
    if path == "-":
        return json.loads(sys.stdin.read())
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _read_json_path_or_stdin_once(path: str, *, stdin_state: dict[str, bool]):
    if path != "-":
        return _read_json_path_or_stdin(path)
    if stdin_state["consumed"]:
        raise ValueError("stdin snapshot '-' may only appear once")
    stdin_state["consumed"] = True
    return _read_json_path_or_stdin(path)


def _emit_json(payload: object) -> None:
    sys.stdout.write(json.dumps(payload, indent=2, sort_keys=True))
    sys.stdout.write("\n")


def _emit_json_line(payload: object) -> None:
    sys.stdout.write(json.dumps(payload, sort_keys=True))
    sys.stdout.write("\n")


if __name__ == "__main__":
    raise SystemExit(main())
