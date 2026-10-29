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
Whether PyPI holds a version is read from that version's own JSON, which answers at once; the project's JSON and the
simple index list a new version minutes later (scalable-publishing DESIGN.md §4). `--whole` is stage 1's last reading:
each of the fifteen held by its version's JSON and listed by the simple index, which pip and uv read.
Exit 0 when PyPI holds all fifteen at the release · 3 when some wait (a sibling, the day's quota, or `--whole`'s simple
index still behind) · 4 from `--whole`, a version PyPI does not hold, which no wait changes · 1 on a failure, or
when PyPI gives no answer.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
import tomllib
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from check_versions import req_name, uv_lines  # noqa: E402

SERVER = "chaincompiler-si"
DAILY_NEW_PROJECTS = 4      # PyPI's quota for one account and one address (its `RateLimit-Policy`: q=4;w=86400)


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


def fetch(url: str) -> tuple[int, str]:
    """GET one of PyPI's pages: (its HTTP status, its body); status 0 when PyPI gave no answer."""
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, ""
    except (urllib.error.URLError, TimeoutError):
        return 0, ""


def pypi_status(name: str, version: str | None = None, get=fetch) -> int:
    """PyPI's HTTP status for a project (or one of its versions): 200 held, 404 not; anything else is not an answer."""
    url = f"https://pypi.org/pypi/{name}/{version}/json" if version else f"https://pypi.org/pypi/{name}/json"
    return get(url)[0]


def held(name: str, version: str, get=fetch) -> bool:
    """Whether PyPI holds a version, read from that version's own JSON, which answers the moment an upload lands; the
    project's JSON lists a new version minutes later (scalable-publishing DESIGN.md §4), so it is never read for this."""
    status = pypi_status(name, version, get)
    if status not in (200, 404):
        raise SystemExit(f"PyPI gave no answer for {name} {version} (HTTP {status or 'none'}): nothing is decided")
    return status == 200


def indexed(name: str, version: str, get=fetch) -> bool | None:
    """Whether PyPI's simple index — what pip and uv read — lists a file of the version (a wheel or the sdist): True,
    False, or None when PyPI gave no answer. It lists a new version minutes after the version's JSON holds it."""
    status, body = get(f"https://pypi.org/simple/{name}/")
    if status == 404:
        return False
    if status != 200:
        return None
    return re.search(rf"-{re.escape(version)}(?:-|\.tar\.gz)", body) is not None


def whole(clone: Path, get=fetch) -> int:
    """Stage 1's reading of PyPI, before an install from it starts: every one of the fifteen held at the release by its
    version's JSON, and listed at the release by the simple index. Exit 0 whole · 3 the simple index still behind (read
    again in a minute) · 4 a version PyPI does not hold, which no wait changes (run the upload again, or treat the name
    as refused) · 1 no answer, or the fifteen at more than one version."""
    pkgs, order = packages(clone), upload_order(clone)
    versions = {p["version"] for p in pkgs.values()}
    if len(versions) != 1:
        print(f"the fifteen are at more than one version: {sorted(versions)}")
        return 1
    version = versions.pop()
    lagging, missing, silent = [], [], []
    print(f"release {version}, read from each version's JSON and the simple index:")
    for n in order:
        status = pypi_status(n, version, get)
        listed = indexed(n, version, get)
        if status not in (200, 404) or listed is None:
            silent.append(n)
        elif status == 404:
            missing.append(n)
        elif not listed:
            lagging.append(n)
        print(f"  {n:26} version JSON {status or 'no answer'} · simple index "
              f"{'lists it' if listed else 'does not list it' if listed is False else 'gave no answer'}")
    if silent:
        print(f"PyPI gave no answer for {', '.join(silent)}: nothing is decided")
        return 1
    if missing:
        print(f"PyPI does not hold {version} for {', '.join(missing)} — no wait changes that: run the upload again, or "
              "treat the name as refused")
        return 4
    print(f"PyPI holds {version} whole, listed by its simple index" if not lagging else
          f"PyPI holds {version}, and its simple index does not list it yet for {', '.join(lagging)} — read again in a "
          "minute")
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
                    help="read whether PyPI holds the release whole and its simple index lists it; upload nothing")
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
