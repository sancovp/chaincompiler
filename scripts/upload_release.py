#!/usr/bin/env python3
"""upload_release.py — THE UPLOAD of a release's fifteen packages to PyPI, in dependency order (DESIGN.md §18).

    python3 scripts/upload_release.py --clone DIR --publish-package PATH [--order] [--dry-run]
    python3 scripts/upload_release.py --clone DIR --whole

`--clone` is a clone of the public repository at the release's publish commit (the release is its packages' version);
`--publish-package` is scalable-publishing's `bin/publish_package.sh`, which builds one package folder and uploads it
with this machine's PyPI login. The order: the self-interpreter's closure first, then the packages the shipped skills'
uv lines name, then the rest — each tier in dependency order, never the folders' alphabetical order. A package uploads
only when PyPI holds every sibling its build file requires (its dependencies among the fifteen, not its extras) at the
release; one PyPI already holds is skipped. PyPI creates four new projects a day for one account and one address
(`429 Too many new projects created`): after that answer no new name is tried again in the run, while a version of a
project PyPI already holds still uploads. PyPI's state is read afresh on every run, so a run the next day resumes where
the last one stopped. `--order` prints the order and exits; `--dry-run` decides each package without uploading.
Whether PyPI holds a version is read from that version's own JSON, never the project's. Each of PyPI's pages is served
through a cache, and so can answer as it did before an upload — the simple index until its `max-age=600` ends, its HTML
form and the JSON form pip and uv ask for kept apart (`Vary: Accept`), and a version's JSON a 404 for a while — so one
reader can see a new version the next does not (scalable-publishing DESIGN.md §4). `--whole`
is stage 1's last reading: each of the fifteen held by its version's JSON, listed by both forms of the simple index, and
uploaded longer ago than the index's own cache life (its `cache-control` max-age), so no install can still be served a
copy from before the upload.
Exit 0 when PyPI holds all fifteen at the release · 3 when some wait (a sibling, the day's quota, or `--whole`'s simple
index not yet listing it in a form, or within its cache life of the upload) · 4 from `--whole`, a version whose JSON
answers 404 — read again in the minutes after an upload, then the upload run again — · 1 on a failure, or when PyPI
gives no answer.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tomllib
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from check_versions import req_name, uv_lines  # noqa: E402

SERVER = "chaincompiler-si"
DAILY_NEW_PROJECTS = 4      # PyPI's quota for one account and one address (its `RateLimit-Policy`: q=4;w=86400)
# the simple index's two forms, which PyPI's cache keeps apart (`Vary: Accept`): the HTML page, and the JSON form pip and
# uv ask for first (PEP 691)
INDEX_FORMS = {"HTML": "text/html", "JSON": "application/vnd.pypi.simple.v1+json"}


def packages(clone: Path) -> dict[str, dict]:
    """Each distribution → its folder, its version and the siblings its build file requires (extras left out)."""
    found = {}
    for pp in sorted((clone / "packages").glob("*/pyproject.toml")):
        proj = tomllib.loads(pp.read_text(encoding="utf-8"))["project"]
        found[proj["name"]] = {"folder": pp.parent, "version": proj["version"],
                               "requires": [req_name(r)[0] for r in proj.get("dependencies", [])]}
    for p in found.values():
        p["requires"] = sorted(r for r in p["requires"] if r in found)
    return found


def closure(names: set[str], pkgs: dict[str, dict]) -> set[str]:
    out, todo = set(), list(names)
    while todo:
        n = todo.pop()
        if n in pkgs and n not in out:
            out.add(n)
            todo += pkgs[n]["requires"]
    return out


def skill_distributions(clone: Path) -> set[str]:
    """The distributions the shipped skills' uv lines name."""
    out = set()
    for f in (clone / "skills").rglob("*.md"):
        withs, froms = uv_lines(f.read_text(encoding="utf-8"))
        out |= {n.split("[")[0] for n in withs} | {req_name(r)[0] for r in froms.values()}
    return out


def topological(names: set[str], pkgs: dict[str, dict]) -> list[str]:
    """Dependencies before their dependents; alphabetical among the ready."""
    done, order = set(), []
    while len(order) < len(names):
        ready = sorted(n for n in names - done if all(r in done or r not in names for r in pkgs[n]["requires"]))
        if not ready:
            raise SystemExit(f"a dependency cycle among {sorted(names - done)}")
        order.append(ready[0])
        done.add(ready[0])
    return order


def upload_order(clone: Path) -> list[str]:
    pkgs = packages(clone)
    tier1 = closure({SERVER}, pkgs)
    tier2 = closure(skill_distributions(clone) & set(pkgs), pkgs) - tier1
    tier3 = set(pkgs) - tier1 - tier2
    return topological(tier1, pkgs) + topological(tier2, pkgs) + topological(tier3, pkgs)


def fetch(url: str, accept: str | None = None) -> tuple[int, str, dict]:
    """GET one of PyPI's pages, in the form `accept` asks for: (its HTTP status, its body, its headers lower-cased);
    status 0 when PyPI gave no answer."""
    req = urllib.request.Request(url, headers={"Accept": accept} if accept else {})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, r.read().decode("utf-8", "replace"), {k.lower(): v for k, v in r.headers.items()}
    except urllib.error.HTTPError as e:
        return e.code, "", {k.lower(): v for k, v in (e.headers or {}).items()}
    except (urllib.error.URLError, TimeoutError):
        return 0, "", {}


def max_age(headers: dict) -> int:
    """How long a cache may serve the page, from its `cache-control` header (`max-age=600` → 600); 0 when it states none."""
    m = re.search(r"max-age=(\d+)", headers.get("cache-control", ""))
    return int(m.group(1)) if m else 0


def uploaded_at(version_json: str) -> datetime | None:
    """When the version's newest file was uploaded, from its JSON (`urls[].upload_time_iso_8601`); None when it says not."""
    try:
        times = [u.get("upload_time_iso_8601") for u in json.loads(version_json).get("urls", [])]
        return max(datetime.fromisoformat(t.replace("Z", "+00:00")) for t in times if t)
    except (ValueError, AttributeError, TypeError):
        return None


def pypi_status(name: str, version: str | None = None, get=fetch) -> int:
    """PyPI's HTTP status for a project (or one of its versions): 200 held, 404 not; anything else is not an answer."""
    url = f"https://pypi.org/pypi/{name}/{version}/json" if version else f"https://pypi.org/pypi/{name}/json"
    return get(url)[0]


def held(name: str, version: str, get=fetch) -> bool:
    """Whether PyPI holds a version, read from that version's own JSON — never the project's (scalable-publishing
    DESIGN.md §4)."""
    status = pypi_status(name, version, get)
    if status not in (200, 404):
        raise SystemExit(f"PyPI gave no answer for {name} {version} (HTTP {status or 'none'}): nothing is decided")
    return status == 200


def indexed(name: str, version: str, get=fetch) -> dict[str, tuple[bool | None, int]]:
    """Whether each form of PyPI's simple index — what pip and uv read — lists a file of the version (a wheel or the
    sdist): {form: (True, False, or None when PyPI gave no answer; the form's cache life in seconds)}. PyPI's cache keeps
    the HTML form and the JSON form apart, so one can list a version the other does not yet."""
    out = {}
    for form, accept in INDEX_FORMS.items():
        status, body, headers = get(f"https://pypi.org/simple/{name}/", accept)
        if status == 404:
            out[form] = (False, max_age(headers))
        elif status != 200:
            out[form] = (None, 0)
        else:
            out[form] = (re.search(rf"-{re.escape(version)}(?:-|\.tar\.gz)", body) is not None, max_age(headers))
    return out


def whole(clone: Path, get=fetch, now: datetime | None = None) -> int:
    """Stage 1's reading of PyPI, before an install from it starts: every one of the fifteen held at the release by its
    version's JSON, listed at the release by both forms of the simple index, and uploaded longer ago than the index's
    cache life, so a cache can no longer serve pip or uv a copy from before the upload. Exit 0 whole · 3 the simple index
    may still be behind (read again in a minute) · 4 a version whose JSON answers 404 — in the minutes after an upload
    that can be a cached 404, so read again; one that stands names a version PyPI does not hold (run the upload again,
    or treat the name as refused) · 1 no answer, or the fifteen at more than one version."""
    pkgs, order = packages(clone), upload_order(clone)
    versions = {p["version"] for p in pkgs.values()}
    if len(versions) != 1:
        print(f"the fifteen are at more than one version: {sorted(versions)}")
        return 1
    version = versions.pop()
    now = now or datetime.now(timezone.utc)
    lagging, missing, silent = [], [], []
    print(f"release {version}, read from each version's JSON and both forms of the simple index, at "
          f"{now.isoformat(timespec='seconds')}:")
    for n in order:
        status, body, _ = get(f"https://pypi.org/pypi/{n}/{version}/json")
        forms = indexed(n, version, get)
        at = uploaded_at(body) if status == 200 else None
        cache = max(life for _, life in forms.values())
        age = (now - at).total_seconds() if at else None
        if status not in (200, 404) or any(listed is None for listed, _ in forms.values()) or (status == 200 and not at):
            silent.append(n)
        elif status == 404:
            missing.append(n)
        elif not all(listed for listed, _ in forms.values()) or age < cache:
            lagging.append(n)
        upload = f", uploaded {at.isoformat(timespec='seconds')} ({age:.0f} s ago)" if at else ""
        listing = " · ".join(f"{form} {'lists it' if listed else 'does not list it' if listed is False else 'gave no answer'}"
                             for form, (listed, _) in forms.items())
        print(f"  {n:26} version JSON {status or 'no answer'}{upload} · simple index {listing} (cached up to {cache} s)")
    if silent:
        print(f"PyPI gave no answer for {', '.join(silent)}: nothing is decided")
        return 1
    if missing:
        print(f"PyPI does not hold {version} for {', '.join(missing)} by its version's JSON — in the minutes after an "
              "upload that can be a cached 404, so read again in a minute; if it still answers 404, run the upload again, "
              "or treat the name as refused")
        return 4
    print(f"PyPI holds {version} whole, listed by both forms of its simple index, every upload older than its cache"
          if not lagging else
          f"PyPI holds {version}, and its simple index may not list it yet for {', '.join(lagging)} — a form does not "
          "list it, or it was uploaded within the index's cache life — read again in a minute")
    return 3 if lagging else 0


def publish(script: str, folder: Path) -> tuple[int, str]:
    r = subprocess.run(["bash", script, str(folder)], capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


def reason(out: str) -> str:
    """Why an upload failed, from its output: each error line twine or the publish script printed, with the line after
    an `HTTPError` (PyPI's own words); else the output's last line. The build's progress lines come after twine's error
    in the joined output, so the last line alone never names the cause."""
    lines = [re.sub(r"\x1b\[[0-9;?]*[A-Za-z]", "", l).strip() for l in out.splitlines()]
    lines = [l for l in lines if l]
    picked = []
    for i, l in enumerate(lines):
        if re.search(r"\bERROR\b|HTTPError|REFUSED|\[package\] no |error:", l):
            picked.append(l)
            if "HTTPError" in l and i + 1 < len(lines):
                picked.append(lines[i + 1])
    return " · ".join(dict.fromkeys(picked)) if picked else (lines[-1] if lines else "")


def run(clone: Path, script: str, dry_run: bool = False, status=held, project=pypi_status, upload=publish) -> int:
    pkgs, order = packages(clone), upload_order(clone)
    versions = {p["version"] for p in pkgs.values()}
    if len(versions) != 1:
        raise SystemExit(f"the fifteen are at more than one version: {sorted(versions)}")
    version = versions.pop()
    have = {n: status(n, version) for n in order}
    quota_spent, failed, planned_new = False, False, 0
    print(f"release {version}, in order: {' · '.join(order)}")
    for n in order:
        if have[n]:
            print(f"  {n:26} held")
            continue
        missing = [r for r in pkgs[n]["requires"] if not have[r]]
        if missing:
            print(f"  {n:26} waits: PyPI does not hold {', '.join(missing)} at {version}")
            continue
        new_name = project(n) != 200
        if new_name and quota_spent:
            print(f"  {n:26} waits: a new name, and PyPI's quota of new projects is spent for the day")
            continue
        if dry_run:
            if new_name and planned_new >= DAILY_NEW_PROJECTS:
                print(f"  {n:26} waits: a new name past the day's quota of {DAILY_NEW_PROJECTS}")
                continue
            planned_new += new_name
            have[n] = True              # as a real run would hold it, for the packages after it
            print(f"  {n:26} would upload{' (a new name on PyPI)' if new_name else ''}")
            continue
        code, out = upload(script, pkgs[n]["folder"])
        if code == 0 or f"REFUSED: PyPI already holds {n} {version}" in out:
            have[n] = True
            print(f"  {n:26} uploaded")
        elif "429" in out or "Too many new projects" in out:
            quota_spent = True
            print(f"  {n:26} waits: PyPI answered 429 — its quota of new projects is spent for the day")
        else:
            failed = True
            print(f"  {n:26} FAILED (exit {code}): {reason(out)}")
    waiting = [n for n in order if not have[n]]
    print(("a run now, with the day's quota whole, would leave PyPI holding" if dry_run else "PyPI holds")
          + f" {len(order) - len(waiting)} of {len(order)} at {version}"
          + (f"; waiting: {', '.join(waiting)}" if waiting else ""))
    return 1 if failed else (3 if waiting else 0)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="upload a release's fifteen packages to PyPI, in dependency order")
    ap.add_argument("--clone", required=True, help="a clone of the public repository at the release's publish commit")
    ap.add_argument("--publish-package", help="scalable-publishing's bin/publish_package.sh")
    ap.add_argument("--order", action="store_true", help="print the upload order and exit")
    ap.add_argument("--dry-run", action="store_true", help="decide each package, upload nothing")
    ap.add_argument("--whole", action="store_true",
                    help="read whether PyPI holds the release whole, both forms of its simple index list it and its "
                         "cache life has passed since each upload; upload nothing")
    a = ap.parse_args(argv)
    clone = Path(a.clone).resolve()
    if a.order:
        print("\n".join(upload_order(clone)))
        return 0
    if a.whole:
        return whole(clone)
    if not a.publish_package:
        ap.error("--publish-package is required unless --order or --whole")
    return run(clone, a.publish_package, a.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
