#!/usr/bin/env python3
"""check_versions.py — the gate on the one version line and the skills' uv lines (DESIGN.md §16 · §18).

    python3 scripts/check_versions.py [--root DIR]

The release version is the newest README changelog entry. Refused, each named with its place:
  - a package's `version` or a `__version__` it defines that differs from it;
  - a plugin manifest version (`plugin.json`, `marketplace.json`) that differs;
  - a dependency among the fifteen, an optional extra's included, not pinned `==` to it;
  - a declared `agent-prompt-engineering` or `agent-skilltree` without the lower bound §18 states;
  - a module a package's source imports that its build file does not declare (a lazy import as an optional extra);
  - a build file that does not give its package's page on PyPI its README (`readme = "README.md"`, the file present)
    and the repository's license (`license = "MIT"`), or whose `setuptools` build requirement is below 77, the first
    release that reads a license written that way;
  - a `.mcp.json` whose self-interpreter is not `uvline.server_launch(<release>)` — uv running the plugin's
    `server/launch.py` with `--from chaincompiler-si==<release> si-server` — or a plugin without that launcher and
    its `initialize.json` and `tools.json`;
  - a shipped skill whose code has no uv line before its first code block, or a uv line that misses a distribution
    the code it runs imports (a lazy or optional import included), pins a sibling to another version, or names an
    outside distribution without its lower bound;
  - a copy of `bandit-chain-system`, `glyphsteer` or `glyphsteer-dense` — and any other `SKILL.md` under a
    `.claude/skills/` folder or a package's own folder that carries a shipped skill's name — that is not byte-identical
    to its source, is a link, or is reached through a linked folder;
  - a package folder whose `LICENSE` is missing or differs from the repository's.
Exit 0 with nothing refused; exit 1 naming every refusal.
"""
from __future__ import annotations

import argparse
import ast
import json
import os
import re
import shlex
import sys
import tomllib
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from update_site import parse_changelog  # noqa: E402
from uvline import server_launch  # noqa: E402

LOWER = {"agent-prompt-engineering": "0.2.0", "agent-skilltree": "0.4.0"}
LICENSE = "MIT"         # the repository's LICENSE, as every package's metadata states it
SETUPTOOLS = 77         # the first setuptools that reads `license = "MIT"` (an SPDX expression)

# a module root → its distribution, for the modules the fifteen import from outside themselves
OUTSIDE = {"skilltree": "agent-skilltree", "prompt_engineering": "agent-prompt-engineering",
           "pydantic_stack_core": "pydantic-stack-core", "lark": "lark", "click": "click", "yaml": "pyyaml",
           "numpy": "numpy", "fastmcp": "fastmcp", "mcp": "mcp", "fastembed": "fastembed",
           "sentence_transformers": "sentence-transformers", "fastapi": "fastapi", "uvicorn": "uvicorn",
           "pytest": "pytest"}

# entry points whose code reaches a lazy import: (module root, called name) → the distributions it reaches
LAZY = {("chainaios", n): ["glyphsteer"] for n in
        ("roll_up_algebra", "hierarchicalize", "make_gba", "construct_into", "make_hba", "make_cog")}
LAZY[("glyphsteer", "GlyphGrammar")] = ["chaincompiler", "rulecatcher"]
LAZY[("chaincompiler", "compile_persona")] = ["glyphsteer"]

FENCE = re.compile(r"^```([A-Za-z0-9_-]*)\s*$")


class Report:
    def __init__(self) -> None:
        self.refused: list[str] = []

    def refuse(self, where: str, why: str) -> None:
        self.refused.append(f"{where}: {why}")


def release(root: Path) -> str:
    entries = parse_changelog((root / "README.md").read_text(encoding="utf-8"))
    if not entries:
        raise SystemExit("README.md has no `## Changelog` entry to read the release version from")
    return entries[0]["version"].lstrip("v")


def packages(root: Path) -> dict[str, dict]:
    """Each package folder → its parsed `[project]`, its folder, and the module roots it owns."""
    out = {}
    for pp in sorted((root / "packages").glob("*/pyproject.toml")):
        d = tomllib.loads(pp.read_text(encoding="utf-8"))
        proj, folder = d["project"], pp.parent
        owned = {p.name for p in (folder / "src").glob("*") if p.is_dir() and (p / "__init__.py").exists()}
        owned |= set(d.get("tool", {}).get("setuptools", {}).get("py-modules", []))
        out[proj["name"]] = {"project": proj, "folder": folder, "owned": owned, "file": pp,
                             "build": d.get("build-system", {})}
    return out


def req_name(req: str) -> tuple[str, str, str]:
    """`name[extras]spec` → (name, extras, spec)."""
    m = re.match(r"^\s*([A-Za-z0-9_.-]+)\s*(\[[^\]]*\])?\s*(.*)$", req)
    return (m.group(1).lower(), (m.group(2) or "").strip("[]"), m.group(3).strip()) if m else (req, "", "")


def module_to_dist(pkgs: dict[str, dict]) -> dict[str, str]:
    table = dict(OUTSIDE)
    for dist, p in pkgs.items():
        for mod in p["owned"]:
            table[mod] = dist
    return table


def imports_of(path: Path) -> tuple[set[str], set[str]]:
    """The module roots a source file imports at its top and inside functions (absolute imports only)."""
    top, lazy = set(), set()
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        mods = ([a.name for a in node.names] if isinstance(node, ast.Import) else
                [node.module] if isinstance(node, ast.ImportFrom) and node.module and node.level == 0 else [])
        for m in mods:
            (top if node.col_offset == 0 else lazy).add(m.split(".")[0])
    return top, lazy


def check_packages(root: Path, version: str, r: Report) -> dict[str, dict]:
    pkgs = packages(root)
    m2d = module_to_dist(pkgs)
    stdlib = set(sys.stdlib_module_names)
    for dist, p in pkgs.items():
        rel = p["file"].relative_to(root).as_posix()
        proj = p["project"]
        if proj.get("version") != version:
            r.refuse(rel, f"version {proj.get('version')!r} is not the release {version}")
        if proj.get("readme") != "README.md" or not (p["folder"] / "README.md").is_file():
            r.refuse(rel, "does not declare its folder's README.md as `readme`, so its page on PyPI has no description")
        if proj.get("license") != LICENSE:
            r.refuse(rel, f"license {proj.get('license')!r} is not the repository's {LICENSE!r}")
        tools = [req_name(x)[2] for x in p["build"].get("requires", []) if req_name(x)[0] == "setuptools"]
        floor = [int(m.group(1)) for s in tools for m in [re.match(r"^>=\s*(\d+)", s)] if m]
        if not floor or floor[0] < SETUPTOOLS:
            r.refuse(rel, f"its build requirement {tools or 'none'} for setuptools is not >={SETUPTOOLS}, the first that "
                          "reads `license` written as an expression")
        reqs = [(None, x) for x in proj.get("dependencies", [])]
        reqs += [(extra, x) for extra, xs in proj.get("optional-dependencies", {}).items() for x in xs]
        declared_top, declared_all = set(), set()
        for extra, req in reqs:
            name, _, spec = req_name(req)
            (declared_all if extra else declared_top).add(name)
            declared_all.add(name)
            if name in pkgs and spec != f"=={version}":
                r.refuse(rel, f"{req!r} is not pinned =={version}" + (f" (extra {extra})" if extra else ""))
            if name in LOWER and f">={LOWER[name]}" not in spec.replace(" ", ""):
                r.refuse(rel, f"{req!r} does not carry the lower bound >={LOWER[name]}")
        for src in sorted((p["folder"] / "src").rglob("*.py")) + [p["folder"] / f"{m}.py" for m in p["owned"]
                                                                   if (p["folder"] / f"{m}.py").exists()]:
            top, lazy = imports_of(src)
            for mod in sorted((top | lazy) - stdlib - p["owned"] - {"__future__"}):
                d = m2d.get(mod)
                where = src.relative_to(root).as_posix()
                if d is None:
                    r.refuse(where, f"imports {mod!r}, which no build file or the gate's table maps to a distribution")
                elif mod in top and d not in declared_top:
                    r.refuse(where, f"imports {mod!r} at its top, and {rel} does not declare {d} as a dependency")
                elif d not in declared_all:
                    r.refuse(where, f"imports {mod!r} inside a function, and {rel} declares {d} neither as a "
                                    "dependency nor in an optional extra")
        for init in sorted((p["folder"] / "src").glob("*/__init__.py")):
            m = re.search(r'(?m)^__version__\s*=\s*"([^"]*)"', init.read_text(encoding="utf-8"))
            if m and m.group(1) != version:
                r.refuse(init.relative_to(root).as_posix(), f"__version__ {m.group(1)!r} is not the release {version}")
    return pkgs


def check_plugin(root: Path, version: str, r: Report) -> None:
    pj = json.loads((root / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    if pj.get("version") != version:
        r.refuse(".claude-plugin/plugin.json", f"version {pj.get('version')!r} is not the release {version}")
    mk = json.loads((root / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"))
    for p in mk.get("plugins", []):
        if p.get("name") == pj.get("name") and p.get("version") != version:
            r.refuse(".claude-plugin/marketplace.json", f"plugin version {p.get('version')!r} is not the release {version}")
    servers = json.loads((root / ".mcp.json").read_text(encoding="utf-8")).get("mcpServers", {})
    si = servers.get("self-interpreter", {})
    want = server_launch(version)
    if {k: si.get(k) for k in want} != want:
        r.refuse(".mcp.json", f"the self-interpreter does not launch as {want['command']} {' '.join(want['args'])}")
    for part in ("server/launch.py", "server/initialize.json", "server/tools.json"):
        if not (root / part).is_file():
            r.refuse(part, "the plugin's server launcher is missing (DESIGN.md §16)")


def blocks(text: str) -> list[tuple[int, str, str]]:
    """Every fenced block: (its opening line's offset, its language, its body)."""
    out, lines, i, pos = [], text.splitlines(keepends=True), 0, 0
    offsets = []
    for ln in lines:
        offsets.append(pos)
        pos += len(ln)
    while i < len(lines):
        m = FENCE.match(lines[i].rstrip("\n"))
        if m:
            j = i + 1
            while j < len(lines) and not lines[j].startswith("```"):
                j += 1
            out.append((offsets[i], m.group(1), "".join(lines[i + 1:j])))
            i = j + 1
        else:
            i += 1
    return out


def code_needs(lang: str, body: str, m2d: dict[str, str], commands: dict[str, str]) -> tuple[set[str], set[str]]:
    """What a block needs: (distributions its Python imports, a lazy reach included; console commands it runs)."""
    dists, cmds = set(), set()
    if lang == "python":
        roots, names = set(), set()
        try:
            for node in ast.walk(ast.parse(body)):
                if isinstance(node, ast.Import):
                    roots |= {a.name.split(".")[0] for a in node.names}
                elif isinstance(node, ast.ImportFrom) and node.module:
                    roots.add(node.module.split(".")[0])
                    names |= {a.name for a in node.names}
                elif isinstance(node, ast.Attribute):
                    names.add(node.attr)
                elif isinstance(node, ast.Name):
                    names.add(node.id)
        except SyntaxError:
            roots = {m.split(".")[0] for m in re.findall(r"^\s*(?:from|import)\s+([A-Za-z_][\w.]*)", body, re.M)}
            names = set(re.findall(r"\b([A-Za-z_]\w*)\s*\(", body))
        for root in roots:
            if root in m2d:
                dists.add(m2d[root])
                for (lroot, lname), reach in LAZY.items():
                    if lroot == root and lname in names:
                        dists |= set(reach)
    elif lang in ("bash", "sh", "shell", "console"):          # an unlabelled block is a diagram or output, not commands
        for line in body.splitlines():
            words = line.strip().split()
            if words and words[0] in commands:
                cmds.add(words[0])
    return dists, cmds


def uv_lines(text: str) -> tuple[dict[str, str], dict[str, str]]:
    """The uv commands in a skill's text before its first block: ({dist: spec} for `uv run --with`, {command: requirement}
    for `uvx --from`). A dist named with extras counts for the extras' distributions too (resolved by the caller)."""
    withs, froms = {}, {}
    for cmd in re.findall(r"`(uv run --no-project [^`]*python3)`", text):
        toks = shlex.split(cmd)
        for i, t in enumerate(toks):
            if t == "--with" and i + 1 < len(toks):
                name, extras, spec = req_name(toks[i + 1])
                withs[name] = spec
                for e in filter(None, extras.split(",")):
                    withs.setdefault(f"{name}[{e.strip()}]", spec)
    for cmd in re.findall(r"`(uvx --from [^`]*)`", text):
        toks = shlex.split(cmd.replace("…", ""))
        if len(toks) >= 4:
            froms[toks[3]] = toks[2]
    return withs, froms


def check_skills(root: Path, version: str, pkgs: dict[str, dict], r: Report) -> None:
    m2d = module_to_dist(pkgs)
    commands = {}
    for dist, p in pkgs.items():
        for cmd in p["project"].get("scripts", {}):
            commands[cmd] = dist
    commands["skilltree"] = "agent-skilltree"
    extras = {(dist, e): {req_name(x)[0] for x in xs} for dist, p in pkgs.items()
              for e, xs in p["project"].get("optional-dependencies", {}).items()}
    for f in sorted((root / "skills").rglob("*.md")):
        text = f.read_text(encoding="utf-8")
        bl = blocks(text)
        need, cmds = set(), set()
        for _, lang, body in bl:
            d, c = code_needs(lang, body, m2d, commands)
            need |= d
            cmds |= c
        if not need and not cmds:
            continue
        where = f.relative_to(root).as_posix()
        head = text[: bl[0][0]] if bl else text
        withs, froms = uv_lines(head)
        if need and not withs:
            r.refuse(where, f"its Python imports {sorted(need)} and it states no uv line before its first code block")
        covered = set()
        for name, spec in withs.items():
            if "[" in name:
                base, e = name[:-1].split("[", 1)
                covered |= extras.get((base, e), set())
            else:
                covered.add(name)
                if name in pkgs and spec != f"=={version}":
                    r.refuse(where, f"its uv line pins {name}{spec}, not =={version}")
                if name in LOWER and spec.replace(" ", "") != f">={LOWER[name]}":
                    r.refuse(where, f"its uv line names {name}{spec}, not >={LOWER[name]}")
        if withs:
            for d in sorted(need - covered):
                r.refuse(where, f"its uv line does not name {d}, which the code it runs imports")
        for c in sorted(cmds):
            req = froms.get(c)
            if req is None:
                r.refuse(where, f"it runs `{c}` and states no `uvx --from … {c}` line before its first code block")
                continue
            name, _, spec = req_name(req)
            if name != commands[c]:
                r.refuse(where, f"its uvx line for `{c}` names {name}, not {commands[c]}")
            elif name in pkgs and spec != f"=={version}":
                r.refuse(where, f"its uvx line pins {name}{spec}, not =={version}")
            elif name in LOWER and spec.replace(" ", "") != f">={LOWER[name]}":
                r.refuse(where, f"its uvx line names {name}{spec}, not >={LOWER[name]}")


def skill_name(p: Path) -> str | None:
    """A SKILL.md's frontmatter `name`, read without a YAML parser (a name is one plain scalar)."""
    m = re.match(r"^---\n(.*?)\n---\n", p.read_text(encoding="utf-8"), re.S)
    n = re.search(r"(?m)^name:\s*(.+?)\s*$", m.group(1)) if m else None
    return n.group(1).strip("'\"") if n else None


def check_copies(root: Path, r: Report) -> None:
    pairs = [(root / "packages/chainaios/src/chainaios/data/bandit-chain-system/SKILL.md", root / "skills/bandit-chain-system/SKILL.md"),
             (root / "packages/chainaios/src/chainaios/data/bandit-chain-system/SKILL.md", root / ".claude/skills/bandit-chain-system/SKILL.md"),
             (root / "skills/glyphsteer/SKILL.md", root / ".claude/skills/glyphsteer/SKILL.md"),
             (root / "skills/glyphsteer-dense/SKILL.md", root / ".claude/skills/glyphsteer-dense/SKILL.md")]
    pairs += [(pairs[0][0], p) for p in sorted((root / "personas").glob("*/.claude/skills/bandit-chain-system/SKILL.md"))]
    # every other hand-kept SKILL.md carrying a shipped skill's name — under a `.claude/skills/` folder or a package's own
    # folder — is a copy of it (a SkillTree node under `skills/*-tree/` and a GBA's generated body are not: the
    # regeneration diffs check those)
    shipped = {skill_name(p): p for p in sorted((root / "skills").rglob("SKILL.md"))
               if ".claude" not in p.relative_to(root / "skills").parts}
    # every package folder carries the repository's LICENSE, which its wheel ships
    pairs += [(root / "LICENSE", folder / "LICENSE") for folder in sorted((root / "packages").glob("*/"))
              if (folder / "pyproject.toml").is_file()]
    listed = {copy for _, copy in pairs}
    for p in sorted(root.rglob("SKILL.md")):
        rel = p.relative_to(root).parts
        if p in listed or rel[0] in ("skills", "personas") or not (".claude" in rel or rel[0] == "packages"):
            continue
        if skill_name(p) in shipped:
            pairs.append((shipped[skill_name(p)], p))
    for src, copy in pairs:
        where = copy.relative_to(root).as_posix()
        if copy.is_symlink():
            r.refuse(where, "is a link, not a copy")
        elif not copy.is_file():
            r.refuse(where, "is missing")
        elif copy.read_bytes() != src.read_bytes():
            r.refuse(where, f"differs from {src.relative_to(root).as_posix()}")
    # a copy reached through a linked folder — its own or any folder above it: the walks above enter no linked folder, so
    # this one follows links, each real folder once (a link cycle ends there), and names every SKILL.md it reaches that
    # carries a shipped skill's name with a link on its path
    seen = set()
    for dirpath, dirnames, files in os.walk(root, followlinks=True):
        rel = Path(dirpath).relative_to(root).parts
        real = os.path.realpath(dirpath)
        if real in seen or (rel and rel[0] in ("skills", "personas", ".git")):
            dirnames[:] = []
            continue
        seen.add(real)
        dirnames[:] = [d for d in dirnames if d not in (".git", "__pycache__", "node_modules")]
        if "SKILL.md" not in files or not rel or not (".claude" in rel or rel[0] == "packages"):
            continue
        link = next((root.joinpath(*rel[:i]) for i in range(1, len(rel) + 1) if root.joinpath(*rel[:i]).is_symlink()),
                    None)
        name = skill_name(Path(dirpath) / "SKILL.md")
        if link is not None and name in shipped:
            r.refuse(f"{Path(*rel).as_posix()}/SKILL.md", f"is reached through the link {link.relative_to(root).as_posix()}, "
                                                          f"not a copy of {shipped[name].relative_to(root).as_posix()}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="the gate on the one version line and the skills' uv lines")
    ap.add_argument("--root", default=str(HERE.parent))
    a = ap.parse_args(argv)
    root = Path(a.root).resolve()
    version, r = release(root), Report()
    pkgs = check_packages(root, version, r)
    check_plugin(root, version, r)
    check_skills(root, version, pkgs, r)
    check_copies(root, r)
    if r.refused:
        print(f"✗ {len(r.refused)} refused at release {version}:")
        for x in r.refused:
            print("  ", x)
        return 1
    print(f"✓ one version line at {version}: {len(pkgs)} packages, the plugin, .mcp.json, every skill's uv line and every copy")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
