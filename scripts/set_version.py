#!/usr/bin/env python3
"""set_version.py — write one release version everywhere a version lives (DESIGN.md §18).

    python3 scripts/set_version.py 0.3.0

Writes the version into every package's `pyproject.toml` `version` and every `__version__` a package defines, the
plugin's version in `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json`, the pin in `.mcp.json`, and
every uv-line pin in the shipped skills and their copies (`skills/`, the working copies in `.claude/skills/`, the
`bandit-chain-system` package data); it pins every dependency among the fifteen, an optional extra's included, with
`==`. It edits text in place and touches nothing else: the README changelog entry is the author's, and the GBAs under
`personas/` are re-applied by the release flow so each carries the same bytes. `check_versions.py` is its gate.
"""
from __future__ import annotations

import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VERSION = re.compile(r"^\d+\.\d+\.\d+$")


def distributions(root: Path = ROOT) -> list[str]:
    """The fifteen distribution names, read from their build files, longest first (so a regex alternation never stops
    at a prefix: `chaincompiler-accc` before `chaincompiler`)."""
    names = [tomllib.loads(p.read_text(encoding="utf-8"))["project"]["name"]
             for p in sorted((root / "packages").glob("*/pyproject.toml"))]
    return sorted(names, key=len, reverse=True)


def pin_dependencies(text: str, names: list[str], version: str) -> str:
    """Pin every sibling in the `[project]` `dependencies` array and every `[project.optional-dependencies]` array."""
    sib = re.compile(r'"(' + "|".join(map(re.escape, names)) + r')(\[[^\]"]*\])?\s*(?:[<>=!~][^"]*)?"')
    out, table = [], None
    for line in text.splitlines(keepends=True):
        head = re.match(r"^\s*\[([^\[\]]+)\]\s*$", line)
        if head:
            table = head.group(1).strip()
        in_deps = (table == "project" and re.match(r"^\s*dependencies\s*=", line)) or \
                  (table == "project.optional-dependencies" and re.match(r"^\s*[A-Za-z0-9_.-]+\s*=", line))
        if in_deps:
            if "[" in line.split("=", 1)[1] and "]" not in line.split("=", 1)[1].split("[", 1)[1]:
                raise SystemExit(f"a dependency array spans lines, which this script does not edit: {line.strip()}")
            line = sib.sub(lambda m: f'"{m.group(1)}{m.group(2) or ""}=={version}"', line)
        out.append(line)
    return "".join(out)


def skill_pins(text: str, names: list[str], version: str) -> str:
    """Re-pin every sibling distribution a uv line names (`--with X==…`, `--from X==…`, quoted or not)."""
    pin = re.compile(r'((?:--with|--from)\s+"?)(' + "|".join(map(re.escape, names)) + r')(\[[^\]"]*\])?==[0-9][0-9A-Za-z.]*')
    return pin.sub(lambda m: f"{m.group(1)}{m.group(2)}{m.group(3) or ''}=={version}", text)


def skill_files(root: Path = ROOT) -> list[Path]:
    """Every file a uv line can live in: the shipped skills, their working copies, the package-data copy and a package's
    own copy of a shipped skill."""
    files = [p for p in (root / "skills").rglob("*.md")]
    for name in ("bandit-chain-system", "glyphsteer", "glyphsteer-dense"):
        files += list((root / ".claude" / "skills" / name).rglob("*.md"))
    files += list((root / "packages").glob("*/src/*/data/**/*.md"))
    files += list((root / "packages").glob("*/.claude/skills/**/*.md"))     # a package's own copy of a shipped skill
    return sorted(set(files))


def write(path: Path, new: str, changed: list[str], root: Path) -> None:
    if path.read_text(encoding="utf-8") != new:
        path.write_text(new, encoding="utf-8")
        changed.append(path.relative_to(root).as_posix())


def set_version(version: str, root: Path = ROOT) -> list[str]:
    if not VERSION.match(version):
        raise SystemExit(f"not a release version (X.Y.Z): {version!r}")
    names, changed = distributions(root), []
    for pp in sorted((root / "packages").glob("*/pyproject.toml")):
        text = pp.read_text(encoding="utf-8")
        text = re.sub(r'(?m)^(version\s*=\s*)"[^"]*"', rf'\g<1>"{version}"', text, count=1)
        write(pp, pin_dependencies(text, names, version), changed, root)
    for init in sorted((root / "packages").glob("*/src/*/__init__.py")):
        text = init.read_text(encoding="utf-8")
        write(init, re.sub(r'(?m)^(__version__\s*=\s*)"[^"]*"', rf'\g<1>"{version}"', text), changed, root)
    for manifest in (root / ".claude-plugin" / "plugin.json", root / ".claude-plugin" / "marketplace.json"):
        text = manifest.read_text(encoding="utf-8")
        write(manifest, re.sub(r'("version"\s*:\s*)"[^"]*"', rf'\g<1>"{version}"', text), changed, root)
    mcp = root / ".mcp.json"
    write(mcp, re.sub(r"chaincompiler-si==[0-9][0-9A-Za-z.]*", f"chaincompiler-si=={version}",
                      mcp.read_text(encoding="utf-8")), changed, root)
    for f in skill_files(root):
        write(f, skill_pins(f.read_text(encoding="utf-8"), names, version), changed, root)
    return changed


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print(__doc__.strip().splitlines()[2].strip())
        return 2
    changed = set_version(argv[0])
    print(f"set {argv[0]} in {len(changed)} file(s):")
    for c in changed:
        print("  ", c)
    print("then: re-apply every GBA under personas/, regenerate the capability skills, and run check_versions.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
