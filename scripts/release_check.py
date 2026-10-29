#!/usr/bin/env python3
"""release_check.py — a release's own checks in one command, run on its tip before its PR is opened (the release flow's
THE PROOF, `.claude/rules/22-seq-chaincompiler-release.md`).

    python3 scripts/release_check.py --replaced FILE [--only PART …] [--public URL] [--tee-log LOG]

It refuses to run on a folder with uncommitted changes, or with a `python3` whose packages resolve outside this tree's
`packages/`: the frontmatter sweep and the tee probe read the working tree, and every generator runs from the
installed packages, so only a clean tree with its own packages imported is the tip being proven. Run it with the
`python3` of the editable environment `./install.sh` built from this tree. The parts, each naming every finding:

  generated    in a copy of the tip as committed: `update_site.py`, `build_meta_ape_skills.py`, bigdog's
               `build_grade_legend()`, every GBA under `personas/` re-applied through `_apply_tree`, and
               `build_server_tools.py --check` — each output equal to the committed file, a generated file the commit
               lacks named as the public `deploy.yml` names an untracked one, and the count of stub bodies unchanged
  frontmatter  every `SKILL.md` under `skills/`, `.claude/skills/`, `personas/` and `packages/`, dot-folders entered,
               parses to a mapping with a string `name` and a string `description`
  sentences    each line of `--replaced` — a reading the release rewrote away, taken from the lines its diff removes —
               found nowhere in the source home's tracked text, searched with whitespace flattened so a reading wrapped
               across two lines is found, but in its histories: every `CHANGELOG.md`, the README's `## Changelog`
               section up to the next `## ` heading, `site/data.json` (which renders that changelog), and every goal
               file and goal proof under `.claude/goals/` (a merged goal's conditions are never reworded); and always
               the readings the flow names: `Promote a chain to golden` outside those histories, `` `cat `` in
               `packages/*/src` and `.claude/`, a machine path or a `~/<name>` other than `~/.claude` in a tracked file
  publish      the publish dry run: the public repository cloned read-only into a local bare copy, the source home's
               `scalable-publishing/bin/publish_unit.sh` mirroring the tip into it, then in a clone of the result
               `check_changelog.py --require-new`, `update_site.py` exiting 0 and changing no generated file nor leaving
               one untracked (both halves of `deploy.yml`'s gate), no dangling link; the files the publish commit
               changes are printed for the reader
  tee          the tee probe: a headless `claude -p` at a marked seat whose one server is this tip's `server/launch.py`
               behind a wrapper that logs both its streams and the real server's output, whole, and starts the real
               server after Claude Code's thirty seconds, asked to call `si_interpret` with `1+1` — or, given
               `--tee-log`, a log that wrapper wrote — read for: a first client message, a `server/discover` that opens
               it refused within one second, `initialize` answered within one second of that first message, `tools/list`
               answered with `server/tools.json`, the `tools/call` written to the real server only after the real
               server's own answer to the launcher's `initialize` and no sooner than its delay, and answered `2`, every
               client request answered exactly once; when it ran the session, the server listed `connected` at its
               start and its result the tool's answer, `2`, in either form the tool returns it (its text `2` or its
               structured content `{"result":"2"}`); and the real server's own answers to `server/discover` and
               `prompts/list`, asked of `python3 -m si.server` directly, printed for the reader

Exit 0 with no finding · 1 naming each finding.
"""
from __future__ import annotations

import argparse
import bisect
import contextlib
import io
import json
import os
import queue
import re
import subprocess
import sys
import tarfile
import tempfile
import threading
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PARTS = ("generated", "frontmatter", "sentences", "publish", "tee")
GENERATED = ("site/data.json", "assets/roadmap.svg", ".claude/rules/chaincompiler_states.md")
SKILL_ROOTS = ("skills", ".claude/skills", "personas", "packages")
IMPORTED = ("chainaios", "chaincompiler", "accc", "corcc", "sccc", "si", "honeyc", "rulecatcher")
MACHINE = re.compile(r"/Users/[A-Za-z]|/home/[A-Za-z]|/private/(tmp|var)/|/var/folders")
MACHINE_STATED = "/private/(tmp|var)/|/var/folders"          # a line stating the pattern itself is no finding
HOME_NAME = re.compile(r"~/[A-Za-z_]")
STUB_RE = re.compile(r"SkillTree [a-z]* node `")
TEE_LINE = re.compile(r"^\[\s*([0-9.]+)\]\s+(C->L|L->C|L->S|S->L)\s+(.*)$")
TEE_DELAY = 35                                                # longer than Claude Code's thirty seconds
OWN_INIT = "server/launch.py:initialize"                      # the id of the launcher's own initialize to the server


# ── where the tip is ────────────────────────────────────────────────────────────────────────────────────────────────
def git(top: Path, *args: str, check: bool = True) -> str:
    r = subprocess.run(["git", "-C", str(top), *args], capture_output=True, text=True)
    if check and r.returncode:
        raise SystemExit(f"git {' '.join(args)} failed: {r.stderr.strip()}")
    return r.stdout


def toplevel(root: Path) -> tuple[Path, str]:
    """The repository holding the folder, and the folder's path inside it ('' when the folder is the repository)."""
    top = Path(git(root, "rev-parse", "--show-toplevel").strip())
    rel = root.resolve().relative_to(top.resolve()).as_posix()
    return top, "" if rel == "." else rel


def extract(top: Path, prefix: str, dst: Path) -> None:
    """The folder as committed at HEAD — tracked files only — written into dst."""
    data = subprocess.run(["git", "-C", str(top), "archive", "--format=tar", f"HEAD:{prefix}" if prefix else "HEAD"],
                          capture_output=True, check=True).stdout
    dst.mkdir(parents=True, exist_ok=True)
    with tarfile.open(fileobj=io.BytesIO(data)) as t:
        t.extractall(dst, filter="data") if sys.version_info >= (3, 12) else t.extractall(dst)


def tree_diff(a: Path, b: Path, skip: tuple[str, ...] = (".index.db", "__pycache__")) -> list[str]:
    """Every path under a or b that one lacks or whose bytes differ."""
    def files(d: Path) -> set[str]:
        return {p.relative_to(d).as_posix() for p in d.rglob("*")
                if (p.is_file() or p.is_symlink()) and not set(p.relative_to(d).parts) & set(skip)} if d.exists() else set()
    fa, fb = files(a), files(b)
    out = sorted(fa ^ fb)
    out += sorted(r for r in fa & fb if (a / r).read_bytes() != (b / r).read_bytes())
    return out


def run(cmd: list[str], cwd: Path, env: dict | None = None, timeout: int = 1800) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True, timeout=timeout)


def tail(r: subprocess.CompletedProcess, n: int = 300) -> str:
    return (r.stdout + r.stderr).strip()[-n:]


# ── the tip being proven ────────────────────────────────────────────────────────────────────────────────────────────
def preflight(root: Path, py: str) -> list[str]:
    """Refused: uncommitted changes in the folder, or a `python3` whose packages resolve outside this tree's packages/."""
    found = []
    dirty = git(root, "status", "--porcelain", "--", ".").strip()
    if dirty:
        found.append("the folder has uncommitted changes, so the tip is not what is checked:\n"
                     + "\n".join("      " + l for l in dirty.splitlines()[:20]))
    probe = ("import importlib.util, json; print(json.dumps({m: (importlib.util.find_spec(m).origin "
             f"if importlib.util.find_spec(m) else None) for m in {list(IMPORTED)!r}}}))")
    r = run([py, "-c", probe], root)
    where = json.loads(r.stdout) if r.returncode == 0 else {}
    packages = (root / "packages").resolve()
    for m in IMPORTED:
        origin = where.get(m)
        print(f"  {m} -> {origin}", flush=True)
        if not origin or packages not in Path(origin).resolve().parents:
            found.append(f"{py} imports {m} from {origin or 'nowhere'}, not from this tree's packages/ — the generators "
                         "would run another tree's code")
    return found


# ── generated ───────────────────────────────────────────────────────────────────────────────────────────────────────
REAPPLY = r"""
import json
from pathlib import Path
from chainaios.gba import _apply_tree, _resolved, load_gba
for gj in sorted(Path("personas").glob("*/gba.json")):
    root = gj.parent.resolve()
    _apply_tree(load_gba(root), _resolved(json.loads(gj.read_text()), root))
    print("re-applied", gj.parent.name)
"""
LEGEND = r"""
import importlib.util
from pathlib import Path
s = importlib.util.spec_from_file_location("bigdog_build", "skills/bigdog/build.py")
m = importlib.util.module_from_spec(s)
s.loader.exec_module(m)
print(m.build_grade_legend() == Path("skills/bigdog/GRADE-LADDER.md").read_text(encoding="utf-8"))
"""


def stubs(d: Path) -> int:
    return sum(1 for p in d.rglob("SKILL.md") if STUB_RE.search(p.read_text(encoding="utf-8", errors="replace")))


def part_generated(root: Path, py: str, steps: tuple[str, ...] = ("site", "skills", "legend", "gbas", "server")) -> list[str]:
    top, prefix = toplevel(root)
    found = []
    with tempfile.TemporaryDirectory() as tmp:
        copy, committed = Path(tmp) / "copy", Path(tmp) / "committed"
        extract(top, prefix, copy)
        extract(top, prefix, committed)
        if "site" in steps:
            r = run([py, "scripts/update_site.py"], copy)
            if r.returncode:
                found.append(f"update_site.py exited {r.returncode}: {tail(r)}")
            for rel in GENERATED:
                if not (committed / rel).is_file():
                    found.append(f"{rel} is not committed — `update_site.py` writes it, and the public deploy.yml fails a "
                                 "generated file left untracked")
                elif not (copy / rel).is_file() or (copy / rel).read_bytes() != (committed / rel).read_bytes():
                    found.append(f"{rel} is stale — `update_site.py` writes it otherwise")
        if "skills" in steps:
            r = run([py, "scripts/build_meta_ape_skills.py"], copy)
            if r.returncode:
                found.append(f"build_meta_ape_skills.py exited {r.returncode}: {tail(r)}")
            found += [f"skills/{rel} is stale — `build_meta_ape_skills.py` writes it otherwise"
                      for rel in tree_diff(copy / "skills", committed / "skills")]
        if "legend" in steps:
            r = run([py, "-c", LEGEND], copy)
            if r.stdout.strip() != "True":
                found.append("skills/bigdog/GRADE-LADDER.md is not bigdog's `build_grade_legend()`"
                             + (f": {tail(r)}" if r.returncode else ""))
        if "gbas" in steps:
            before = stubs(copy / "personas")
            r = run([py, "-c", REAPPLY], copy)
            if r.returncode:
                found.append(f"re-applying the GBAs under personas/ failed: {tail(r)}")
            after = stubs(copy / "personas")
            if after != before:
                found.append(f"re-applying the GBAs changed the count of stub bodies: {before} → {after}")
            found += [f"personas/{rel} differs once its GBA is re-applied"
                      for rel in tree_diff(copy / "personas", committed / "personas")]
        if "server" in steps:
            r = run([py, "scripts/build_server_tools.py", "--check"], copy, timeout=300)
            if r.returncode:
                found.append(f"server/initialize.json or server/tools.json is not the real server's: {tail(r)}")
    return found


# ── frontmatter ─────────────────────────────────────────────────────────────────────────────────────────────────────
def part_frontmatter(root: Path) -> list[str]:
    import yaml
    found = []
    for base in SKILL_ROOTS:
        for dirpath, _dirs, files in os.walk(root / base):        # enters dot-folders
            if "SKILL.md" not in files:
                continue
            p = Path(dirpath) / "SKILL.md"
            text = p.read_text(encoding="utf-8", errors="replace")
            m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
            try:
                fm = yaml.safe_load(m.group(1)) if m else None
            except yaml.YAMLError as e:
                fm, why = None, str(e).splitlines()[0]
            else:
                why = "no frontmatter" if not m else "its frontmatter is not a mapping with a string name and description"
            if not (isinstance(fm, dict) and isinstance(fm.get("name"), str) and isinstance(fm.get("description"), str)):
                found.append(f"{p.relative_to(root).as_posix()}: {why}")
    return found


# ── sentences ───────────────────────────────────────────────────────────────────────────────────────────────────────
def changelog_span(top: Path, readme: str) -> tuple[int, int] | None:
    """The README's history: the lines of its `## Changelog` section, up to the next `## ` heading."""
    text = git(top, "show", f"HEAD:{readme}", check=False).splitlines()
    start = next((i + 1 for i, l in enumerate(text) if re.match(r"^##\s+Changelog\s*$", l)), None)
    if start is None:
        return None
    end = next((i for i in range(start, len(text)) if re.match(r"^##\s", text[i])), len(text))
    return start, end


def history_line(top: Path, prefix: str, path: str, line: int) -> bool:
    """A line of the source home's histories: any `CHANGELOG.md`, the folder's README inside its `## Changelog` section,
    the folder's `site/data.json` (that changelog as `update_site.py` renders it), and every goal file and goal proof
    under `.claude/goals/` — evidence as it was measured, and conditions that are never reworded."""
    if Path(path).name == "CHANGELOG.md" or path == (f"{prefix}/site/data.json" if prefix else "site/data.json"):
        return True
    if path.startswith(".claude/goals/"):
        return True
    readme = f"{prefix}/README.md" if prefix else "README.md"
    if path == readme:
        span = changelog_span(top, readme)
        return span is not None and span[0] < line <= span[1]
    return False


def grep(top: Path, pattern: str, fixed: bool, paths: list[str], files_only: bool = False) -> list:
    args = ["grep", "-I", "-l" if files_only else "-n", "-F" if fixed else "-E", "-e", pattern, "HEAD", "--", *paths]
    out = git(top, *args, check=False)
    if files_only:
        return [l.split(":", 1)[1] for l in out.splitlines() if l.startswith("HEAD:")]
    hits = []
    for line in out.splitlines():
        m = re.match(r"^HEAD:([^:]+):(\d+):(.*)$", line)
        if m:
            hits.append((m.group(1), int(m.group(2)), m.group(3)))
    return hits


def flat_hits(top: Path, sentence: str, paths: list[str]) -> list[tuple[str, int]]:
    """Every place a sentence stands in the tracked text, its whitespace flattened — so a reading the documents wrap
    across two lines is found — as (path, the line it starts on)."""
    words = sentence.split()
    if not words:
        return []
    target = " ".join(words)
    # a file holding the sentence holds each of its words on some line: ask git for the files holding all of the
    # longest few, then read only those
    anchors = sorted(set(words), key=len, reverse=True)[:4]
    args = ["grep", "-I", "-l", "--all-match", "-F"] + [x for w in anchors for x in ("-e", w)] + ["HEAD", "--", *paths]
    candidates = [l.split(":", 1)[1] for l in git(top, *args, check=False).splitlines() if l.startswith("HEAD:")]
    hits = []
    for path in candidates:
        text = git(top, "show", f"HEAD:{path}", check=False)
        flat_parts, starts, lines, line, pos, offset = [], [], [], 1, 0, 0
        for m in re.finditer(r"\S+", text):           # one pass: each word, where it starts flattened, its line
            line += text.count("\n", pos, m.start())
            pos = m.start()
            starts.append(offset)
            offset += len(m.group()) + 1
            flat_parts.append(m.group())
            lines.append(line)
        flat = " ".join(flat_parts)
        at = flat.find(target)
        while at != -1:
            i = bisect.bisect_right(starts, at) - 1
            hits.append((path, lines[i]))
            at = flat.find(target, at + 1)
    return hits


def part_sentences(root: Path, replaced: list[str] | None) -> list[str]:
    """Not a finding: a history line; this checker's own source and tests, which carry every pattern they search for
    and plant them; for the two fixed greps alone, a line stating the grep with its pattern quoted and rule 02's own
    statement that descent is the Read tool, NOT `cat`; for the machine-path grep, a line stating the pattern itself."""
    top, prefix = toplevel(root)
    here = prefix or "."
    own = {f"{prefix}/{p}" if prefix else p for p in ("scripts/release_check.py", "scripts/tests/test_release_check.py")}
    found = []
    if replaced is None:
        found.append("no --replaced file was given, so no reading the release replaced was searched for — give the "
                     "lines its diff removes, or an empty file when it replaced none")
    for s in filter(None, (" ".join(x.split()) for x in replaced or [])):
        found += [f"{p}:{n}: still reads the replaced {s!r}" for p, n in flat_hits(top, s, ["."])
                  if not history_line(top, prefix, p, n)]
    golden = "Promote a chain to golden"
    found += [f"{p}:{n}: `{golden}` outside the histories" for p, n in flat_hits(top, golden, [here])
              if p not in own and not history_line(top, prefix, p, n)
              and not ("git grep" in git(top, "show", f"HEAD:{p}").splitlines()[n - 1] and f"'{golden}'"
                       in git(top, "show", f"HEAD:{p}").splitlines()[n - 1])]
    src = [f"{prefix}/packages/*/src" if prefix else "packages/*/src", f"{prefix}/.claude" if prefix else ".claude"]
    found += [f"{p}:{n}: descends with `cat `, not the Read tool" for p, n, t in grep(top, "`cat ", True, src)
              if p not in own and "NOT `cat`" not in t and not ("git grep" in t and "'`cat '" in t)]
    found += [f"{p}:{n}: names a machine path" for p, n, t in grep(top, MACHINE.pattern, False, [here])
              if p not in own and MACHINE_STATED not in t and not history_line(top, prefix, p, n)]
    found += [f"{p}:{n}: names a `~/<name>` other than `~/.claude`" for p, n, _ in grep(top, HOME_NAME.pattern, False, [here])
              if p not in own and not history_line(top, prefix, p, n)]
    return found


# ── publish ─────────────────────────────────────────────────────────────────────────────────────────────────────────
def unit_for(top: Path, prefix: str) -> dict | None:
    manifest = top / "scalable-publishing" / "publish-manifest.json"
    if not manifest.is_file():
        return None
    return next((u for u in json.loads(manifest.read_text(encoding="utf-8"))["units"] if u.get("subdir") == prefix), None)


def part_publish(root: Path, py: str, public: str | None = None) -> list[str]:
    top, prefix = toplevel(root)
    publisher = top / "scalable-publishing" / "bin" / "publish_unit.sh"
    unit = unit_for(top, prefix)
    if not prefix or not publisher.is_file() or not unit or not unit.get("public_repo"):
        return ["the publish dry run runs from the source home: no `scalable-publishing/bin/publish_unit.sh` or no manifest "
                f"unit with a public repository for {prefix or 'this folder'}"]
    found = []
    with tempfile.TemporaryDirectory() as tmp:
        t = Path(tmp)
        url = public or f"https://github.com/{unit['public_repo']}.git"
        for cmd in (["git", "clone", "-q", url, str(t / "public")],
                    ["git", "clone", "-q", "--bare", str(t / "public"), str(t / "target.git")]):
            r = run(cmd, t)
            if r.returncode:
                return [f"{' '.join(cmd[:3])} failed: {tail(r)}"]
        sha = git(top, "rev-parse", "--short=10", "HEAD").strip()
        r = run(["bash", str(publisher), prefix, str(t / "target.git"), sha, unit["public_repo"],
                 json.dumps(unit.get("readme", {}))], top)
        if r.returncode:
            return [f"publish_unit.sh exited {r.returncode}: {tail(r, 400)}"]
        r = run(["git", "clone", "-q", str(t / "target.git"), str(t / "result")], t)
        if r.returncode:
            return [f"the published result could not be cloned: {tail(r)}"]
        res = t / "result"
        stat = run(["git", "show", "--stat", "--format=%s", "HEAD"], res).stdout
        print("  the publish commit:\n" + "\n".join("    " + l for l in stat.strip().splitlines()[:60]))
        r = run([py, "scripts/check_changelog.py", "--require-new"], res)
        if r.returncode:
            found.append(f"check_changelog.py --require-new on the published result: {tail(r)}")
        r = run([py, "scripts/update_site.py"], res)
        if r.returncode:
            found.append(f"update_site.py exited {r.returncode} on the published result: {tail(r)}")
        if run(["git", "diff", "--quiet", "--", *GENERATED], res).returncode:
            found.append("the published result's generated files change when `update_site.py` runs there")
        untracked = run(["git", "ls-files", "--others", "--exclude-standard", "--", *GENERATED], res).stdout.split()
        found += [f"the published result leaves {u} untracked once `update_site.py` writes it" for u in untracked]
        found += [f"{p.relative_to(res).as_posix()} is a link to nothing" for p in res.rglob("*")
                  if p.is_symlink() and not p.exists() and ".git" not in p.relative_to(res).parts]
    return found


# ── tee ─────────────────────────────────────────────────────────────────────────────────────────────────────────────
WRAPPER = r'''"""The tee probe's wrapper: this tip's server/launch.py, both its streams, every line it sends the real server and
every line the real server answers logged whole with the seconds since it started, the real server started after
PROBE_DELAY seconds, as a cold install would."""
import importlib.util, json, os, sys, time
from pathlib import Path
LOG, DELAY, PY, LAUNCH = (os.environ[k] for k in ("PROBE_LOG", "PROBE_DELAY", "PROBE_PY", "PROBE_LAUNCH"))
spec = importlib.util.spec_from_file_location("launch", LAUNCH)
launch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(launch)
t0 = time.time()
def log(tag, data):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(f"[{time.time() - t0:8.3f}] {tag} {data.decode('utf-8', 'replace').rstrip()}\n")
class Tee:
    def __init__(self, f, tag): self.f, self.tag = f, tag
    def __iter__(self):
        for line in self.f:
            log(self.tag, line)
            yield line
    def __getattr__(self, name): return getattr(self.f, name)
class TeeOut:
    def __init__(self, f): self.f = f
    def write(self, b): log("L->C", b); return self.f.write(b)
    def flush(self): return self.f.flush()
class TeePopen(launch.subprocess.Popen):
    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        if self.stdout is not None:
            self.stdout = Tee(self.stdout, "S->L")          # the real server's own answers
launch.subprocess.Popen = TeePopen
launch.server_command = lambda args: ["sh", "-c", f"sleep {DELAY}; exec env PYTHONDONTWRITEBYTECODE=1 {PY} -m si.server"]
original = launch.Launcher.to_server
launch.Launcher.to_server = lambda self, line: (log("L->S", line), original(self, line))[1]
here = Path(LAUNCH).parent
tools = json.loads((here / "tools.json").read_text(encoding="utf-8"))
init = json.loads((here / "initialize.json").read_text(encoding="utf-8"))
sys.exit(launch.Launcher(sys.argv[1:], tools, init, inp=Tee(sys.stdin.buffer, "C->L"), out=TeeOut(sys.stdout.buffer)).run())
'''
TEE_TASK = ("Call the tool si_interpret of the self-interpreter server with the source 1+1, then reply with exactly "
            "what it returned and nothing else.")


def read_tee_log(text: str, tools: dict, delay: float | None = None) -> list[str]:
    """The tee probe's verdicts, read from the wrapper's log; `delay` is the seconds the real server was held back."""
    lines = []
    for raw in text.splitlines():
        m = TEE_LINE.match(raw)
        if m:
            try:
                lines.append((float(m.group(1)), m.group(2), json.loads(m.group(3))))
            except ValueError:
                lines.append((float(m.group(1)), m.group(2), None))
    def tagged(tag):
        return [(t, msg) for t, tg, msg in lines if tg == tag and isinstance(msg, dict)]
    client, answers, to_server, from_server = tagged("C->L"), tagged("L->C"), tagged("L->S"), tagged("S->L")
    if not client:
        return ["the log holds no client message"]
    found = []
    first_t, first = client[0]
    requests = [(t, msg) for t, msg in client if msg.get("method") and "id" in msg]
    for t, msg in requests:
        n = sum(1 for _, a in answers if a.get("id") == msg["id"] and ("result" in a or "error" in a))
        if n != 1:
            found.append(f"the client's {msg['method']} (id {msg['id']!r}) was answered {n} times, not once")
    def answer_to(method):
        req = next(((t, m) for t, m in requests if m["method"] == method), None)
        ans = next(((t, a) for t, a in answers if req and a.get("id") == req[1]["id"]), None)
        return req, ans
    if first.get("method") == "server/discover" and "id" in first:
        ans = next(((t, a) for t, a in answers if a.get("id") == first["id"]), None)
        if ans is None or "error" not in ans[1] or ans[0] - first_t > 1.0:
            found.append("the client's opening server/discover was not refused within one second"
                         + (f" (answered after {ans[0] - first_t:.2f}s)" if ans else ""))
    req, ans = answer_to("initialize")
    if req is None:
        found.append("the client sent no initialize")
    elif ans is None or "result" not in ans[1] or ans[0] - first_t > 1.0:
        found.append("initialize was not answered within one second of the client's first message"
                     + (f" (after {ans[0] - first_t:.2f}s)" if ans else ""))
    req, ans = answer_to("tools/list")
    if req is None or ans is None or ans[1].get("result") != tools:
        found.append("tools/list was not answered with server/tools.json")
    req, ans = answer_to("tools/call")
    if req is None:
        found.append("the client called no tool")
        return found
    server_up = next((t for t, m in from_server if m.get("id") == OWN_INIT and "result" in m), None)
    sent = next((t for t, m in to_server if m.get("id") == req[1]["id"]), None)
    served = next((t for t, m in from_server if m.get("id") == req[1]["id"]), None)
    if server_up is None:
        found.append("the log shows no answer of the real server's own to the launcher's initialize")
    if sent is None or (server_up is not None and sent < server_up):
        found.append("the tools/call was not written to the real server after the real server's own initialize answer")
    if delay is not None and sent is not None and sent < delay:
        found.append(f"the tools/call was written to the server {sent:.2f}s in, before the {delay}s it was held back")
    if served is None:
        found.append("the log shows no answer of the real server's own to the tools/call")
    result = (ans or (0, {}))[1].get("result") or {}
    texts = [c.get("text") for c in result.get("content", []) if isinstance(c, dict)]
    if (result.get("structuredContent") or {}).get("result") != "2" and "2" not in texts:
        found.append("the tools/call was not answered 2")
    return found


def result_is_two(text: object) -> bool:
    """The session's reply is the tool's answer and nothing else, in either form the tool returns it — its text `2`, or
    its structured content `{"result":"2"}`, which a client may hand the model instead — quoted or fenced at most."""
    s = re.sub(r"^```[A-Za-z]*\s*|\s*```$", "", str(text or "").strip()).strip().strip("`'\"").strip()
    if s == "2":
        return True
    try:
        v = json.loads(s)
    except ValueError:
        return False
    return isinstance(v, dict) and set(v) == {"result"} and str(v["result"]) == "2"


def server_own_answers(py: str, timeout: float = 120) -> dict:
    """The real server's own answers to `server/discover` (sent first, as Claude Code sends it) and `prompts/list`."""
    p = subprocess.Popen([py, "-m", "si.server"], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL)
    q: queue.Queue = queue.Queue()
    threading.Thread(target=lambda: [q.put(l) for l in p.stdout], daemon=True).start()
    def send(msg):
        p.stdin.write((json.dumps(msg) + "\n").encode())
        p.stdin.flush()
    got = {}
    try:
        send({"jsonrpc": "2.0", "id": "discover", "method": "server/discover", "params": {}})
        send({"jsonrpc": "2.0", "id": "init", "method": "initialize", "params": {
            "protocolVersion": "2025-11-25", "capabilities": {}, "clientInfo": {"name": "release_check", "version": "1"}}})
        send({"jsonrpc": "2.0", "method": "notifications/initialized"})
        send({"jsonrpc": "2.0", "id": "prompts", "method": "prompts/list", "params": {}})
        while len(got) < 3:
            m = json.loads(q.get(timeout=timeout))
            if m.get("id") in ("discover", "init", "prompts"):
                got[m["id"]] = m
    except (queue.Empty, ValueError, OSError):
        pass
    finally:
        p.stdin.close()
        p.terminate()
    return {k: got.get(k) for k in ("discover", "prompts")}


def part_tee(root: Path, py: str, log: str | None = None) -> list[str]:
    tools = json.loads((root / "server" / "tools.json").read_text(encoding="utf-8"))
    if log:
        return read_tee_log(Path(log).read_text(encoding="utf-8"), tools)
    sys.path.insert(0, str(HERE))
    from plugin_proof import KEEP_ENV, cmd_new, is_seat  # the clean seat the plugin proof keeps
    with tempfile.TemporaryDirectory(prefix="tee-") as tmp:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            made = cmd_new(str(Path(tmp) / "seats"))
        seat = Path(buf.getvalue().strip().splitlines()[-1]) if buf.getvalue().strip() else Path(tmp)
        if made or not is_seat(seat):
            return [f"no clean seat could be made: {buf.getvalue().strip()}"]
        wrapper, logf, cfg = seat / "tee_launch.py", seat / "tee.log", seat / "mcp.json"
        wrapper.write_text(WRAPPER, encoding="utf-8")
        cfg.write_text(json.dumps({"mcpServers": {"self-interpreter": {
            "command": sys.executable, "args": [str(wrapper), "--from", "chaincompiler-si==0", "si-server"],
            "env": {"PROBE_LOG": str(logf), "PROBE_DELAY": str(TEE_DELAY), "PROBE_PY": py,
                    "PROBE_LAUNCH": str(root / "server" / "launch.py")}}}}))
        env = {k: os.environ[k] for k in KEEP_ENV if k in os.environ}
        found = []
        try:
            r = run(["claude", "-p", TEE_TASK, "--output-format", "stream-json", "--verbose", "--model", "haiku",
                     "--strict-mcp-config", "--mcp-config", str(cfg), "--setting-sources", "project,local",
                     "--allowedTools", "mcp__self-interpreter__si_interpret"], seat, env=env, timeout=600)
            out = r.stdout
        except subprocess.TimeoutExpired as e:
            found.append("the probe's session did not end within 600 s")
            out = (e.stdout or b"").decode("utf-8", "replace") if isinstance(e.stdout, bytes) else (e.stdout or "")
        evs = [json.loads(l) for l in out.splitlines() if l.strip().startswith("{")]
        init = next((e for e in evs if e.get("type") == "system" and e.get("subtype") == "init"), {})
        result = next((e for e in reversed(evs) if e.get("type") == "result"), {})
        found += read_tee_log(logf.read_text(encoding="utf-8") if logf.exists() else "", tools, delay=TEE_DELAY)
        status = [m.get("status") for m in init.get("mcp_servers", []) if m.get("name") == "self-interpreter"]
        if status != ["connected"]:
            found.append(f"the session's start lists the server {status or 'not at all'}, not connected")
        if not result_is_two(result.get("result")) or result.get("is_error"):
            found.append(f"the session's result is not the tool's answer 2: {str(result.get('result', ''))[:200]!r}")
        print("  the tee probe's log:\n" + "\n".join("    " + l[:200] for l in
                                                     (logf.read_text(encoding="utf-8").splitlines() if logf.exists() else [])))
        own = server_own_answers(py)
        print("  the real server's own answers, asked directly:\n"
              + "\n".join(f"    {k}: {json.dumps(v)[:300]}" for k, v in own.items()))
        return found


# ── the command ─────────────────────────────────────────────────────────────────────────────────────────────────────
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="a release's own checks, in one command")
    ap.add_argument("--root", default=str(ROOT), help="the ChainCompiler folder of a checkout at the tip")
    ap.add_argument("--replaced", help="a file of the readings the release rewrote away, one per line")
    ap.add_argument("--only", nargs="*", choices=PARTS, help="run only these parts")
    ap.add_argument("--public", help="the public repository to clone for the publish dry run (default: the unit's)")
    ap.add_argument("--tee-log", help="read this tee-probe log instead of running the probe")
    a = ap.parse_args(argv)
    root, py = Path(a.root).resolve(), sys.executable
    print("## the tip being proven", flush=True)
    refused = preflight(root, py)
    if refused:
        print("\n".join(f"  ✗ {f}" for f in refused))
        print("✗ the release check refuses: commit the tip, and run it with this tree's editable environment")
        return 1
    print("  ✓ the folder is committed, and its packages import from this tree")
    replaced = Path(a.replaced).read_text(encoding="utf-8").splitlines() if a.replaced else None
    parts = a.only or list(PARTS)
    total = 0
    for part in parts:
        print(f"## {part}", flush=True)
        found = {"generated": lambda: part_generated(root, py), "frontmatter": lambda: part_frontmatter(root),
                 "sentences": lambda: part_sentences(root, replaced),
                 "publish": lambda: part_publish(root, py, a.public),
                 "tee": lambda: part_tee(root, py, a.tee_log)}[part]()
        total += len(found)
        print("  ✓ nothing found" if not found else "\n".join(f"  ✗ {f}" for f in found), flush=True)
    print(f"✓ the release check found nothing ({', '.join(parts)})" if not total else
          f"✗ the release check found {total} thing(s) to fix")
    return 1 if total else 0


if __name__ == "__main__":
    raise SystemExit(main())
