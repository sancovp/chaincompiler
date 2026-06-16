#!/usr/bin/env python3
"""Contribution gate for registry.json — run by CI on pull_request.

SELF-CONTAINED (stdlib only) so CI can run the BASE (trusted) copy of this file
against a PR's data — a fork PR must not be able to swap out its own gate. The
canonical, unit-tested logic lives in `skilltree.registry`; this mirrors it.

Policy (locked): a contribution may only ADD `unverified` entries with provenance.
It may not change another entry's trust, remove others' entries, or rename/
re-parent the registry. Promotion is a separate, maintainer-only step.

    python3 scripts/validate_registry.py [--base origin/main]
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

KINDS = ("skill", "tree", "exchange", "mcp")
TRUST = ("unverified", "verified", "featured")
_REQUIRED = ("name", "kind", "repo")


def validate_registry(d: dict) -> list[str]:
    errs: list[str] = []
    if not isinstance(d.get("name"), str):
        errs.append("registry: missing string `name`")
    if "parent" not in d:
        errs.append("registry: missing `parent` (null at the root)")
    if not isinstance(d.get("entries"), list):
        return errs + ["registry: `entries` must be a list"]
    seen: set = set()
    for i, e in enumerate(d["entries"]):
        tag = e.get("name", f"#{i}")
        for f in _REQUIRED:
            if not e.get(f):
                errs.append(f"entry {tag}: missing `{f}`")
        if e.get("kind") not in KINDS:
            errs.append(f"entry {tag}: kind must be one of {KINDS}")
        if e.get("trust", "unverified") not in TRUST:
            errs.append(f"entry {tag}: trust must be one of {TRUST}")
        if e.get("name") in seen:
            errs.append(f"entry {tag}: duplicate name")
        seen.add(e.get("name"))
    return errs


def validate_contribution(base: dict, head: dict) -> list[str]:
    errs = validate_registry(head)
    if errs:
        return errs
    if head.get("name") != base.get("name"):
        errs.append("contribution may not rename the registry")
    if head.get("parent") != base.get("parent"):
        errs.append("contribution may not change the registry parent")
    b = {e["name"]: e for e in base.get("entries", [])}
    h = {e["name"]: e for e in head.get("entries", [])}
    for name in h.keys() - b.keys():
        e = h[name]
        if e.get("trust", "unverified") != "unverified":
            errs.append(f"new entry {name!r} must be `unverified` (promotion is maintainer-only)")
        if not (e.get("provenance") or {}).get("by"):
            errs.append(f"new entry {name!r} must carry provenance.by")
    for name in b.keys() - h.keys():
        errs.append(f"contribution removes existing entry {name!r} (maintainer-only)")
    for name in b.keys() & h.keys():
        if h[name].get("trust") != b[name].get("trust"):
            errs.append(f"contribution changes trust of {name!r} (maintainer-only — use promote)")
    return errs


def _git_show(ref_path: str) -> dict:
    try:
        out = subprocess.run(["git", "show", ref_path], capture_output=True, text=True, check=True).stdout
        return json.loads(out)
    except Exception:
        return {}


def main(argv: list[str]) -> int:
    base_ref = "origin/main"
    if "--base" in argv:
        base_ref = argv[argv.index("--base") + 1]
    head = json.loads(Path("registry.json").read_text(encoding="utf-8"))
    base = _git_show(f"{base_ref}:registry.json") or {"name": head.get("name"),
                                                       "parent": head.get("parent"), "entries": []}
    errs = validate_contribution(base, head)
    if errs:
        print("✗ contribution rejected:")
        for e in errs:
            print(f"  - {e}")
        return 1
    added = len({e["name"] for e in head.get("entries", [])}
                - {e["name"] for e in base.get("entries", [])})
    print(f"✓ contribution OK — {added} new entry(ies) queued as `unverified` (awaiting maintainer promotion).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
