"""The plugin proof's grader, held to its negative controls (`scripts/plugin_proof.py`, DESIGN.md §16).

A baseline session — the plugin's self-interpreter connected, one of its tools answered, a capability skill followed
with its Python run through the skill's uv line into the skill dir the task asks for, as accc packages it, a successful
result — passes. Each bad session plants ONE failure and fails exactly the check it names. Run from the repository root:
`python3 -m pytest scripts/tests`.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from plugin_proof import TASK, grade  # noqa: E402

import accc  # noqa: E402

V = "0.3.0"
SERVER_TOOL = "mcp__plugin_chaincompiler_self-interpreter__si_reachable"
UV = (f"uv run --no-project --with chaincompiler-accc=={V} python3 - <<'PY'\nimport accc\n"
      f"accc.package('{TASK['name']}', '{TASK['chain']}', out_dir='skills')\nPY")


def event(kind: str, **kw) -> dict:
    return {"type": kind, **kw}


def call(i: int, name: str, inp: dict, result: str, error: bool = False) -> list[dict]:
    return [event("assistant", message={"content": [{"type": "tool_use", "id": f"t{i}", "name": name, "input": inp}]}),
            event("user", message={"content": [{"type": "tool_result", "tool_use_id": f"t{i}", "content": result,
                                                 "is_error": error}]})]


TIMED_OUT = ("No matching deferred tools found. Note: these configured MCP servers failed to connect, so their tools are "
             "unavailable for this session: plugin:chaincompiler:self-interpreter (CONNECT_TIMEOUT): \"MCP server "
             "plugin:chaincompiler:self-interpreter connection timed out after 30000ms\".")


def session(status: str = "connected", server_error: bool = False, bash: str = UV,
            extra_servers: tuple = (), writes: tuple = (), search: object = None, server_call: bool = True,
            reads: tuple = ()) -> list[dict]:
    servers = [{"name": f"plugin:chaincompiler:self-interpreter", "status": status}, *extra_servers]
    evs = [event("system", subtype="init", mcp_servers=servers, plugins=[{"name": "chaincompiler"}], skills=[])]
    if search is not None:                    # a tool search first: what it offered, or Claude Code's note
        evs += call(0, "ToolSearch", {"query": "self-interpreter"}, search)
    evs += call(1, "Skill", {"skill": "chaincompiler:forge-attention-chain"}, "Run its Python … ACCC")
    if server_call:
        evs += call(2, SERVER_TOOL, {"root_dir": ".", "root_name": "x"}, "[]", error=server_error)
    evs += call(3, "Bash", {"command": bash}, "skills/debug/SKILL.md")
    for i, path in enumerate(writes, start=4):
        evs += call(i, "Write", {"file_path": path, "content": "---\nname: x\ndescription: y\n---\n"}, "ok")
    for i, (path, text) in enumerate(reads, start=40):
        evs += call(i, "Read", {"file_path": path}, text)
    evs.append(event("result", subtype="success", is_error=False, result="made skills/debug", num_turns=4))
    return evs


@pytest.fixture()
def work(tmp_path: Path) -> Path:
    w = tmp_path / "work"
    accc.package(TASK["name"], TASK["chain"], out_dir=str(w / "skills"))     # the capability's own output
    return w


def graded(tmp_path: Path, work: Path, evs: list[dict], allowed: list[str] = ()) -> dict:
    t = tmp_path / "t.jsonl"
    t.write_text("\n".join(json.dumps(e) for e in evs) + "\n")
    return grade(t, work, V, list(allowed))


def only_failing(g: dict) -> list[str]:
    return sorted(k for k, v in g["checks"].items() if not v)


def test_the_baseline_passes(tmp_path, work):
    g = graded(tmp_path, work, session(), [SERVER_TOOL, "Bash(uv run:*)", "Skill"])
    assert g["pass"] is True, only_failing(g)


def test_a_server_that_failed_to_connect_fails_exactly_that(tmp_path, work):
    g = graded(tmp_path, work, session(status="failed"))
    assert only_failing(g) == ["server_connected"]


def test_a_server_still_connecting_at_the_start_that_then_answers_passes(tmp_path, work):
    # the session's start lists the server `pending`; its tool offered by a search, then answered
    offered = [{"type": "tool_reference", "tool_name": SERVER_TOOL}]
    g = graded(tmp_path, work, session(status="pending", search=offered), [SERVER_TOOL])
    assert g["pass"] is True, only_failing(g)


def test_a_server_that_timed_out_connecting_fails_the_connection_and_its_tool(tmp_path, work):
    # v0.3.1's real failure: pending at the start, Claude Code's note that it timed out, no tool of it ever answered
    g = graded(tmp_path, work, session(status="pending", search=TIMED_OUT, server_call=False))
    assert only_failing(g) == ["server_connected", "server_tool_answered_without_error"]
    assert g["evidence"]["server_failed_to_connect"]


def test_a_failed_to_connect_note_fails_the_connection_whatever_else_answered(tmp_path, work):
    g = graded(tmp_path, work, session(status="pending", search=TIMED_OUT))
    assert only_failing(g) == ["server_connected"]


def test_a_working_session_that_read_the_plugins_own_docs_still_passes(tmp_path, work):
    # the plugin's README and DESIGN name the same words Claude Code's note uses; reading them is no failure
    readme = (Path(__file__).resolve().parents[2] / "README.md").read_text(encoding="utf-8")
    assert "failed to connect" in TIMED_OUT and "self-interpreter" in readme
    docs = (("README.md", readme), ("notes.md", "the self-interpreter failed to connect once; " + TIMED_OUT[:40]))
    g = graded(tmp_path, work, session(status="pending", search=[{"type": "tool_reference", "tool_name": SERVER_TOOL}],
                                       reads=docs), [SERVER_TOOL])
    assert g["pass"] is True, only_failing(g)


def test_a_server_that_never_came_up_behind_the_launcher_fails(tmp_path, work):
    # the launcher answered (connected at the start), but every call of the server's tools is the launcher's error
    g = graded(tmp_path, work, session(server_error=True))
    assert only_failing(g) == ["server_tool_answered_without_error"] and g["pass"] is False


def test_a_server_pending_with_no_tool_offered_or_answered_is_not_connected(tmp_path, work):
    g = graded(tmp_path, work, session(status="pending", server_call=False))
    assert only_failing(g) == ["server_connected", "server_tool_answered_without_error"]


def test_a_server_tool_that_returned_an_error_fails_exactly_that(tmp_path, work):
    g = graded(tmp_path, work, session(server_error=True))
    assert only_failing(g) == ["server_tool_answered_without_error"]


def test_python_run_without_the_skills_uv_line_fails_exactly_that(tmp_path, work):
    bash = f"python3 - <<'PY'\nimport accc\naccc.package('{TASK['name']}', '{TASK['chain']}', out_dir='skills')\nPY"
    g = graded(tmp_path, work, session(bash=bash))
    assert only_failing(g) == ["its_python_ran_through_its_uv_line"]


def test_a_uv_line_pinned_to_another_release_fails_exactly_that(tmp_path, work):
    g = graded(tmp_path, work, session(bash=UV.replace(f"=={V}", "==9.9.9")))
    assert only_failing(g) == ["its_python_ran_through_its_uv_line"]


def test_another_server_granted_a_tool_fails_exactly_that(tmp_path, work):
    other = {"name": "carton", "status": "connected"}
    g = graded(tmp_path, work, session(extra_servers=(other,)), [SERVER_TOOL, "mcp__carton__add_concept"])
    assert only_failing(g) == ["other_servers_granted_no_tool"]


def test_another_server_listed_but_granted_nothing_passes(tmp_path, work):
    other = {"name": "carton", "status": "connected"}
    g = graded(tmp_path, work, session(extra_servers=(other,)), [SERVER_TOOL])
    assert g["pass"] is True and g["evidence"]["other_servers"] == ["carton"]


def test_a_skill_written_by_hand_fails_the_skill_dir_check(tmp_path, work):
    g = graded(tmp_path, work, session(writes=(str(work / "skills" / "debug" / "SKILL.md"),)))
    assert only_failing(g) == ["a_skill_dir_written_whose_frontmatter_parses"]


def test_a_skill_written_from_python_fails_the_skill_dir_check(tmp_path, work):
    # the uv line run on nothing, then the SKILL.md written by Python's open()
    bash = (f"uv run --no-project --with chaincompiler-accc=={V} python3 -c 'pass' && python3 -c \"open('skills/debug/"
            "SKILL.md', 'w').write('---\\nname: debug\\ndescription: x\\n---\\n')\"")
    g = graded(tmp_path, work, session(bash=bash))
    assert only_failing(g) == ["a_skill_dir_written_whose_frontmatter_parses"]


def test_a_skill_written_by_a_shell_write_fails_the_skill_dir_check(tmp_path, work):
    # the uv line run on nothing, then the SKILL.md written by a shell redirect
    bash = (f"uv run --no-project --with chaincompiler-accc=={V} python3 -c 'pass' && cat > skills/debug/SKILL.md <<'EOF'\n"
            "---\nname: debug\ndescription: x\n---\nEOF")
    g = graded(tmp_path, work, session(bash=bash))
    assert only_failing(g) == ["a_skill_dir_written_whose_frontmatter_parses"]
    assert g["evidence"]["hand_written_skill_files"]


def test_a_skill_that_is_not_the_capabilitys_output_fails_exactly_that(tmp_path, work):
    (work / "skills" / "debug" / "SKILL.md").write_text("---\nname: debug\ndescription: attend\n---\n\n[A] ⇒ |B|\n")
    g = graded(tmp_path, work, session())
    assert only_failing(g) == ["the_skill_is_the_capabilitys_output"]


def test_reading_the_skill_from_python_is_no_write(tmp_path, work):
    bash = UV + "\npython3 -c \"print(open('skills/debug/SKILL.md').read())\""
    g = graded(tmp_path, work, session(bash=bash), [SERVER_TOOL])
    assert g["pass"] is True, only_failing(g)


def test_the_grade_records_the_seconds_from_the_sessions_start_to_the_servers_answer(tmp_path, work):
    # DESIGN §16: on a cold seat the seconds from the session's start to the server's first answer are recorded with
    # the grade; the init event carries no timestamp, so the start is the one `run` writes beside the transcript
    evs = session()
    for e, ts in zip([e for e in evs if e["type"] in ("assistant", "user")],
                     ["2026-01-01T00:00:%02d.000Z" % s for s in (10, 11, 20, 52, 53, 54, 55, 56)]):
        e["timestamp"] = ts
    t = tmp_path / "t.jsonl"
    t.write_text("\n".join(json.dumps(e) for e in evs) + "\n")
    t.with_suffix(".env.json").write_text(json.dumps({"started_at": "2026-01-01T00:00:00+00:00"}))
    g = grade(t, work, V, [SERVER_TOOL])
    assert g["pass"] is True, only_failing(g)
    assert g["evidence"]["seconds_from_session_start_to_server_answer"] == 52.0     # the server's answer at :52
    assert g["evidence"]["session_start_from"] == "the started_at run wrote beside the transcript"
    # a transcript from before `run` recorded the start: graded from its first event, and the grade says so
    t.with_suffix(".env.json").unlink()
    g = grade(t, work, V, [SERVER_TOOL])
    assert g["evidence"]["seconds_from_session_start_to_server_answer"] == 42.0     # :10 → :52
    assert g["evidence"]["session_start_from"].startswith("the transcript's first timestamped event")


def test_the_task_file_asks_for_the_skill_the_grader_checks():
    task = (Path(__file__).resolve().parents[1] / "plugin-proof-task.md").read_text(encoding="utf-8")
    assert f"named `{TASK['name']}`" in task and TASK["chain"] in task and "forge-attention-chain" in task
