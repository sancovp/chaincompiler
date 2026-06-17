from __future__ import annotations

from contextlib import redirect_stdout
import io
import json
from pathlib import Path

from rulecatcher.cli import main
from rulecatcher.db import connect, list_rules
from rulecatcher.engine import adopt_rules, catch_patterns
from rulecatcher.graphing import render_transition_graph
from rulecatcher.linting import apply_normalization, build_normalization_suggestions, lint_path


def write_file(path: Path, text: str) -> Path:
    path.write_text(text, encoding="utf-8")
    return path


def test_catch_persists_candidate_rules(tmp_path: Path) -> None:
    db_path = tmp_path / "rules.db"
    corpus = write_file(
        tmp_path / "corpus.txt",
        "state => open\nstate => open\nstate => open\nmode => safe\nmode => safe\n",
    )

    with connect(db_path) as connection:
        count = catch_patterns(connection, [corpus], min_support=2, min_confidence=0.8, max_prefix=2)
        rows = list_rules(connection)

    assert count >= 2
    assert any("open" == row["expected_token"] for row in rows)
    assert any("safe" == row["expected_token"] for row in rows)


def test_keywords_separate_keyword_from_identifier_and_persist_to_lint(tmp_path: Path) -> None:
    # Two line-forms share the [<BOS>, IDENTIFIER] prefix when 'state' is just an
    # identifier: transitions ("name --> x") and declarations ("state x <<c>>").
    # Declaring 'state' as a keyword splits them, so the transition spine rule
    # becomes 1.00, and the keyword set must persist so lint classifies the same way.
    db_path = tmp_path / "rules.db"
    corpus = write_file(
        tmp_path / "corpus.txt",
        "a --> b\nc --> d\ne --> f\nstate g <<c>>\nstate h <<c>>\n",
    )

    with connect(db_path) as connection:
        catch_patterns(
            connection,
            [corpus],
            scope="csgn",
            min_support=2,
            min_confidence=0.8,
            max_prefix=2,
            keywords=["state"],
        )
        rows = list_rules(connection, "pending", scope="csgn")
        spine = next(
            row
            for row in rows
            if row["rule_type"] == "next_kind"
            and json.loads(row["prefix_json"]) == ["<BOS>", "IDENTIFIER"]
            and row["expected_token"] == "OPERATOR"
        )
        # Without keyword separation this would be 3/5 (0.6); with it, 3/3 (1.0).
        assert spine["support"] == spine["total"]
        assert float(spine["confidence"]) == 1.0
        adopt_rules(connection, [int(spine["id"])])

        # lint reloads the scope's keywords: a real declaration stays clean,
        # a transition missing its arrow is flagged.
        clean = lint_path(connection, write_file(tmp_path / "ok.txt", "state z <<c>>\n"), scope="csgn")
        broken = lint_path(connection, write_file(tmp_path / "bad.txt", "a b\n"), scope="csgn")

    assert clean == []
    assert len(broken) == 1
    assert broken[0].expected_token == "OPERATOR"


def test_adopted_rule_lints_broken_next_token(tmp_path: Path) -> None:
    db_path = tmp_path / "rules.db"
    corpus = write_file(
        tmp_path / "corpus.txt",
        "state => open\nstate => open\nstate => open\n",
    )
    broken = write_file(
        tmp_path / "broken.txt",
        "state => closed\n",
    )

    with connect(db_path) as connection:
        catch_patterns(connection, [corpus], min_support=2, min_confidence=0.8, max_prefix=2)
        rows = list_rules(connection, "pending")
        target_rule = next(row for row in rows if row["expected_token"] == "open")
        adopt_rules(connection, [int(target_rule["id"])])
        violations = lint_path(connection, broken)

    assert len(violations) == 1
    assert violations[0].expected_token == "open"
    assert violations[0].found_token == "closed"


def test_normalize_suggests_expected_token_and_can_apply(tmp_path: Path) -> None:
    db_path = tmp_path / "rules.db"
    corpus = write_file(
        tmp_path / "corpus.txt",
        "mode => safe\nmode => safe\nmode => safe\n",
    )
    broken = write_file(
        tmp_path / "broken.txt",
        "mode => risky\n",
    )

    with connect(db_path) as connection:
        catch_patterns(connection, [corpus], min_support=2, min_confidence=0.8, max_prefix=2)
        rows = list_rules(connection, "pending")
        target_rule = next(row for row in rows if row["expected_token"] == "safe")
        adopt_rules(connection, [int(target_rule["id"])])
        violations = lint_path(connection, broken)
        suggestions = build_normalization_suggestions(violations)

    assert suggestions[0].replacement == "safe"
    normalized = apply_normalization(broken.read_text(encoding="utf-8"), suggestions)
    assert normalized == "mode => safe\n"


def test_graph_renders_observed_and_adopted_transitions(tmp_path: Path) -> None:
    db_path = tmp_path / "rules.db"
    corpus = write_file(
        tmp_path / "corpus.txt",
        "state => open\nstate => open\nmode => safe\nmode => safe\n",
    )

    with connect(db_path) as connection:
        catch_patterns(connection, [corpus], min_support=2, min_confidence=0.8, max_prefix=2)
        rows = list_rules(connection, "pending")
        target_rule = next(row for row in rows if row["expected_token"] == "open")
        adopt_rules(connection, [int(target_rule["id"])])
        graph = render_transition_graph(connection, format_name="table")

    assert "['state', '=>'] -> 'open'" in graph
    assert "status=adopted" in graph


def test_cli_supports_stdin_catch_and_lint(monkeypatch, tmp_path: Path) -> None:
    db_path = tmp_path / "rules.db"

    monkeypatch.setattr("sys.stdin", io.StringIO("state => open\nstate => open\nstate => open\n"))
    stdout = io.StringIO()
    with redirect_stdout(stdout):
        exit_code = main(["--db", str(db_path), "catch", "-", "--label", "stdin-corpus"])
    assert exit_code == 0
    assert "caught" in stdout.getvalue()

    with connect(db_path) as connection:
        rows = list_rules(connection, "pending")
        target_rule = next(row for row in rows if row["expected_token"] == "open")
        adopt_rules(connection, [int(target_rule["id"])])

    monkeypatch.setattr("sys.stdin", io.StringIO("state => closed\n"))
    stdout = io.StringIO()
    with redirect_stdout(stdout):
        exit_code = main(["--db", str(db_path), "lint", "-", "--label", "incoming"])
    assert exit_code == 1
    assert "incoming:1" in stdout.getvalue()


def test_cli_normalize_in_place_rewrites_file(tmp_path: Path) -> None:
    db_path = tmp_path / "rules.db"
    corpus = write_file(
        tmp_path / "corpus.txt",
        "mode => safe\nmode => safe\nmode => safe\n",
    )
    broken = write_file(
        tmp_path / "broken.txt",
        "mode => risky\n",
    )

    with connect(db_path) as connection:
        catch_patterns(connection, [corpus], min_support=2, min_confidence=0.8, max_prefix=2)
        rows = list_rules(connection, "pending")
        target_rule = next(row for row in rows if row["expected_token"] == "safe")
        adopt_rules(connection, [int(target_rule["id"])])

    stdout = io.StringIO()
    with redirect_stdout(stdout):
        exit_code = main(["--db", str(db_path), "normalize", str(broken), "--in-place"])

    assert exit_code == 0
    assert broken.read_text(encoding="utf-8") == "mode => safe\n"
    assert "normalized" in stdout.getvalue()


def test_scopes_isolate_rule_stacks(tmp_path: Path) -> None:
    db_path = tmp_path / "rules.db"
    alpha = write_file(
        tmp_path / "alpha.txt",
        "state => open\nstate => open\nstate => open\n",
    )
    beta = write_file(
        tmp_path / "beta.txt",
        "state => closed\nstate => closed\nstate => closed\n",
    )
    sample = write_file(
        tmp_path / "sample.txt",
        "state => closed\n",
    )

    with connect(db_path) as connection:
        catch_patterns(connection, [alpha], scope="alpha", min_support=2, min_confidence=0.8, max_prefix=2)
        catch_patterns(connection, [beta], scope="beta", min_support=2, min_confidence=0.8, max_prefix=2)

        alpha_rule = next(row for row in list_rules(connection, "pending", scope="alpha") if row["expected_token"] == "open")
        beta_rule = next(row for row in list_rules(connection, "pending", scope="beta") if row["expected_token"] == "closed")
        adopt_rules(connection, [int(alpha_rule["id"]), int(beta_rule["id"])])

        alpha_violations = lint_path(connection, sample, scope="alpha")
        beta_violations = lint_path(connection, sample, scope="beta")
        alpha_graph = render_transition_graph(connection, scope="alpha", format_name="table")
        beta_graph = render_transition_graph(connection, scope="beta", format_name="table")

    assert len(alpha_violations) == 1
    assert alpha_violations[0].expected_token == "open"
    assert beta_violations == []
    assert "-> 'open'" in alpha_graph
    assert "-> 'closed'" in beta_graph


def test_kind_rules_catch_novel_structural_syntax_break(tmp_path: Path) -> None:
    db_path = tmp_path / "rules.db"
    corpus = write_file(
        tmp_path / "corpus.txt",
        "state => open\nmode => safe\nshape => square\n",
    )
    novel = write_file(
        tmp_path / "novel.txt",
        "door closed\n",
    )

    with connect(db_path) as connection:
        catch_patterns(connection, [corpus], scope="syntax", min_support=2, min_confidence=0.8, max_prefix=2)
        kind_rule = next(
            row
            for row in list_rules(connection, "pending", scope="syntax")
            if row["rule_type"] == "next_kind" and row["expected_token"] == "OPERATOR"
        )
        adopt_rules(connection, [int(kind_rule["id"])])
        violations = lint_path(connection, novel, scope="syntax")
        suggestions = build_normalization_suggestions(violations)

    assert len(violations) == 1
    assert violations[0].rule_type == "next_kind"
    assert violations[0].expected_token == "OPERATOR"
    assert violations[0].found_kind == "IDENTIFIER"
    assert suggestions[0].replacement is None
    assert suggestions[0].candidate_tokens == ("=>",)
    assert suggestions[0].suggested_action == "insert_before"
    assert "<OPERATOR>" in suggestions[0].reason
    assert "['=>']" in suggestions[0].reason


def test_replace_scope_discards_old_rules(tmp_path: Path) -> None:
    db_path = tmp_path / "rules.db"
    first = write_file(
        tmp_path / "first.txt",
        "state => open\nstate => open\nstate => open\n",
    )
    second = write_file(
        tmp_path / "second.txt",
        "state => closed\nstate => closed\nstate => closed\n",
    )

    with connect(db_path) as connection:
        catch_patterns(connection, [first], scope="alpha", replace_scope=True, min_support=2, min_confidence=0.8, max_prefix=2)
        first_rules = list_rules(connection, "pending", scope="alpha")
        assert any(row["expected_token"] == "open" for row in first_rules)

        catch_patterns(connection, [second], scope="alpha", replace_scope=True, min_support=2, min_confidence=0.8, max_prefix=2)
        second_rules = list_rules(connection, "pending", scope="alpha")

    assert any(row["expected_token"] == "closed" for row in second_rules)
    assert not any(row["expected_token"] == "open" and row["rule_type"] == "next_token" for row in second_rules)


def test_rule_graph_can_render_kind_rules(tmp_path: Path) -> None:
    db_path = tmp_path / "rules.db"
    corpus = write_file(
        tmp_path / "corpus.txt",
        "state => open\nmode => safe\nshape => square\n",
    )

    with connect(db_path) as connection:
        catch_patterns(connection, [corpus], scope="syntax", replace_scope=True, min_support=2, min_confidence=0.8, max_prefix=2)
        kind_rule = next(
            row
            for row in list_rules(connection, "pending", scope="syntax", rule_type="next_kind")
            if row["expected_token"] == "OPERATOR"
        )
        adopt_rules(connection, [int(kind_rule["id"])])
        graph = render_transition_graph(
            connection,
            scope="syntax",
            layer="rules",
            rule_type="next_kind",
            format_name="table",
        )

    assert "<IDENTIFIER>" in graph
    assert "<OPERATOR>" in graph
    assert "status=adopted" in graph


def test_metasystem_graph_table_includes_observed_rules_and_history(tmp_path: Path) -> None:
    db_path = tmp_path / "rules.db"
    corpus = write_file(
        tmp_path / "corpus.txt",
        "state => open\nstate => open\nstate => open\n",
    )
    broken = write_file(
        tmp_path / "broken.txt",
        "state => closed\n",
    )

    with connect(db_path) as connection:
        catch_patterns(connection, [corpus], scope="alpha", replace_scope=True, min_support=2, min_confidence=0.8, max_prefix=2)
        target_rule = next(row for row in list_rules(connection, "pending", scope="alpha", rule_type="next_token") if row["expected_token"] == "open")
        adopt_rules(connection, [int(target_rule["id"])], actor="silas", source="bootstrap", reason="stable syntax")
        lint_path(connection, broken, scope="alpha")
        graph = render_transition_graph(connection, scope="alpha", layer="metasystem", format_name="table")

    assert "observed 'state =>' -> 'open'" in graph
    assert "expects 'rule#" in graph
    assert "health=watch" in graph
    assert "decision 'decision#" in graph


def test_graph_json_emits_metasystem_payload_with_nodes_and_edges(tmp_path: Path) -> None:
    db_path = tmp_path / "rules.db"
    corpus = write_file(
        tmp_path / "corpus.txt",
        "state => open\nstate => open\nstate => open\n",
    )
    broken = write_file(
        tmp_path / "broken.txt",
        "state => closed\n",
    )

    with connect(db_path) as connection:
        catch_patterns(connection, [corpus], scope="alpha", replace_scope=True, min_support=2, min_confidence=0.8, max_prefix=2)
        target_rule = next(row for row in list_rules(connection, "pending", scope="alpha", rule_type="next_token") if row["expected_token"] == "open")
        adopt_rules(connection, [int(target_rule["id"])], actor="silas", source="bootstrap", reason="portable core")
        lint_path(connection, broken, scope="alpha")

    stdout = io.StringIO()
    with redirect_stdout(stdout):
        exit_code = main(
            [
                "--db",
                str(db_path),
                "graph",
                "--scope",
                "alpha",
                "--layer",
                "metasystem",
                "--format",
                "dot",
                "--json",
            ]
        )

    assert exit_code == 0
    payload = json.loads(stdout.getvalue())
    assert payload["layer"] == "metasystem"
    assert payload["summary"]["observed_transition_count"] >= 1
    assert payload["rendered"].startswith("digraph rulecatcher")

    rule_node = next(
        node
        for node in payload["graph"]["nodes"]
        if node["kind"] == "rule" and node["expected_display"] == "open"
    )
    assert rule_node["health"]["violation_count"] == 1
    assert rule_node["health"]["recommendation"] == "watch"

    decision_edge = next(
        edge
        for edge in payload["graph"]["edges"]
        if edge["kind"] == "decision" and edge["new_status"] == "adopted"
    )
    assert decision_edge["actor"] == "silas"
    assert decision_edge["decision_source"] == "bootstrap"


def test_report_json_summarizes_scope_and_next_actions(tmp_path: Path) -> None:
    db_path = tmp_path / "rules.db"
    corpus = write_file(
        tmp_path / "corpus.txt",
        "state => open\nstate => open\nstate => open\n",
    )
    broken = write_file(
        tmp_path / "broken.txt",
        "state => closed\n",
    )

    with connect(db_path) as connection:
        catch_patterns(connection, [corpus], scope="alpha", replace_scope=True, min_support=2, min_confidence=0.8, max_prefix=2)
        target_rule = next(row for row in list_rules(connection, "pending", scope="alpha", rule_type="next_token") if row["expected_token"] == "open")
        adopt_rules(connection, [int(target_rule["id"])], actor="silas", source="bootstrap")
        lint_path(connection, broken, scope="alpha")

    stdout = io.StringIO()
    with redirect_stdout(stdout):
        exit_code = main(["--db", str(db_path), "report", "--scope", "alpha", "--json"])

    assert exit_code == 0
    payload = json.loads(stdout.getvalue())
    assert payload["summary"]["artifact_count"] == 1
    assert payload["summary"]["adopted_rule_count"] >= 1
    assert payload["summary"]["triage_counts"]["adopt"] >= 1
    assert payload["summary"]["health_counts"]["watch"] >= 1
    assert payload["stack"]
    assert payload["triage"]["rules"]
    assert any(action["kind"] == "adopt_pending_rules" for action in payload["next_actions"])
    assert any(action["kind"] == "monitor_active_rules" for action in payload["next_actions"])


def test_report_json_flags_scope_bootstrap_when_no_adopted_rules_exist(tmp_path: Path) -> None:
    db_path = tmp_path / "rules.db"
    corpus = write_file(
        tmp_path / "corpus.txt",
        "state => open\nstate => open\nstate => open\n",
    )

    with connect(db_path) as connection:
        catch_patterns(connection, [corpus], scope="alpha", replace_scope=True, min_support=2, min_confidence=0.8, max_prefix=2)

    stdout = io.StringIO()
    with redirect_stdout(stdout):
        exit_code = main(["--db", str(db_path), "report", "--scope", "alpha", "--json"])

    assert exit_code == 0
    payload = json.loads(stdout.getvalue())
    bootstrap_action = next(action for action in payload["next_actions"] if action["kind"] == "bootstrap_stack")
    assert bootstrap_action["count"] >= 1


def test_report_text_includes_operational_sections(tmp_path: Path) -> None:
    db_path = tmp_path / "rules.db"
    corpus = write_file(
        tmp_path / "corpus.txt",
        "state => open\nstate => open\nstate => open\n",
    )

    with connect(db_path) as connection:
        catch_patterns(connection, [corpus], scope="alpha", replace_scope=True, min_support=2, min_confidence=0.8, max_prefix=2)

    stdout = io.StringIO()
    with redirect_stdout(stdout):
        exit_code = main(["--db", str(db_path), "report", "--scope", "alpha"])

    assert exit_code == 0
    rendered = stdout.getvalue()
    assert "report scope=alpha" in rendered
    assert "next_actions:" in rendered
    assert "triage:" in rendered


def test_explain_json_by_id_includes_health_history_evidence_and_transitions(tmp_path: Path) -> None:
    db_path = tmp_path / "rules.db"
    corpus = write_file(
        tmp_path / "corpus.txt",
        "state => open\nstate => open\nstate => open\n",
    )
    broken = write_file(
        tmp_path / "broken.txt",
        "state => closed\n",
    )

    rule_id = 0
    with connect(db_path) as connection:
        catch_patterns(connection, [corpus], scope="alpha", replace_scope=True, min_support=2, min_confidence=0.8, max_prefix=2)
        target_rule = next(row for row in list_rules(connection, "pending", scope="alpha", rule_type="next_token") if row["expected_token"] == "open")
        rule_id = int(target_rule["id"])
        adopt_rules(connection, [rule_id], actor="silas", source="bootstrap", reason="stabilize core")
        lint_path(connection, broken, scope="alpha")

    stdout = io.StringIO()
    with redirect_stdout(stdout):
        exit_code = main(["--db", str(db_path), "explain", str(rule_id), "--json"])

    assert exit_code == 0
    payload = json.loads(stdout.getvalue())
    assert payload["rule"]["expected_display"] == "open"
    assert payload["health"]["violation_count"] == 1
    assert payload["health"]["recommendation"] == "watch"
    assert payload["summary"]["evidence_count"] == 3
    assert payload["history"][0]["actor"] == "silas"
    assert payload["history"][0]["source"] == "bootstrap"
    observed_match = next(
        item
        for item in payload["observed_transitions"]
        if item["prefix_display"] == ["state", "=>"] and item["next_display"] == "open"
    )
    assert observed_match["support"] == 3


def test_explain_json_can_resolve_rule_by_signature(tmp_path: Path) -> None:
    db_path = tmp_path / "rules.db"
    corpus = write_file(
        tmp_path / "corpus.txt",
        "state => open\nstate => open\nstate => open\n",
    )

    with connect(db_path) as connection:
        catch_patterns(connection, [corpus], scope="alpha", replace_scope=True, min_support=2, min_confidence=0.8, max_prefix=2)

    stdout = io.StringIO()
    with redirect_stdout(stdout):
        exit_code = main(
            [
                "--db",
                str(db_path),
                "explain",
                "--scope",
                "alpha",
                "--rule-type",
                "next_token",
                "--prefix-token",
                "state",
                "--prefix-token",
                "=>",
                "--expected-token",
                "open",
                "--json",
            ]
        )

    assert exit_code == 0
    payload = json.loads(stdout.getvalue())
    assert payload["selector"]["prefix_display"] == ["state", "=>"]
    assert payload["selector"]["expected_display"] == "open"
    assert payload["rule"]["scope"] == "alpha"


def test_explain_json_lists_competing_rules_for_same_prefix(tmp_path: Path) -> None:
    db_path = tmp_path / "rules.db"
    corpus = write_file(
        tmp_path / "corpus.txt",
        "state => open\nstate => open\nstate => closed\nstate => closed\n",
    )

    with connect(db_path) as connection:
        catch_patterns(connection, [corpus], scope="alpha", replace_scope=True, min_support=2, min_confidence=0.4, max_prefix=2)

    stdout = io.StringIO()
    with redirect_stdout(stdout):
        exit_code = main(
            [
                "--db",
                str(db_path),
                "explain",
                "--scope",
                "alpha",
                "--rule-type",
                "next_token",
                "--prefix-token",
                "state",
                "--prefix-token",
                "=>",
                "--expected-token",
                "open",
                "--json",
            ]
        )

    assert exit_code == 0
    payload = json.loads(stdout.getvalue())
    competing = next(
        item
        for item in payload["competing_rules"]
        if item["prefix_display"] == ["state", "=>"] and item["expected_display"] == "closed"
    )
    assert competing["status"] == "pending"


def test_normalize_json_exposes_structural_candidate_tokens(tmp_path: Path) -> None:
    db_path = tmp_path / "rules.db"
    corpus = write_file(
        tmp_path / "corpus.txt",
        "state => open\nmode => safe\nshape => square\n",
    )
    novel = write_file(
        tmp_path / "novel.txt",
        "door closed\n",
    )

    with connect(db_path) as connection:
        catch_patterns(connection, [corpus], scope="syntax", replace_scope=True, min_support=2, min_confidence=0.8, max_prefix=2)
        kind_rule = next(
            row
            for row in list_rules(connection, "pending", scope="syntax", rule_type="next_kind")
            if row["expected_token"] == "OPERATOR"
        )
        adopt_rules(connection, [int(kind_rule["id"])])

    stdout = io.StringIO()
    with redirect_stdout(stdout):
        exit_code = main(["--db", str(db_path), "normalize", str(novel), "--scope", "syntax", "--json"])

    assert exit_code == 1
    payload = json.loads(stdout.getvalue())
    suggestion = payload["suggestions"][0]
    assert suggestion["candidate_tokens"] == ["=>"]
    assert suggestion["suggested_action"] == "insert_before"
    assert suggestion["replacement"] is None


def test_normalize_text_surfaces_structural_insert_hint(tmp_path: Path) -> None:
    db_path = tmp_path / "rules.db"
    corpus = write_file(
        tmp_path / "corpus.txt",
        "state => open\nmode => safe\nshape => square\n",
    )
    novel = write_file(
        tmp_path / "novel.txt",
        "door closed\n",
    )

    with connect(db_path) as connection:
        catch_patterns(connection, [corpus], scope="syntax", replace_scope=True, min_support=2, min_confidence=0.8, max_prefix=2)
        kind_rule = next(
            row
            for row in list_rules(connection, "pending", scope="syntax", rule_type="next_kind")
            if row["expected_token"] == "OPERATOR"
        )
        adopt_rules(connection, [int(kind_rule["id"])])

    stdout = io.StringIO()
    with redirect_stdout(stdout):
        exit_code = main(["--db", str(db_path), "normalize", str(novel), "--scope", "syntax"])

    assert exit_code == 1
    rendered = stdout.getvalue()
    assert "consider inserting one of ['=>'] before 'closed'" in rendered


def test_review_json_is_machine_readable(monkeypatch, tmp_path: Path) -> None:
    db_path = tmp_path / "rules.db"
    corpus = write_file(
        tmp_path / "corpus.txt",
        "state => open\nstate => open\nstate => open\n",
    )

    with connect(db_path) as connection:
        catch_patterns(connection, [corpus], scope="alpha", replace_scope=True, min_support=2, min_confidence=0.8, max_prefix=2)

    stdout = io.StringIO()
    with redirect_stdout(stdout):
        exit_code = main(["--db", str(db_path), "review", "--scope", "alpha", "--json"])

    assert exit_code == 0
    payload = json.loads(stdout.getvalue())
    assert payload["scope"] == "alpha"
    assert payload["rules"]
    assert payload["rules"][0]["prefix_display"]


def test_conflicts_json_groups_competing_rules(tmp_path: Path) -> None:
    db_path = tmp_path / "rules.db"
    corpus = write_file(
        tmp_path / "corpus.txt",
        "state => open\nstate => open\nstate => closed\nstate => closed\n",
    )

    with connect(db_path) as connection:
        catch_patterns(connection, [corpus], scope="alpha", replace_scope=True, min_support=2, min_confidence=0.4, max_prefix=2)

    stdout = io.StringIO()
    with redirect_stdout(stdout):
        exit_code = main(["--db", str(db_path), "conflicts", "--scope", "alpha", "--rule-type", "next_token", "--json"])

    assert exit_code == 0
    payload = json.loads(stdout.getvalue())
    assert len(payload["conflicts"]) >= 1
    conflict = next(item for item in payload["conflicts"] if item["prefix_display"] == ["state", "=>"])
    assert sorted(conflict["expected_options"]) == ["closed", "open"]


def test_lint_json_emits_structured_violations(monkeypatch, tmp_path: Path) -> None:
    db_path = tmp_path / "rules.db"
    corpus = write_file(
        tmp_path / "corpus.txt",
        "state => open\nstate => open\nstate => open\n",
    )

    with connect(db_path) as connection:
        catch_patterns(connection, [corpus], scope="alpha", replace_scope=True, min_support=2, min_confidence=0.8, max_prefix=2)
        target_rule = next(row for row in list_rules(connection, "pending", scope="alpha") if row["expected_token"] == "open")
        adopt_rules(connection, [int(target_rule["id"])])

    monkeypatch.setattr("sys.stdin", io.StringIO("state => closed\n"))
    stdout = io.StringIO()
    with redirect_stdout(stdout):
        exit_code = main(["--db", str(db_path), "lint", "-", "--scope", "alpha", "--label", "incoming", "--json"])

    assert exit_code == 1
    payload = json.loads(stdout.getvalue())
    assert payload["label"] == "incoming"
    assert payload["violations"][0]["expected_display"] == "open"
    assert payload["violations"][0]["prefix_display"] == ["state", "=>"]


def test_session_jsonl_emits_line_and_summary_events(monkeypatch, tmp_path: Path) -> None:
    db_path = tmp_path / "rules.db"
    corpus = write_file(
        tmp_path / "corpus.txt",
        "state => open\nstate => open\nstate => open\n",
    )

    with connect(db_path) as connection:
        catch_patterns(connection, [corpus], scope="alpha", replace_scope=True, min_support=2, min_confidence=0.8, max_prefix=2)
        target_rule = next(row for row in list_rules(connection, "pending", scope="alpha", rule_type="next_token") if row["expected_token"] == "open")
        adopt_rules(connection, [int(target_rule["id"])])

    monkeypatch.setattr("sys.stdin", io.StringIO("state => closed\nmode => safe\n"))
    stdout = io.StringIO()
    with redirect_stdout(stdout):
        exit_code = main(["--db", str(db_path), "session", "--scope", "alpha", "--label", "live", "--format", "jsonl"])

    assert exit_code == 1
    events = [json.loads(line) for line in stdout.getvalue().splitlines()]
    assert events[0]["event"] == "line"
    assert events[0]["violations"]
    assert events[1]["event"] == "line"
    assert events[-1]["event"] == "summary"
    assert events[-1]["line_count"] == 2
    assert events[-1]["violation_count"] == 1


def test_session_learn_adds_rules_to_scope(monkeypatch, tmp_path: Path) -> None:
    db_path = tmp_path / "rules.db"

    monkeypatch.setattr("sys.stdin", io.StringIO("door => open\nwindow => closed\n"))
    stdout = io.StringIO()
    with redirect_stdout(stdout):
        exit_code = main(
            [
                "--db",
                str(db_path),
                "session",
                "--scope",
                "beta",
                "--label",
                "learn-beta",
                "--learn",
                "--format",
                "jsonl",
                "--min-confidence",
                "0.5",
            ]
        )

    assert exit_code == 0
    events = [json.loads(line) for line in stdout.getvalue().splitlines()]
    assert events[-1]["event"] == "summary"
    assert events[-1]["learn"] is True
    assert events[-1]["candidate_rule_count"] > 0

    with connect(db_path) as connection:
        learned_rules = list_rules(connection, "pending", scope="beta")

    assert learned_rules


def test_export_import_scope_roundtrip_preserves_stack_history_and_health(tmp_path: Path) -> None:
    source_db = tmp_path / "source.db"
    target_db = tmp_path / "target.db"
    corpus = write_file(
        tmp_path / "corpus.txt",
        "state => open\nstate => open\nstate => open\n",
    )
    broken = write_file(
        tmp_path / "broken.txt",
        "state => closed\n",
    )
    snapshot_path = tmp_path / "alpha.rulecatcher.json"

    with connect(source_db) as connection:
        catch_patterns(connection, [corpus], scope="alpha", replace_scope=True, min_support=2, min_confidence=0.8, max_prefix=2)
        target_rule = next(row for row in list_rules(connection, "pending", scope="alpha", rule_type="next_token") if row["expected_token"] == "open")
        adopt_rules(connection, [int(target_rule["id"])], actor="silas", source="bootstrap", reason="share this stack")
        lint_path(connection, broken, scope="alpha")

    stdout = io.StringIO()
    with redirect_stdout(stdout):
        exit_code = main(["--db", str(source_db), "export-scope", "--scope", "alpha", "--output", str(snapshot_path)])

    assert exit_code == 0
    exported_payload = json.loads(snapshot_path.read_text(encoding="utf-8"))
    assert exported_payload["format"] == "rulecatcher-scope-v1"
    assert exported_payload["scope"] == "alpha"
    assert exported_payload["rules"]
    assert exported_payload["decisions"]

    stdout = io.StringIO()
    with redirect_stdout(stdout):
        exit_code = main(
            [
                "--db",
                str(target_db),
                "import-scope",
                str(snapshot_path),
                "--scope",
                "beta",
                "--replace-scope",
                "--json",
            ]
        )

    assert exit_code == 0
    import_payload = json.loads(stdout.getvalue())
    assert import_payload["source_scope"] == "alpha"
    assert import_payload["target_scope"] == "beta"
    assert import_payload["rule_count"] >= 1

    with connect(target_db) as connection:
        imported_rule = next(row for row in list_rules(connection, "adopted", scope="beta", rule_type="next_token") if row["expected_token"] == "open")
        imported_violations = lint_path(connection, broken, scope="beta")

    assert imported_rule["status"] == "adopted"
    assert len(imported_violations) == 1
    assert imported_violations[0].expected_token == "open"

    stdout = io.StringIO()
    with redirect_stdout(stdout):
        exit_code = main(["--db", str(target_db), "history", "--scope", "beta", "--json"])

    assert exit_code == 0
    history_payload = json.loads(stdout.getvalue())
    imported_event = next(
        event
        for event in history_payload["events"]
        if event["expected_display"] == "open" and event["new_status"] == "adopted"
    )
    assert imported_event["actor"] == "silas"
    assert imported_event["source"] == "bootstrap"

    stdout = io.StringIO()
    with redirect_stdout(stdout):
        exit_code = main(["--db", str(target_db), "govern", "--scope", "beta", "--status", "all", "--json"])

    assert exit_code == 0
    govern_payload = json.loads(stdout.getvalue())
    health_row = next(
        rule
        for rule in govern_payload["rules"]
        if rule["status"] == "adopted" and rule["expected_display"] == "open" and rule["prefix_display"] == ["state", "=>"]
    )
    assert health_row["violation_count"] == 2


def test_compare_json_reports_rule_and_transition_diffs_between_scopes(tmp_path: Path) -> None:
    db_path = tmp_path / "rules.db"
    alpha = write_file(
        tmp_path / "alpha.txt",
        "state => open\nstate => open\nstate => open\n",
    )
    beta = write_file(
        tmp_path / "beta.txt",
        "state => closed\nstate => closed\nstate => closed\n",
    )

    with connect(db_path) as connection:
        catch_patterns(connection, [alpha], scope="alpha", replace_scope=True, min_support=2, min_confidence=0.8, max_prefix=2)
        catch_patterns(connection, [beta], scope="beta", replace_scope=True, min_support=2, min_confidence=0.8, max_prefix=2)

        alpha_rule = next(row for row in list_rules(connection, "pending", scope="alpha", rule_type="next_token") if row["expected_token"] == "open")
        beta_rule = next(row for row in list_rules(connection, "pending", scope="beta", rule_type="next_token") if row["expected_token"] == "closed")
        adopt_rules(connection, [int(alpha_rule["id"])], actor="silas", source="alpha-bootstrap")
        adopt_rules(connection, [int(beta_rule["id"])], actor="silas", source="beta-bootstrap")

    stdout = io.StringIO()
    with redirect_stdout(stdout):
        exit_code = main(["--db", str(db_path), "compare", "scope:alpha", "scope:beta", "--json"])

    assert exit_code == 0
    payload = json.loads(stdout.getvalue())
    assert payload["summary"]["rule_added_count"] >= 1
    assert payload["summary"]["rule_removed_count"] >= 1
    assert payload["summary"]["transition_added_count"] >= 1
    assert payload["summary"]["transition_removed_count"] >= 1

    added_rule = next(
        item
        for item in payload["rules"]["added"]
        if item["prefix_display"] == ["state", "=>"] and item["expected_display"] == "closed"
    )
    removed_rule = next(
        item
        for item in payload["rules"]["removed"]
        if item["prefix_display"] == ["state", "=>"] and item["expected_display"] == "open"
    )
    assert added_rule["status"] == "adopted"
    assert removed_rule["status"] == "adopted"

    added_transition = next(
        item
        for item in payload["observed_transitions"]["added"]
        if item["prefix_display"] == ["state", "=>"] and item["next_display"] == "closed"
    )
    removed_transition = next(
        item
        for item in payload["observed_transitions"]["removed"]
        if item["prefix_display"] == ["state", "=>"] and item["next_display"] == "open"
    )
    assert added_transition["support"] == 3
    assert removed_transition["support"] == 3


def test_compare_snapshot_to_scope_reports_status_and_health_changes(tmp_path: Path) -> None:
    db_path = tmp_path / "rules.db"
    corpus = write_file(
        tmp_path / "corpus.txt",
        "state => open\nstate => open\nstate => open\n",
    )
    broken = write_file(
        tmp_path / "broken.txt",
        "state => closed\n",
    )
    snapshot_path = tmp_path / "alpha-before.rulecatcher.json"

    with connect(db_path) as connection:
        catch_patterns(connection, [corpus], scope="alpha", replace_scope=True, min_support=2, min_confidence=0.8, max_prefix=2)

    stdout = io.StringIO()
    with redirect_stdout(stdout):
        exit_code = main(["--db", str(db_path), "export-scope", "--scope", "alpha", "--output", str(snapshot_path)])

    assert exit_code == 0

    with connect(db_path) as connection:
        target_rule = next(row for row in list_rules(connection, "pending", scope="alpha", rule_type="next_token") if row["expected_token"] == "open")
        adopt_rules(connection, [int(target_rule["id"])], actor="silas", source="bootstrap", reason="stabilize core")
        lint_path(connection, broken, scope="alpha")

    stdout = io.StringIO()
    with redirect_stdout(stdout):
        exit_code = main(["--db", str(db_path), "compare", str(snapshot_path), "scope:alpha", "--json"])

    assert exit_code == 0
    payload = json.loads(stdout.getvalue())
    changed_rule = next(
        item
        for item in payload["rules"]["changed"]
        if item["signature"]["prefix_display"] == ["state", "=>"] and item["signature"]["expected_display"] == "open"
    )
    assert changed_rule["changes"]["status"] == {"left": "pending", "right": "adopted"}
    assert changed_rule["changes"]["violation_count"] == {"left": 0, "right": 1}
    assert payload["summary"]["decision_added_count"] == 1


def test_compare_between_snapshots_does_not_create_default_database(monkeypatch, tmp_path: Path) -> None:
    db_path = tmp_path / "rules.db"
    alpha = write_file(
        tmp_path / "alpha.txt",
        "state => open\nstate => open\nstate => open\n",
    )
    beta = write_file(
        tmp_path / "beta.txt",
        "state => closed\nstate => closed\nstate => closed\n",
    )
    left_snapshot = tmp_path / "alpha.rulecatcher.json"
    right_snapshot = tmp_path / "beta.rulecatcher.json"

    with connect(db_path) as connection:
        catch_patterns(connection, [alpha], scope="alpha", replace_scope=True, min_support=2, min_confidence=0.8, max_prefix=2)
        catch_patterns(connection, [beta], scope="beta", replace_scope=True, min_support=2, min_confidence=0.8, max_prefix=2)

    stdout = io.StringIO()
    with redirect_stdout(stdout):
        exit_code = main(["--db", str(db_path), "export-scope", "--scope", "alpha", "--output", str(left_snapshot)])
    assert exit_code == 0

    stdout = io.StringIO()
    with redirect_stdout(stdout):
        exit_code = main(["--db", str(db_path), "export-scope", "--scope", "beta", "--output", str(right_snapshot)])
    assert exit_code == 0

    monkeypatch.chdir(tmp_path)
    default_db = tmp_path / ".rulecatcher.db"
    assert not default_db.exists()

    stdout = io.StringIO()
    with redirect_stdout(stdout):
        exit_code = main(["compare", str(left_snapshot), str(right_snapshot), "--json"])

    assert exit_code == 0
    assert not default_db.exists()
    payload = json.loads(stdout.getvalue())
    assert payload["left"]["kind"] == "snapshot"
    assert payload["right"]["kind"] == "snapshot"


def test_triage_json_recommends_adopt_for_strong_pending_rule(tmp_path: Path) -> None:
    db_path = tmp_path / "rules.db"
    corpus = write_file(
        tmp_path / "corpus.txt",
        "state => open\nstate => open\nstate => open\n",
    )

    with connect(db_path) as connection:
        catch_patterns(connection, [corpus], scope="alpha", replace_scope=True, min_support=2, min_confidence=0.8, max_prefix=2)

    stdout = io.StringIO()
    with redirect_stdout(stdout):
        exit_code = main(["--db", str(db_path), "triage", "--scope", "alpha", "--json"])

    assert exit_code == 0
    payload = json.loads(stdout.getvalue())
    target = next(rule for rule in payload["rules"] if rule["prefix_display"] == ["state", "=>"] and rule["expected_display"] == "open")
    assert target["recommendation"] == "adopt"
    assert target["conflicting_adopted_rule_ids"] == []
    assert target["competing_pending_rule_ids"] == []
    assert payload["focus"] == "auto"
    assert not any(rule["prefix_display"] == ["=>"] and rule["expected_display"] == "open" for rule in payload["rules"])
    assert not any(rule["prefix_display"] == ["=>", "open"] and rule["expected_display"] == "<EOL>" for rule in payload["rules"])


def test_triage_focus_all_restores_boundary_rules(tmp_path: Path) -> None:
    db_path = tmp_path / "rules.db"
    corpus = write_file(
        tmp_path / "corpus.txt",
        "state => open\nstate => open\nstate => open\n",
    )

    with connect(db_path) as connection:
        catch_patterns(connection, [corpus], scope="alpha", replace_scope=True, min_support=2, min_confidence=0.8, max_prefix=2)

    stdout = io.StringIO()
    with redirect_stdout(stdout):
        exit_code = main(["--db", str(db_path), "triage", "--scope", "alpha", "--focus", "all", "--json"])

    assert exit_code == 0
    payload = json.loads(stdout.getvalue())
    assert payload["focus"] == "all"
    assert any(rule["prefix_display"] == ["=>", "open"] and rule["expected_display"] == "<EOL>" for rule in payload["rules"])


def test_triage_json_flags_conflict_with_adopted_rule(tmp_path: Path) -> None:
    db_path = tmp_path / "rules.db"
    first = write_file(
        tmp_path / "first.txt",
        "state => open\nstate => open\nstate => open\n",
    )
    second = write_file(
        tmp_path / "second.txt",
        "state => closed\nstate => closed\nstate => closed\n",
    )

    with connect(db_path) as connection:
        catch_patterns(connection, [first], scope="alpha", replace_scope=True, min_support=2, min_confidence=0.8, max_prefix=2)
        adopted_rule = next(row for row in list_rules(connection, "pending", scope="alpha", rule_type="next_token") if row["expected_token"] == "open")
        adopt_rules(connection, [int(adopted_rule["id"])])
        catch_patterns(connection, [second], scope="alpha", replace_scope=False, min_support=2, min_confidence=0.4, max_prefix=2)

    stdout = io.StringIO()
    with redirect_stdout(stdout):
        exit_code = main(["--db", str(db_path), "triage", "--scope", "alpha", "--recommendation", "review", "--json"])

    assert exit_code == 0
    payload = json.loads(stdout.getvalue())
    target = next(rule for rule in payload["rules"] if rule["prefix_display"] == ["state", "=>"] and rule["expected_display"] == "closed")
    assert target["recommendation"] == "review"
    assert target["conflicting_adopted_rule_ids"]
    assert any("conflicts with adopted rule" in reason for reason in target["reasons"])


def test_session_learn_triage_emits_proposal_event(monkeypatch, tmp_path: Path) -> None:
    db_path = tmp_path / "rules.db"

    monkeypatch.setattr("sys.stdin", io.StringIO("state => open\nstate => open\nstate => open\n"))
    stdout = io.StringIO()
    with redirect_stdout(stdout):
        exit_code = main(
            [
                "--db",
                str(db_path),
                "session",
                "--scope",
                "alpha",
                "--label",
                "teach",
                "--learn",
                "--triage",
                "--format",
                "jsonl",
            ]
        )

    assert exit_code == 0
    events = [json.loads(line) for line in stdout.getvalue().splitlines()]
    triage_event = next(event for event in events if event["event"] == "triage")
    assert triage_event["proposal_count"] > 0
    target = next(rule for rule in triage_event["rules"] if rule["prefix_display"] == ["state", "=>"] and rule["expected_display"] == "open")
    assert target["recommendation"] == "adopt"
    assert not any(rule["prefix_display"] == ["=>"] and rule["expected_display"] == "open" for rule in triage_event["rules"])
    assert events[-1]["event"] == "summary"
    assert events[-1]["triage"] is True
    assert events[-1]["triage_count"] == triage_event["proposal_count"]


def test_apply_triage_json_dry_run_previews_without_mutation(tmp_path: Path) -> None:
    db_path = tmp_path / "rules.db"
    corpus = write_file(
        tmp_path / "corpus.txt",
        "state => open\nstate => open\nstate => open\n",
    )

    with connect(db_path) as connection:
        catch_patterns(connection, [corpus], scope="alpha", replace_scope=True, min_support=2, min_confidence=0.8, max_prefix=2)

    stdout = io.StringIO()
    with redirect_stdout(stdout):
        exit_code = main(
            [
                "--db",
                str(db_path),
                "apply-triage",
                "--scope",
                "alpha",
                "--recommendation",
                "adopt",
                "--dry-run",
                "--json",
            ]
        )

    assert exit_code == 0
    payload = json.loads(stdout.getvalue())
    assert payload["dry_run"] is True
    assert payload["focus"] == "auto"
    assert payload["rules"]
    assert payload["applied_count"] == 0
    assert payload["applied_rule_ids"] == []

    with connect(db_path) as connection:
        adopted_rules = list_rules(connection, "adopted", scope="alpha")

    assert adopted_rules == []


def test_apply_triage_json_applies_adopt_recommendations_with_history(tmp_path: Path) -> None:
    db_path = tmp_path / "rules.db"
    corpus = write_file(
        tmp_path / "corpus.txt",
        "state => open\nstate => open\nstate => open\n",
    )

    with connect(db_path) as connection:
        catch_patterns(connection, [corpus], scope="alpha", replace_scope=True, min_support=2, min_confidence=0.8, max_prefix=2)

    stdout = io.StringIO()
    with redirect_stdout(stdout):
        exit_code = main(
            [
                "--db",
                str(db_path),
                "apply-triage",
                "--scope",
                "alpha",
                "--recommendation",
                "adopt",
                "--actor",
                "silas",
                "--source",
                "triage-loop",
                "--reason-prefix",
                "batch apply",
                "--json",
            ]
        )

    assert exit_code == 0
    payload = json.loads(stdout.getvalue())
    assert payload["applied_count"] > 0
    target = next(rule for rule in payload["rules"] if rule["prefix_display"] == ["state", "=>"] and rule["expected_display"] == "open")
    assert target["recommendation"] == "adopt"

    stdout = io.StringIO()
    with redirect_stdout(stdout):
        exit_code = main(["--db", str(db_path), "history", "--scope", "alpha", "--json"])

    assert exit_code == 0
    history_payload = json.loads(stdout.getvalue())
    event = next(
        item
        for item in history_payload["events"]
        if item["expected_display"] == "open" and item["new_status"] == "adopted"
    )
    assert event["actor"] == "silas"
    assert event["source"] == "triage-loop:adopt"
    assert event["reason"] is not None
    assert event["reason"].startswith("batch apply; triage recommend adopt:")


def test_session_apply_triage_emits_apply_event_and_mutates_stack(monkeypatch, tmp_path: Path) -> None:
    db_path = tmp_path / "rules.db"

    monkeypatch.setattr("sys.stdin", io.StringIO("state => open\nstate => open\nstate => open\n"))
    stdout = io.StringIO()
    with redirect_stdout(stdout):
        exit_code = main(
            [
                "--db",
                str(db_path),
                "session",
                "--scope",
                "alpha",
                "--label",
                "auto",
                "--learn",
                "--triage",
                "--apply-triage",
                "adopt",
                "--format",
                "jsonl",
            ]
        )

    assert exit_code == 0
    events = [json.loads(line) for line in stdout.getvalue().splitlines()]
    triage_event = next(event for event in events if event["event"] == "triage")
    assert triage_event["focus"] == "auto"
    assert not any(rule["prefix_display"] == ["=>", "open"] and rule["expected_display"] == "<EOL>" for rule in triage_event["rules"])
    apply_event = next(event for event in events if event["event"] == "apply_triage")
    assert apply_event["focus"] == "auto"
    assert apply_event["recommendation"] == "adopt"
    assert apply_event["applied_count"] > 0
    assert events[-1]["applied_triage_counts"]["adopt"] == apply_event["applied_count"]

    with connect(db_path) as connection:
        adopted_rules = list_rules(connection, "adopted", scope="alpha")

    assert any(row["expected_token"] == "open" for row in adopted_rules)


def test_history_json_tracks_explicit_decision_provenance(tmp_path: Path) -> None:
    db_path = tmp_path / "rules.db"
    corpus = write_file(
        tmp_path / "corpus.txt",
        "state => open\nstate => open\nstate => open\n",
    )

    with connect(db_path) as connection:
        catch_patterns(connection, [corpus], scope="alpha", replace_scope=True, min_support=2, min_confidence=0.8, max_prefix=2)
        target_rule = next(row for row in list_rules(connection, "pending", scope="alpha", rule_type="next_token") if row["expected_token"] == "open")

    stdout = io.StringIO()
    with redirect_stdout(stdout):
        exit_code = main(
            [
                "--db",
                str(db_path),
                "adopt",
                str(target_rule["id"]),
                "--actor",
                "silas",
                "--source",
                "review-loop",
                "--reason",
                "stable core syntax",
                "--json",
            ]
        )

    assert exit_code == 0
    payload = json.loads(stdout.getvalue())
    assert payload["actor"] == "silas"
    assert payload["source"] == "review-loop"
    assert payload["reason"] == "stable core syntax"

    stdout = io.StringIO()
    with redirect_stdout(stdout):
        exit_code = main(["--db", str(db_path), "history", "--scope", "alpha", "--json"])

    assert exit_code == 0
    payload = json.loads(stdout.getvalue())
    event = payload["events"][0]
    assert event["previous_status"] == "pending"
    assert event["new_status"] == "adopted"
    assert event["automatic"] is False
    assert event["actor"] == "silas"
    assert event["source"] == "review-loop"
    assert event["reason"] == "stable core syntax"
    assert event["prefix_display"] == ["state", "=>"]
    assert event["expected_display"] == "open"


def test_history_json_records_automatic_displacement(tmp_path: Path) -> None:
    db_path = tmp_path / "rules.db"
    first = write_file(
        tmp_path / "first.txt",
        "state => open\nstate => open\nstate => open\n",
    )
    second = write_file(
        tmp_path / "second.txt",
        "state => closed\nstate => closed\nstate => closed\n",
    )

    with connect(db_path) as connection:
        catch_patterns(connection, [first], scope="alpha", replace_scope=True, min_support=2, min_confidence=0.8, max_prefix=2)
        open_rule = next(row for row in list_rules(connection, "pending", scope="alpha", rule_type="next_token") if row["expected_token"] == "open")
        adopt_rules(connection, [int(open_rule["id"])], actor="silas", source="bootstrap", reason="initial stack choice")
        catch_patterns(connection, [second], scope="alpha", replace_scope=False, min_support=2, min_confidence=0.4, max_prefix=2)
        closed_rule = next(row for row in list_rules(connection, "pending", scope="alpha", rule_type="next_token") if row["expected_token"] == "closed")

    stdout = io.StringIO()
    with redirect_stdout(stdout):
        exit_code = main(
            [
                "--db",
                str(db_path),
                "adopt",
                str(closed_rule["id"]),
                "--actor",
                "silas",
                "--source",
                "repair-loop",
                "--reason",
                "new dominant pattern",
                "--json",
            ]
        )

    assert exit_code == 0

    stdout = io.StringIO()
    with redirect_stdout(stdout):
        exit_code = main(["--db", str(db_path), "history", "--scope", "alpha", "--json"])

    assert exit_code == 0
    payload = json.loads(stdout.getvalue())

    explicit_event = next(
        event
        for event in payload["events"]
        if event["expected_display"] == "closed" and event["new_status"] == "adopted"
    )
    assert explicit_event["automatic"] is False
    assert explicit_event["source"] == "repair-loop"

    automatic_event = next(
        event
        for event in payload["events"]
        if event["expected_display"] == "open" and event["automatic"] is True
    )
    assert automatic_event["previous_status"] == "adopted"
    assert automatic_event["new_status"] == "rejected"
    assert automatic_event["source"] == "repair-loop:auto-displace"
    assert automatic_event["reason"] == f"superseded by adopted rule {closed_rule['id']}"


def test_govern_json_reports_rule_health(tmp_path: Path) -> None:
    db_path = tmp_path / "rules.db"
    corpus = write_file(
        tmp_path / "corpus.txt",
        "state => open\nstate => open\nstate => open\n",
    )

    with connect(db_path) as connection:
        catch_patterns(connection, [corpus], scope="alpha", replace_scope=True, min_support=2, min_confidence=0.8, max_prefix=2)
        target_rule = next(row for row in list_rules(connection, "pending", scope="alpha", rule_type="next_token") if row["expected_token"] == "open")
        adopt_rules(connection, [int(target_rule["id"])])
        lint_path(connection, write_file(tmp_path / "clean.txt", "state => open\n"), scope="alpha")
        lint_path(connection, write_file(tmp_path / "broken-1.txt", "state => closed\n"), scope="alpha")
        lint_path(connection, write_file(tmp_path / "broken-2.txt", "state => closed\n"), scope="alpha")

    stdout = io.StringIO()
    with redirect_stdout(stdout):
        exit_code = main(
            [
                "--db",
                str(db_path),
                "govern",
                "--scope",
                "alpha",
                "--recommendation",
                "review",
                "--json",
            ]
        )

    assert exit_code == 0
    payload = json.loads(stdout.getvalue())
    assert payload["scope"] == "alpha"
    assert payload["recommendation"] == "review"
    assert len(payload["rules"]) == 1
    rule = payload["rules"][0]
    assert rule["prefix_display"] == ["state", "=>"]
    assert rule["expected_display"] == "open"
    assert rule["hit_count"] == 1
    assert rule["violation_count"] == 2
    assert rule["evaluation_count"] == 3
    assert rule["violation_rate"] == 2 / 3
    assert rule["recommendation"] == "review"
    assert rule["last_hit_at"] is not None
    assert rule["last_violation_at"] is not None


# --- regressions for the three CSGN findings (verdict / triage-core / json) ---

def test_lint_verdict_orthogonal_vs_syntax_break(tmp_path: Path) -> None:
    # #4: a found token that IS in the language (a known kind) -> orthogonal
    # (steerable); a foreign kind -> syntax_break (fatal).
    from rulecatcher.linting import lint_text
    db_path = tmp_path / "rules.db"
    corpus = write_file(tmp_path / "c.txt", "state => open\nmode => safe\nshape => square\n")
    with connect(db_path) as cx:
        catch_patterns(cx, [corpus], scope="syntax", min_support=2, min_confidence=0.8, max_prefix=2)
        spine = next(
            r for r in list_rules(cx, "pending", scope="syntax", rule_type="next_kind")
            if json.loads(r["prefix_json"]) == ["<BOS>", "IDENTIFIER"] and r["expected_token"] == "OPERATOR"
        )
        adopt_rules(cx, [int(spine["id"])])
        # 'closed' is an IDENTIFIER — a kind the grammar uses -> orthogonal
        ortho = lint_text(cx, "door closed\n", scope="syntax", record_stats=False)
        # '123' is a NUMBER — foreign to this grammar -> syntax_break
        brk = lint_text(cx, "door 123\n", scope="syntax", record_stats=False)
    assert ortho and ortho[0].verdict == "orthogonal"
    assert brk and brk[0].verdict == "syntax_break"


def test_triage_core_keeps_line_opener_rule(tmp_path: Path) -> None:
    # #3: a [<BOS>, X] -> Y line-opener is the grammar, not boundary boilerplate;
    # triage --focus core must keep it.
    from rulecatcher.tokenize import BOS
    from rulecatcher.triage import triage_pending_rules
    db_path = tmp_path / "rules.db"
    corpus = write_file(tmp_path / "c.txt", "state => open\nmode => safe\nshape => square\n")
    with connect(db_path) as cx:
        catch_patterns(cx, [corpus], scope="syntax", min_support=2, min_confidence=0.8, max_prefix=2)
        core = triage_pending_rules(cx, scope="syntax", focus="core", frontier_only=False)
    assert any(BOS in p.prefix and p.expected_token not in {"<BOS>", "<EOL>"} for p in core)


def test_serialize_rule_row_fields_are_consistent(tmp_path: Path) -> None:
    # #5: next_kind classes are bracketed in prefix/expected_token (matching the
    # human view), with the raw signature exposed explicitly.
    from rulecatcher.present import serialize_rule_row
    db_path = tmp_path / "rules.db"
    corpus = write_file(tmp_path / "c.txt", "state => open\nmode => safe\nshape => square\n")
    with connect(db_path) as cx:
        catch_patterns(cx, [corpus], scope="syntax", min_support=2, min_confidence=0.8, max_prefix=2)
        row = next(
            r for r in list_rules(cx, "pending", scope="syntax", rule_type="next_kind")
            if json.loads(r["prefix_json"]) == ["<BOS>", "IDENTIFIER"] and r["expected_token"] == "OPERATOR"
        )
        payload = serialize_rule_row(row)
    assert payload["prefix"] == ["<BOS>", "<IDENTIFIER>"]      # consistent display form
    assert payload["expected_token"] == "<OPERATOR>"
    assert payload["prefix_signature"] == ["<BOS>", "IDENTIFIER"]  # raw form for matching
    assert payload["expected_signature"] == "OPERATOR"
