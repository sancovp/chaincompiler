"""The release check (`scripts/release_check.py`, the release flow's THE PROOF), held to the findings it must make.

Each part runs on a clean stand-in and finds nothing, and on a stand-in planting ONE defect of its kind and names it —
each plant the input the check the part stands in for would fail: the generated files on a committed copy of this
folder (a stale file, a missing one), the frontmatter on a skills folder, the sentences on a small git repository (a
reading in the README past its changelog, one on a line naming `git grep`, one wrapped across two lines), the publish
dry run against a local bare repository standing in for the public one (only where the source home's publisher is
beside this folder), the tee probe through stand-in logs (an opening probe held, a call written before the real server
answered, an answer the server never gave), and the refusal to run on a dirty tree or another tree's packages. Run from
the repository root: `python3 -m pytest scripts/tests`.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
import release_check as rc  # noqa: E402

TOOLS = json.loads((REPO / "server" / "tools.json").read_text(encoding="utf-8"))


def git(d: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(d), *args], capture_output=True, text=True, check=True).stdout


def commit_all(d: Path, msg: str = "tip") -> None:
    git(d, "add", "-A")
    git(d, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-m", msg)


@pytest.fixture()
def home(tmp_path: Path) -> Path:
    """A git repository holding a committed copy of this folder at `base/chaincompiler`."""
    top = tmp_path / "home"
    folder = top / "base" / "chaincompiler"
    folder.mkdir(parents=True)
    git(top, "init", "-q")
    rc.extract(*rc.toplevel(REPO), folder)
    commit_all(top)
    return folder


# ── the tip being proven ────────────────────────────────────────────────────────────────────────────────────────────
def test_a_dirty_folder_is_refused(home):
    (home / "DESIGN.md").write_text("an edit not committed\n", encoding="utf-8")
    found = rc.preflight(home, sys.executable)
    assert any(f.startswith("the folder has uncommitted changes") and "DESIGN.md" in f for f in found)


def test_packages_imported_from_another_tree_are_refused(home):
    # this environment imports the packages of the tree it was installed from, never the stand-in's copy
    found = rc.preflight(home, sys.executable)
    assert any("not from this tree's packages/" in f for f in found)


# ── generated ───────────────────────────────────────────────────────────────────────────────────────────────────────
def test_generated_files_as_committed_find_nothing(home):
    assert rc.part_generated(home, sys.executable, steps=("site", "legend")) == []


def test_a_stale_generated_file_is_named(home):
    data = home / "site" / "data.json"
    data.write_text(data.read_text(encoding="utf-8").replace('"P10"', '"P10-stale"', 1), encoding="utf-8")
    commit_all(home.parents[1], "a stale site")
    found = rc.part_generated(home, sys.executable, steps=("site",))
    assert found == ["site/data.json is stale — `update_site.py` writes it otherwise"]


def test_a_generated_file_the_commit_lacks_is_named(home):
    (home / "assets" / "roadmap.svg").unlink()
    commit_all(home.parents[1], "the roadmap image left out")
    found = rc.part_generated(home, sys.executable, steps=("site",))
    assert found == ["assets/roadmap.svg is not committed — `update_site.py` writes it, and the public deploy.yml fails "
                     "a generated file left untracked"]


def test_a_capability_skill_edited_by_hand_is_named(home):
    p = home / "skills" / "forge-cor" / "SKILL.md"
    p.write_text(p.read_text(encoding="utf-8") + "\nan edit the generator does not make\n", encoding="utf-8")
    commit_all(home.parents[1], "a hand edit")
    found = rc.part_generated(home, sys.executable, steps=("skills",))
    assert "skills/forge-cor/SKILL.md is stale — `build_meta_ape_skills.py` writes it otherwise" in found


# ── frontmatter ─────────────────────────────────────────────────────────────────────────────────────────────────────
def skill(d: Path, name: str, front: str) -> None:
    (d / name).mkdir(parents=True)
    (d / name / "SKILL.md").write_text(f"---\n{front}\n---\n\nbody\n", encoding="utf-8")


def test_frontmatter_that_parses_finds_nothing(tmp_path):
    skill(tmp_path / "skills", "good", "name: good\ndescription: a plain description")
    skill(tmp_path / ".claude" / "skills" / ".hidden", "deep", "name: deep\ndescription: found inside a dot-folder")
    assert rc.part_frontmatter(tmp_path) == []


def test_frontmatter_that_does_not_parse_is_named_inside_a_dot_folder_too(tmp_path):
    skill(tmp_path / "skills", "good", "name: good\ndescription: fine")
    skill(tmp_path / "packages" / "x" / ".claude" / "skills", "bad", "name: bad\ndescription: Use when: it breaks")
    found = rc.part_frontmatter(tmp_path)
    assert len(found) == 1 and found[0].startswith("packages/x/.claude/skills/bad/SKILL.md")


# ── sentences ───────────────────────────────────────────────────────────────────────────────────────────────────────
OLD = "the server starts straight through uvx"


@pytest.fixture()
def docs(tmp_path: Path) -> Path:
    top = tmp_path / "docs"
    folder = top / "base" / "chaincompiler"
    folder.mkdir(parents=True)
    git(top, "init", "-q")
    (folder / "DESIGN.md").write_text("# design\n\nThe launcher answers at once.\n", encoding="utf-8")
    (folder / "README.md").write_text(f"# readme\n\n## Changelog\n\n### v0.1.0 — d\n- Promote a chain to golden.\n"
                                      f"- the old reading: {OLD}\n\n## Status\n\nThe launcher answers at once.\n",
                                      encoding="utf-8")
    (folder / "CHANGELOG.md").write_text(f"{OLD}\n", encoding="utf-8")
    (folder / "site").mkdir()
    (folder / "site" / "data.json").write_text(f'{{"changelog": ["{OLD}"]}}\n', encoding="utf-8")
    goals = top / ".claude" / "goals"
    (goals / "a-goal" / "proofs").mkdir(parents=True)
    (goals / "a-goal.md").write_text(f"- C1 · a condition, never reworded: {OLD}\n", encoding="utf-8")
    (goals / "a-goal" / "proofs" / "C1.md").write_text(f"measured then: {OLD}\n", encoding="utf-8")
    commit_all(top)
    return folder


def plant(docs: Path, rel: str, text: str) -> None:
    (docs / rel).write_text(text, encoding="utf-8")
    commit_all(docs.parents[1])


def test_sentences_in_the_histories_alone_find_nothing(docs):
    assert rc.part_sentences(docs, [OLD]) == []


def test_a_replaced_sentence_still_read_is_named(docs):
    plant(docs, "DESIGN.md", f"# design\n\n{OLD}\n")
    assert rc.part_sentences(docs, [OLD]) == [f"base/chaincompiler/DESIGN.md:3: still reads the replaced {OLD!r}"]


def test_a_replaced_sentence_wrapped_across_two_lines_is_named(docs):
    plant(docs, "DESIGN.md", "# design\n\nThe plugin says the server starts\nstraight through uvx, as it did.\n")
    assert rc.part_sentences(docs, [OLD]) == [f"base/chaincompiler/DESIGN.md:3: still reads the replaced {OLD!r}"]


def test_a_replaced_sentence_in_the_readme_past_its_changelog_is_named(docs):
    text = (docs / "README.md").read_text(encoding="utf-8").replace("The launcher answers at once.", OLD)
    plant(docs, "README.md", text)
    found = rc.part_sentences(docs, [OLD])
    assert len(found) == 1 and found[0].startswith("base/chaincompiler/README.md:11: still reads the replaced")


def test_a_replaced_sentence_on_a_line_naming_git_grep_is_named(docs):
    plant(docs, "DESIGN.md", f"# design\n\nrun `git grep` and you find {OLD}\nsee /Users/someone/x in git grep\n")
    found = rc.part_sentences(docs, [OLD])
    assert f"base/chaincompiler/DESIGN.md:3: still reads the replaced {OLD!r}" in found
    assert "base/chaincompiler/DESIGN.md:4: names a machine path" in found


def test_no_replaced_file_is_named(docs):
    assert rc.part_sentences(docs, None) == [
        "no --replaced file was given, so no reading the release replaced was searched for — give the lines its diff "
        "removes, or an empty file when it replaced none"]


def test_the_flows_own_readings_are_named(docs):
    (docs / "notes.md").write_text("Promote a chain to golden\nsee /Users/someone/x\nand ~/somewhere\n", encoding="utf-8")
    (docs / ".claude").mkdir()
    (docs / ".claude" / "rule.md").write_text("descend with `cat SKILL.md`\n", encoding="utf-8")
    commit_all(docs.parents[1])
    found = rc.part_sentences(docs, [])
    assert any("notes.md:1: `Promote a chain to golden`" in f for f in found)
    assert any("notes.md:2: names a machine path" in f for f in found)
    assert any("notes.md:3: names a `~/<name>`" in f for f in found)
    assert any(".claude/rule.md:1: descends with `cat `" in f for f in found)


def test_the_folder_itself_states_no_replaced_flow_reading():
    # this folder at its tip: the flow's own readings are absent, the lines stating these checks excepted
    assert rc.part_sentences(REPO, []) == []


# ── publish ─────────────────────────────────────────────────────────────────────────────────────────────────────────
PUBLISHER = REPO.parents[1] / "scalable-publishing"
needs_home = pytest.mark.skipif(not (PUBLISHER / "bin" / "publish_unit.sh").is_file(),
                                reason="the publish dry run runs from the source home, beside scalable-publishing")


def source_home(tmp_path: Path, drop: str | None = None) -> Path:
    """A stand-in source home: this folder committed at base/chaincompiler, scalable-publishing's publisher beside it."""
    top = tmp_path / "home"
    folder = top / "base" / "chaincompiler"
    folder.mkdir(parents=True)
    git(top, "init", "-q")
    rc.extract(*rc.toplevel(REPO), folder)
    if drop:
        (folder / drop).unlink()
    for part in ("bin", "templates"):
        shutil.copytree(PUBLISHER / part, top / "scalable-publishing" / part)
    shutil.copy2(PUBLISHER / "publish-manifest.json", top / "scalable-publishing" / "publish-manifest.json")
    commit_all(top)
    return folder


def public(tmp_path: Path, readme: str) -> Path:
    pub = tmp_path / "public"
    pub.mkdir()
    git(pub, "init", "-q")
    (pub / "README.md").write_text(readme, encoding="utf-8")
    commit_all(pub, "the public repository before the release")
    return pub


BEFORE = "# chaincompiler\n\n## Changelog\n\n### v0.0.1 — d\n- before\n"


@needs_home
def test_a_publish_carrying_a_new_changelog_entry_finds_nothing(tmp_path):
    folder = source_home(tmp_path)
    assert rc.part_publish(folder, sys.executable, str(public(tmp_path, BEFORE))) == []


@needs_home
def test_a_publish_with_no_new_changelog_entry_is_named(tmp_path):
    folder = source_home(tmp_path)
    pub = public(tmp_path, (REPO / "README.md").read_text(encoding="utf-8"))   # the public side already holds it
    found = rc.part_publish(folder, sys.executable, str(pub))
    assert found and found[0].startswith("check_changelog.py --require-new on the published result")


@needs_home
def test_a_publish_that_leaves_a_generated_file_untracked_is_named(tmp_path):
    folder = source_home(tmp_path, drop="assets/roadmap.svg")
    found = rc.part_publish(folder, sys.executable, str(public(tmp_path, BEFORE)))
    assert found == ["the published result leaves assets/roadmap.svg untracked once `update_site.py` writes it"]


# ── tee ─────────────────────────────────────────────────────────────────────────────────────────────────────────────
def tee_log(discover_answered: float = 0.0, init_answered: float = 0.03, server_up: float | None = 46.86,
            call_sent: float = 46.89, server_answer: bool = True, answer_twice: bool = False, tools: dict = TOOLS,
            result: str = "2") -> str:
    def line(t: float, tag: str, msg: dict) -> str:
        return f"[{t:8.3f}] {tag} {json.dumps(msg)}"
    rows = [line(0.00, "C->L", {"jsonrpc": "2.0", "id": "probe", "method": "server/discover", "params": {}}),
            line(discover_answered, "L->C", {"jsonrpc": "2.0", "id": "probe", "error": {"code": -32601, "message": "no"}}),
            line(discover_answered + 0.02, "C->L", {"jsonrpc": "2.0", "id": 0, "method": "initialize", "params": {}}),
            line(init_answered + discover_answered, "L->C", {"jsonrpc": "2.0", "id": 0,
                                                            "result": {"protocolVersion": "2025-11-25"}}),
            line(0.06, "L->S", {"jsonrpc": "2.0", "id": rc.OWN_INIT, "method": "initialize"}),
            line(0.06, "C->L", {"jsonrpc": "2.0", "method": "notifications/initialized"}),
            line(0.06, "C->L", {"jsonrpc": "2.0", "id": 1, "method": "tools/list"}),
            line(0.07, "L->C", {"jsonrpc": "2.0", "id": 1, "result": tools}),
            line(3.40, "C->L", {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "si_interpret"}})]
    if server_up is not None:
        rows.append(line(server_up, "S->L", {"jsonrpc": "2.0", "id": rc.OWN_INIT, "result": {"protocolVersion": "x"}}))
    rows += [line(46.88, "L->S", {"jsonrpc": "2.0", "method": "notifications/initialized"}),
             line(call_sent, "L->S", {"jsonrpc": "2.0", "id": 2, "method": "tools/call"})]
    answer = {"jsonrpc": "2.0", "id": 2, "result": {"content": [{"type": "text", "text": result}],
                                                   "structuredContent": {"result": result}}}
    if server_answer:
        rows.append(line(48.54, "S->L", answer))
    rows += [line(48.55, "L->C", answer)] * (2 if answer_twice else 1)
    return "\n".join(sorted(rows, key=lambda r: float(r[1:9]))) + "\n"


def test_a_tee_log_of_a_good_connection_finds_nothing():
    assert rc.read_tee_log(tee_log(), TOOLS, delay=35) == []


def test_an_opening_probe_held_until_the_server_is_up_is_named():
    # the launcher holds server/discover 25 s, then answers the initialize that follows at once
    found = rc.read_tee_log(tee_log(discover_answered=25.0), TOOLS)
    assert "the client's opening server/discover was not refused within one second (answered after 25.00s)" in found
    assert "initialize was not answered within one second of the client's first message (after 25.03s)" in found


def test_an_initialize_answered_late_is_named():
    assert rc.read_tee_log(tee_log(init_answered=2.0), TOOLS) == \
        ["initialize was not answered within one second of the client's first message (after 2.00s)"]


def test_a_tools_list_that_is_not_the_stored_one_is_named():
    assert rc.read_tee_log(tee_log(tools={"tools": []}), TOOLS) == ["tools/list was not answered with server/tools.json"]


def test_a_call_written_before_the_real_server_answered_is_named():
    found = rc.read_tee_log(tee_log(call_sent=3.41), TOOLS, delay=35)
    assert "the tools/call was not written to the real server after the real server's own initialize answer" in found
    assert "the tools/call was written to the server 3.41s in, before the 35s it was held back" in found


def test_a_log_where_the_real_server_never_answered_is_named():
    found = rc.read_tee_log(tee_log(server_up=None, server_answer=False), TOOLS)
    assert "the log shows no answer of the real server's own to the launcher's initialize" in found
    assert "the log shows no answer of the real server's own to the tools/call" in found


def test_a_request_answered_twice_is_named():
    assert rc.read_tee_log(tee_log(answer_twice=True), TOOLS) == \
        ["the client's tools/call (id 2) was answered 2 times, not once"]


def test_a_call_not_answered_2_is_named():
    assert rc.read_tee_log(tee_log(result="3"), TOOLS) == ["the tools/call was not answered 2"]


def test_an_empty_log_is_named():
    assert rc.read_tee_log("", TOOLS) == ["the log holds no client message"]


def test_the_command_exits_1_naming_each_finding_0_with_none_and_1_when_it_refuses(tmp_path, monkeypatch, capsys):
    # the command over one part, through its own `--tee-log` path; the tip check is stood in for (its refusals are
    # planted above), since these tests run in environments whose packages resolve elsewhere
    monkeypatch.setattr(rc, "preflight", lambda root, py: [])
    bad, good = tmp_path / "bad.log", tmp_path / "good.log"
    bad.write_text(tee_log(result="3"), encoding="utf-8")
    good.write_text(tee_log(), encoding="utf-8")
    assert rc.main(["--only", "tee", "--tee-log", str(bad), "--replaced", os.devnull]) == 1
    out = capsys.readouterr().out
    assert "✗ the tools/call was not answered 2" in out and "✗ the release check found 1 thing(s) to fix" in out
    assert rc.main(["--only", "tee", "--tee-log", str(good), "--replaced", os.devnull]) == 0
    assert "✓ the release check found nothing (tee)" in capsys.readouterr().out
    monkeypatch.setattr(rc, "preflight", lambda root, py: ["the folder has uncommitted changes, so the tip is not what is checked"])
    assert rc.main(["--only", "tee", "--tee-log", str(good), "--replaced", os.devnull]) == 1
    assert "✗ the release check refuses" in capsys.readouterr().out


def test_the_session_result_is_the_tools_answer_2_in_either_form():
    assert rc.result_is_two("2") and rc.result_is_two(" `2`\n")
    assert rc.result_is_two('{"result":"2"}') and rc.result_is_two('{"result": 2}')
    assert rc.result_is_two('```json\n{"result":"2"}\n```') and rc.result_is_two('`{"result":"2"}`')
    assert not rc.result_is_two("12") and not rc.result_is_two("error -32602") and not rc.result_is_two("")
    assert not rc.result_is_two('{"result":"3"}') and not rc.result_is_two('{"result":"2","isError":true}')
    assert not rc.result_is_two('{"value":"2"}') and not rc.result_is_two("[2]") and not rc.result_is_two('{"result":"2"} done')
