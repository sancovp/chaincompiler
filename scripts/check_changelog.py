#!/usr/bin/env python3
"""Deploy gate: the README changelog must be present, well-formed, and (in CI) new.

  python3 scripts/check_changelog.py               # validate the changelog exists + parses
  python3 scripts/check_changelog.py --require-new # also require a new version vs the last commit
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
README = ROOT / "README.md"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from update_site import parse_changelog  # noqa: E402


def _versions(text: str) -> list[str]:
    return [e["version"] for e in parse_changelog(text)]


def _prev_readme() -> str | None:
    try:
        return subprocess.run(
            ["git", "show", "HEAD~1:README.md"], cwd=ROOT,
            capture_output=True, text=True, check=True,
        ).stdout
    except Exception:
        return None


def main(argv: list[str]) -> int:
    if not README.exists():
        print("✗ no README.md"); return 1
    text = README.read_text(encoding="utf-8")
    versions = _versions(text)
    if not versions:
        print("✗ README has no parseable `## Changelog` entries (### vX — date + bullets)"); return 1
    print(f"✓ changelog OK — latest: {versions[0]} ({len(versions)} entries)")

    if "--require-new" in argv:
        prev = _prev_readme()
        if prev is None:
            print("⚠ no previous README (first commit / not a git repo) — skipping new-entry check")
            return 0
        if set(versions) <= set(_versions(prev)):
            print("✗ no NEW changelog entry vs the previous commit — add one before deploying"); return 1
        print("✓ a new changelog entry is present")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
