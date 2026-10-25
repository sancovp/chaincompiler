#!/usr/bin/env python3
"""plugin_proof.py — the proof of the plugin, at a clean seat (DESIGN.md §16).

It keeps THE CLEAN SEAT's discipline (CompiloApe's `DESIGN.md` §1, its `tests/clean_seat.py`): a fresh `seat-*` folder
under a root in scratch space with no `CLAUDE.md` and no `.claude/rules/` above it, marked by the file `new` writes; a
session there runs in an environment holding only HOME, USER, LOGNAME, PATH, LANG, TERM and TMPDIR — the seat's own
empty `UV_CACHE_DIR` added — without the user's settings, stdin closed. Every grade is read from the transcript and the
files, never from the session's account.

    python3 plugin_proof.py new ROOT                       make a seat, print its path
    python3 plugin_proof.py install SEAT --version V [--marketplace sancovp/chaincompiler]
                                                           signed out, into the seat's empty CLAUDE_CONFIG_DIR: add the
                                                           marketplace, install the plugin, list it; check the cached
                                                           copy; print a JSON report, exit 0 only when every check holds
    python3 plugin_proof.py run SEAT --prompt-file F --out T.jsonl [--allowed-tools …]
                                                           check the seat's python3 imports none of the fifteen, then a
                                                           headless session on the user's own login whose only addition
                                                           is the cached copy; stream-json transcript to --out
    python3 plugin_proof.py grade T.jsonl --work DIR --version V [--allowed-tools …]
                                                           grade a session from its transcript and the files in DIR
    python3 plugin_proof.py remove ROOT SEAT               remove a seat — refused unless SEAT is a marked `seat-*`
                                                           folder directly inside ROOT, and not a link
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

PREFIX, MARKER = "seat-", ".plugin-seat"
KEEP_ENV = ("HOME", "USER", "LOGNAME", "PATH", "LANG", "TERM", "TMPDIR")
REPO = Path(__file__).resolve().parent.parent
PLUGIN, MARKETPLACE = "chaincompiler", "chaincompiler"
SERVER = "self-interpreter"
# the eight capability skills and the distributions each one's uv line names (DESIGN.md §16)
CAPABILITIES = {"forge-attention-chain": "chaincompiler-accc", "forge-cor": "corcc", "forge-skillchain": "sccc",
                "construct-language": "chainaios", "make-prompt": "agent-prompt-engineering",
                "make-persona": "agent-prompt-engineering", "big-generator": "agent-prompt-engineering",
                "persona-generator": "agent-prompt-engineering"}
MODULES = ("rulecatcher", "honeyc", "dietc", "skillchain", "chaincompiler", "accc", "corcc", "sccc", "chainaios", "si",
           "archetype", "framework", "glyphsteer", "personacc", "personapack", "goldenreq")
SKILL_WRITE = re.compile(r">>?\s*[\"']?[^\s\"'<>|;&]*SKILL\.md|\btee\s+(?:-a\s+)?[\"']?[^\s\"']*SKILL\.md|"
                         r"\b(?:cp|mv|install)\s+.*\S*SKILL\.md[\"']?\s*$")


# ── the seat ────────────────────────────────────────────────────────────────────────────────────────────────────────
def loaded_from_above(folder: Path) -> list[str]:
    return [str(f) for d in folder.parents
            for f in (d / "CLAUDE.md", d / "CLAUDE.local.md", d / ".claude" / "CLAUDE.md", d / ".claude" / "rules")
            if f.exists()]


def is_seat(s: Path) -> bool:
    return s.is_dir() and not s.is_symlink() and s.name.startswith(PREFIX) and (s / MARKER).is_file()


def seat_env(seat: Path, **extra: str) -> dict[str, str]:
    env = {k: os.environ[k] for k in KEEP_ENV if k in os.environ}
    env.update(extra)
    return env


def strip(text: str, seat: Path) -> str:
    """Name the seat `<seat>` and the home `~`, so a proof names no machine."""
    return text.replace(str(seat), "<seat>").replace(str(Path.home()), "~")


def cmd_new(root: str) -> int:
    base = Path(root).resolve()
    above = loaded_from_above(base / "x")
    if above:
        print(json.dumps({"ok": False, "why": "a CLAUDE.md or a .claude/rules/ sits above the seat", "found": above}))
        return 1
    base.mkdir(parents=True, exist_ok=True)
    seat = Path(tempfile.mkdtemp(prefix=PREFIX, dir=base))
    (seat / MARKER).write_text("a clean seat for the plugin proof, made by plugin_proof.py new\n")
    print(seat)
    return 0


def cmd_remove(root: str, seat: str) -> int:
    base, given = Path(root).resolve(), Path(seat)
    target = given.resolve()
    if given.is_symlink() or target.parent != base or not is_seat(target):
        print(json.dumps({"ok": False, "refused": str(given), "why": f"not a {PREFIX}* folder directly inside {base}"}))
        return 1
    shutil.rmtree(target)
    print(json.dumps({"ok": True, "removed": str(target)}))
    return 0


def require_seat(seat: str) -> Path:
    s = Path(seat).resolve()
    if not is_seat(s):
        raise SystemExit(json.dumps({"ok": False, "refused": seat, "why": f"not a seat made by `new` (no {MARKER})"}))
    return s


def run(argv: list[str], env: dict, cwd: Path, seat: Path) -> dict:
    r = subprocess.run(argv, env=env, cwd=cwd, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=900)
    return {"command": strip(" ".join(argv), seat), "exit": r.returncode,
            "output": strip((r.stdout + r.stderr).strip(), seat)[-4000:]}


# ── the install ─────────────────────────────────────────────────────────────────────────────────────────────────────
def shipped_skills(root: Path) -> list[str]:
    return sorted(p.relative_to(root / "skills").as_posix() for p in (root / "skills").rglob("SKILL.md"))


def cmd_install(seat: str, version: str, marketplace: str) -> int:
    s = require_seat(seat)
    config = s / "config"
    if config.exists() and any(config.iterdir()):
        print(json.dumps({"ok": False, "why": "the seat's configuration directory is not empty"}))
        return 1
    config.mkdir(exist_ok=True)
    env = seat_env(s, CLAUDE_CONFIG_DIR=str(config))
    steps = [run(["claude", "auth", "status"], env, s, s),
             run(["claude", "plugin", "marketplace", "add", marketplace], env, s, s),
             run(["claude", "plugin", "install", f"{PLUGIN}@{MARKETPLACE}"], env, s, s),
             run(["claude", "plugin", "list", "--json"], env, s, s)]
    signed_out = steps[0]["exit"] != 0 or "not logged in" in steps[0]["output"].lower() \
        or '"loggedin": false' in steps[0]["output"].lower().replace(" ", "")
    listed = []
    try:
        listed = json.loads(subprocess.run(["claude", "plugin", "list", "--json"], env=env, cwd=s, capture_output=True,
                                           stdin=subprocess.DEVNULL, text=True).stdout)
    except (json.JSONDecodeError, ValueError):
        pass
    entry = next((p for p in listed if p.get("id") == f"{PLUGIN}@{MARKETPLACE}"), {})
    cached = Path(entry.get("installPath", "")) if entry.get("installPath") else None
    mcp = json.loads((cached / ".mcp.json").read_text()) if cached and (cached / ".mcp.json").is_file() else {}
    server = mcp.get("mcpServers", {}).get(SERVER, {})
    cached_skills = shipped_skills(cached) if cached and (cached / "skills").is_dir() else []
    checks = {
        "signed_out": signed_out,
        "marketplace_added": steps[1]["exit"] == 0,
        "plugin_installed": steps[2]["exit"] == 0,
        "listed_enabled_at_the_release": entry.get("enabled") is True and entry.get("version") == version,
        "cached_copy_holds_every_shipped_skill": bool(cached_skills) and cached_skills == shipped_skills(REPO),
        "mcp_pins_the_release": server.get("command") == "uvx"
                                and server.get("args") == ["--from", f"chaincompiler-si=={version}", "si-server"],
    }
    report = {"checks": checks, "pass": all(checks.values()), "steps": steps,
              "cached_copy": strip(str(cached), s) if cached else None, "cached_skills": cached_skills,
              "cached_mcp": mcp, "listed": {k: entry.get(k) for k in ("id", "version", "enabled", "scope")}}
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["pass"] else 1


# ── the run ─────────────────────────────────────────────────────────────────────────────────────────────────────────
def python_imports_none(env: dict, cwd: Path) -> dict:
    """The seat's `python3` imports none of the fifteen — so nothing the session runs can come from this machine."""
    probe = ("import importlib.util, json; "
             f"print(json.dumps({{m: importlib.util.find_spec(m) is not None for m in {list(MODULES)!r}}}))")
    r = subprocess.run(["python3", "-c", probe], env=env, cwd=cwd, capture_output=True, text=True, stdin=subprocess.DEVNULL)
    found = json.loads(r.stdout) if r.returncode == 0 else {}
    which = subprocess.run(["sh", "-c", "command -v python3"], env=env, capture_output=True, text=True).stdout.strip()
    return {"python3": which, "importable": sorted(m for m, ok in found.items() if ok), "checked": bool(found)}


def cmd_run(seat: str, prompt_file: str, out: str, allowed: list[str]) -> int:
    s = require_seat(seat)
    listed = json.loads(subprocess.run(["claude", "plugin", "list", "--json"], cwd=s, capture_output=True, text=True,
                                       stdin=subprocess.DEVNULL,
                                       env=seat_env(s, CLAUDE_CONFIG_DIR=str(s / "config"))).stdout or "[]")
    entry = next((p for p in listed if p.get("id") == f"{PLUGIN}@{MARKETPLACE}"), None)
    if not entry:
        print(json.dumps({"ok": False, "why": "the plugin is not installed in this seat — run `install` first"}))
        return 1
    uv_cache = s / "uv-cache"
    if uv_cache.exists() and any(uv_cache.iterdir()):
        print(json.dumps({"ok": False, "why": "the seat's uv cache is not empty"}))
        return 1
    uv_cache.mkdir(exist_ok=True)
    work = s / "work"
    work.mkdir(exist_ok=True)
    env = seat_env(s, UV_CACHE_DIR=str(uv_cache))
    pre = python_imports_none(env, work)
    (Path(out).with_suffix(".env.json")).write_text(json.dumps(
        {**pre, "env_keys": sorted(env), "uv_cache_empty_before": True, "allowed_tools": allowed,
         "plugin_dir": strip(entry["installPath"], s)}, indent=2))
    if not pre["checked"] or pre["importable"]:
        print(json.dumps({"ok": False, "why": "the seat's python3 imports some of the fifteen", "pre": pre}))
        return 1
    cmd = ["claude", "-p", Path(prompt_file).read_text(), "--output-format", "stream-json", "--verbose",
           "--setting-sources", "project,local", "--plugin-dir", entry["installPath"]]
    if allowed:
        cmd += ["--allowedTools", *allowed]
    with open(out, "w") as sink:
        code = subprocess.run(cmd, cwd=work, env=env, stdin=subprocess.DEVNULL, stdout=sink,
                              stderr=subprocess.STDOUT).returncode
    print(json.dumps({"ok": code == 0, "exit": code, "transcript": strip(out, s), "pre": pre}))
    return code


# ── the grade ───────────────────────────────────────────────────────────────────────────────────────────────────────
def events(path: Path) -> list[dict]:
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    return out


def tool_calls(evs: list[dict]) -> list[dict]:
    """Every tool call in order, each with the text of its result and whether that result was an error."""
    calls, by_id = [], {}
    for e in evs:
        if e.get("type") == "assistant":
            for c in e["message"].get("content", []):
                if c.get("type") == "tool_use":
                    call = {"name": c["name"], "input": c["input"], "result": "", "error": False, "answered": False}
                    calls.append(call)
                    by_id[c.get("id")] = call
        elif e.get("type") == "user":
            content = e["message"].get("content", [])
            for c in content if isinstance(content, list) else []:
                if isinstance(c, dict) and c.get("type") == "tool_result" and c.get("tool_use_id") in by_id:
                    body = c.get("content")
                    if isinstance(body, list):
                        body = " ".join(x.get("text", "") for x in body if isinstance(x, dict))
                    by_id[c["tool_use_id"]].update(result=str(body), error=bool(c.get("is_error")), answered=True)
    return calls


def frontmatter_ok(p: Path) -> bool:
    import yaml
    m = re.match(r"^---\n(.*?)\n---\n", p.read_text(encoding="utf-8"), re.S)
    try:
        fm = yaml.safe_load(m.group(1)) if m else None
    except yaml.YAMLError:
        return False
    return isinstance(fm, dict) and isinstance(fm.get("name"), str) and isinstance(fm.get("description"), str)


def grade(transcript: Path, work: Path, version: str, allowed: list[str]) -> dict:
    evs = events(transcript)
    calls = tool_calls(evs)
    init = next((e for e in evs if e.get("type") == "system" and e.get("subtype") == "init"), {})
    result = next((e for e in reversed(evs) if e.get("type") == "result"), {})
    servers = init.get("mcp_servers", []) or []
    ours = [m for m in servers if str(m.get("name", "")).split(":")[-1] == SERVER]
    others = [m.get("name") for m in servers if m not in ours]
    norm = lambda n: re.sub(r"[^A-Za-z0-9]", "_", n)
    granted_others = [t for t in allowed for o in others if norm(t).startswith(f"mcp__{norm(o)}__")]
    server_calls = [c for c in calls if c["name"].startswith("mcp__") and SERVER.replace("-", "_") in norm(c["name"])]
    skill_seen = [name for name in CAPABILITIES for c in calls
                  if (c["name"] == "Skill" and name in json.dumps(c["input"]))
                  or (c["name"] == "Read" and c["input"].get("file_path", "").endswith(f"{name}/SKILL.md"))]
    uv_runs = [c for c in calls if c["name"] == "Bash" and not c["error"] and c["answered"]
               and any(re.search(rf"uv run --no-project\b.*--with\s+\"?{re.escape(d)}(\[[^\]]*\])?"
                                 rf"{'==' + re.escape(version) if d != 'agent-prompt-engineering' else '>=0.2.0'}",
                                 c["input"].get("command", ""))
                       for n, d in CAPABILITIES.items() if n in skill_seen)]
    hand_written = sorted({c["input"].get("file_path", "") for c in calls if c["name"] in ("Write", "Edit", "MultiEdit")
                           and c["input"].get("file_path", "").endswith("SKILL.md")}
                          | {c["input"].get("command", "")[:200] for c in calls if c["name"] == "Bash"
                             and SKILL_WRITE.search(c["input"].get("command", ""))})
    made = sorted(work.rglob("SKILL.md")) if work.is_dir() else []
    parsed = [p for p in made if frontmatter_ok(p)]
    checks = {
        "server_connected": bool(ours) and all(m.get("status") == "connected" for m in ours),
        "other_servers_granted_no_tool": not granted_others,
        "server_tool_answered_without_error": any(c["answered"] and not c["error"] for c in server_calls),
        "capability_skill_followed": bool(skill_seen),
        "its_python_ran_through_its_uv_line": bool(uv_runs),
        "a_skill_dir_written_whose_frontmatter_parses": bool(parsed) and not hand_written,
        "session_succeeded": result.get("subtype") == "success" and not result.get("is_error"),
    }
    return {"checks": checks, "pass": all(checks.values()),
            "evidence": {"mcp_servers": servers, "other_servers": others, "allowed_tools": allowed,
                         "server_calls": [{"name": c["name"], "error": c["error"], "result": c["result"][:300]}
                                          for c in server_calls],
                         "capability_skills_seen": sorted(set(skill_seen)),
                         "uv_runs": [c["input"].get("command", "")[:400] for c in uv_runs],
                         "skill_dirs_made": [p.relative_to(work).as_posix() for p in made],
                         "frontmatter_parses": [p.relative_to(work).as_posix() for p in parsed],
                         "hand_written_skill_files": hand_written,
                         "tool_calls": len(calls), "result": (result.get("result") or "")[:800],
                         "cost_usd": result.get("total_cost_usd"), "turns": result.get("num_turns")}}


def cmd_grade(transcript: str, work: str, version: str, allowed: list[str]) -> int:
    g = grade(Path(transcript), Path(work), version, allowed)
    print(json.dumps(g, indent=2, ensure_ascii=False))
    return 0 if g["pass"] else 1


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="the proof of the plugin, at a clean seat")
    sub = ap.add_subparsers(dest="cmd", required=True)
    n = sub.add_parser("new"); n.add_argument("root")
    i = sub.add_parser("install"); i.add_argument("seat"); i.add_argument("--version", required=True)
    i.add_argument("--marketplace", default="sancovp/chaincompiler")
    r = sub.add_parser("run"); r.add_argument("seat"); r.add_argument("--prompt-file", required=True)
    r.add_argument("--out", required=True); r.add_argument("--allowed-tools", nargs="*", default=[])
    g = sub.add_parser("grade"); g.add_argument("transcript"); g.add_argument("--work", required=True)
    g.add_argument("--version", required=True); g.add_argument("--allowed-tools", nargs="*", default=[])
    rm = sub.add_parser("remove"); rm.add_argument("root"); rm.add_argument("seat")
    a = ap.parse_args(argv)
    if a.cmd == "new":
        return cmd_new(a.root)
    if a.cmd == "install":
        return cmd_install(a.seat, a.version, a.marketplace)
    if a.cmd == "run":
        return cmd_run(a.seat, a.prompt_file, a.out, a.allowed_tools)
    if a.cmd == "grade":
        return cmd_grade(a.transcript, a.work, a.version, a.allowed_tools)
    return cmd_remove(a.root, a.seat)


if __name__ == "__main__":
    sys.exit(main())
