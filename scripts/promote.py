#!/usr/bin/env python3
"""Maintainer-only: promote a registry entry's trust (the gated step).

This is the human gate. It is NOT run on contributor PRs — a maintainer runs it
directly (then commits the change to main).

    python3 scripts/promote.py <entry-name> [--to verified|featured] [--by you]
"""
from __future__ import annotations

import sys
from pathlib import Path

# canonical logic lives in the installed package
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "packages" / "skilltree" / "src"))
from skilltree.registry import promote  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2
    name = argv[0]
    to = argv[argv.index("--to") + 1] if "--to" in argv else "verified"
    by = argv[argv.index("--by") + 1] if "--by" in argv else "maintainer"
    entry = promote(ROOT / "registry.json", name, to=to, by=by)
    print(f"✓ promoted {entry.name!r} → {entry.trust}  (by {by})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
