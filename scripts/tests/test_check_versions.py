"""The version gate's planted refusals (`scripts/check_versions.py`, DESIGN.md §16 · §18).

A copy of the tree passes; each copy planting ONE defect fails with exit 1, naming the place. Run from the repository
root: `python3 -m pytest scripts/tests`.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
GATE = REPO / "scripts" / "check_versions.py"
SKIP = shutil.ignore_patterns(".git", "site", "assets", "examples", "__pycache__", "*.egg-info", ".index.db",
                              "node_modules", "dist", "build", ".pytest_cache", "*.db")


def gate(root: Path) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(GATE), "--root", str(root)], capture_output=True, text=True)


@pytest.fixture()
def tree(tmp_path: Path) -> Path:
    root = tmp_path / "chaincompiler"
    root.mkdir()
    for name in ("README.md", ".mcp.json", "LICENSE"):
        shutil.copy2(REPO / name, root / name)
    for d in ("packages", "skills", ".claude-plugin", "personas", "server"):
        shutil.copytree(REPO / d, root / d, ignore=SKIP, symlinks=True)
    (root / ".claude" / "skills").mkdir(parents=True)
    for s in ("bandit-chain-system", "glyphsteer", "glyphsteer-dense"):
        shutil.copytree(REPO / ".claude" / "skills" / s, root / ".claude" / "skills" / s)
    return root


def sub(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    assert old in text, f"the plant's anchor {old!r} is not in {path}"
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def release(root: Path) -> str:
    return re.search(r"^### v(\S+)", (root / "README.md").read_text(encoding="utf-8"), re.M).group(1)


def refused(root: Path, *names: str) -> str:
    r = gate(root)
    assert r.returncode == 1, r.stdout + r.stderr
    for n in names:
        assert n in r.stdout, f"{n!r} not named in:\n{r.stdout}"
    return r.stdout


def test_the_tree_passes(tree):
    r = gate(tree)
    assert r.returncode == 0, r.stdout + r.stderr


def test_a_package_version_that_differs_is_refused(tree):
    v = release(tree)
    sub(tree / "packages/goldenreq/pyproject.toml", f'version = "{v}"', 'version = "9.9.9"')
    refused(tree, "packages/goldenreq/pyproject.toml", "version '9.9.9'")


def test_a_dunder_version_that_differs_is_refused(tree):
    v = release(tree)
    sub(tree / "packages/sccc/src/sccc/__init__.py", f'__version__ = "{v}"', '__version__ = "9.9.9"')
    refused(tree, "packages/sccc/src/sccc/__init__.py", "__version__ '9.9.9'")


def test_a_plugin_manifest_that_differs_is_refused(tree):
    v = release(tree)
    sub(tree / ".claude-plugin/plugin.json", f'"version": "{v}"', '"version": "9.9.9"')
    refused(tree, ".claude-plugin/plugin.json")


def test_a_marketplace_entry_that_differs_is_refused(tree):
    v = release(tree)
    sub(tree / ".claude-plugin/marketplace.json", f'"version": "{v}"', '"version": "9.9.9"')
    refused(tree, ".claude-plugin/marketplace.json")


def test_a_sibling_not_pinned_exactly_is_refused(tree):
    v = release(tree)
    sub(tree / "packages/personapack/pyproject.toml", f'"personacc=={v}"', '"personacc"')
    refused(tree, "packages/personapack/pyproject.toml", "'personacc' is not pinned")


def test_an_extra_sibling_not_pinned_exactly_is_refused(tree):
    v = release(tree)
    sub(tree / "packages/glyphsteer/pyproject.toml", f'"chaincompiler=={v}"', '"chaincompiler>=0.1"')
    refused(tree, "packages/glyphsteer/pyproject.toml", "(extra grammar)")


def test_an_outside_dependency_without_its_lower_bound_is_refused(tree):
    sub(tree / "packages/skill2framework/pyproject.toml", '"agent-skilltree>=0.4.0"', '"agent-skilltree"')
    refused(tree, "packages/skill2framework/pyproject.toml", "lower bound >=0.4.0")


def test_a_build_file_without_its_readme_is_refused(tree):
    sub(tree / "packages/sccc/pyproject.toml", 'readme = "README.md"\n', "")
    refused(tree, "packages/sccc/pyproject.toml", "does not declare its folder's README.md")


def test_a_build_file_without_the_license_is_refused(tree):
    sub(tree / "packages/goldenreq/pyproject.toml", 'license = "MIT"', 'license = "Apache-2.0"')
    refused(tree, "packages/goldenreq/pyproject.toml", "license 'Apache-2.0' is not the repository's 'MIT'")


def test_a_setuptools_too_old_for_the_license_is_refused(tree):
    sub(tree / "packages/rulecatcher/pyproject.toml", '"setuptools>=77"', '"setuptools>=61.0"')
    refused(tree, "packages/rulecatcher/pyproject.toml", "is not >=77")


def test_an_undeclared_import_is_refused(tree):
    src = tree / "packages/goldenreq/src/goldenreq/__init__.py"
    src.write_text("import numpy\n" + src.read_text(encoding="utf-8"), encoding="utf-8")
    refused(tree, "packages/goldenreq/src/goldenreq/__init__.py", "does not declare numpy")


def test_a_mcp_pin_that_differs_is_refused(tree):
    v = release(tree)
    sub(tree / ".mcp.json", f"chaincompiler-si=={v}", "chaincompiler-si==9.9.9")
    refused(tree, ".mcp.json")


def test_a_server_launched_straight_through_uvx_is_refused(tree):
    # the launch Claude Code times out on a fresh machine: no launcher answering first
    v = release(tree)
    (tree / ".mcp.json").write_text(json.dumps({"mcpServers": {"self-interpreter": {
        "command": "uvx", "args": ["--from", f"chaincompiler-si=={v}", "si-server"]}}}))
    refused(tree, ".mcp.json", "does not launch as uv run")


def test_a_plugin_without_its_server_launcher_is_refused(tree):
    (tree / "server" / "tools.json").unlink()
    refused(tree, "server/tools.json", "launcher is missing")


def test_a_skill_whose_code_has_no_uv_line_is_refused(tree):
    p = tree / "skills/forge-cor/SKILL.md"
    p.write_text(re.sub(r"(?m)^\*\*Run its Python\*\*.*\n\n", "", p.read_text(encoding="utf-8")), encoding="utf-8")
    refused(tree, "skills/forge-cor/SKILL.md", "states no uv line")


def test_a_uv_line_missing_a_distribution_its_code_reaches_is_refused(tree):
    v = release(tree)
    for p in (tree / "skills/bandit-chain-system/SKILL.md",):
        sub(p, f" --with glyphsteer=={v}", "")
    refused(tree, "skills/bandit-chain-system/SKILL.md", "does not name glyphsteer")


def test_a_uv_line_pinned_to_another_version_is_refused(tree):
    v = release(tree)
    sub(tree / "skills/forge-skillchain/SKILL.md", f"sccc=={v}", "sccc==9.9.9")
    refused(tree, "skills/forge-skillchain/SKILL.md", "pins sccc==9.9.9")


def test_a_command_without_its_uvx_line_is_refused(tree):
    p = tree / "skills/report-missed-skill/SKILL.md"
    p.write_text(re.sub(r"(?m)^\*\*Run `skilltree`\*\*.*\n\n", "", p.read_text(encoding="utf-8")), encoding="utf-8")
    refused(tree, "skills/report-missed-skill/SKILL.md", "states no `uvx --from")


def test_a_copy_that_differs_is_refused(tree):
    p = tree / ".claude/skills/glyphsteer/SKILL.md"
    p.write_text(p.read_text(encoding="utf-8") + "\nan edit made in one copy only\n", encoding="utf-8")
    refused(tree, ".claude/skills/glyphsteer/SKILL.md", "differs from skills/glyphsteer/SKILL.md")


def test_a_packages_own_copy_of_a_shipped_skill_that_differs_is_refused(tree):
    p = tree / "packages/glyphsteer/.claude/skills/glyphsteer/SKILL.md"
    p.write_text(p.read_text(encoding="utf-8") + "\nan older reading kept in the package's own copy\n", encoding="utf-8")
    refused(tree, "packages/glyphsteer/.claude/skills/glyphsteer/SKILL.md", "differs from skills/glyphsteer/SKILL.md")


def test_a_package_without_the_license_is_refused(tree):
    (tree / "packages/sccc/LICENSE").unlink()
    refused(tree, "packages/sccc/LICENSE: is missing")


def test_a_copy_that_is_a_link_is_refused(tree):
    p = tree / "personas/chainforge/.claude/skills/bandit-chain-system/SKILL.md"
    p.unlink()
    p.symlink_to(tree / "skills/bandit-chain-system/SKILL.md")
    refused(tree, "personas/chainforge/.claude/skills/bandit-chain-system/SKILL.md", "is a link")
