"""Every Python block of the eight capability skills and of `bandit-chain-system` runs alone (DESIGN.md §16 · §19).

A skill's uv line says to pipe a block into `python3 -`, so each block is run that way — on its own, in an empty folder,
with the `python3` running these tests — and must exit 0: a block that needs what another made has to make it. Run in
an environment whose packages are the ones a plugin install's uv line names (the wheel proof's) and in the editable one
`./install.sh` built. Run from the repository root: `python3 -m pytest scripts/tests`.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
from plugin_proof import CAPABILITIES  # noqa: E402  (the eight capability skills)

SKILLS = sorted(CAPABILITIES) + ["bandit-chain-system"]


def blocks(skill: str) -> list[str]:
    text = (REPO / "skills" / skill / "SKILL.md").read_text(encoding="utf-8")
    return re.findall(r"^```python\n(.*?)^```", text, re.S | re.M)


CASES = [(s, i, b) for s in SKILLS for i, b in enumerate(blocks(s))]


def test_every_skill_has_a_python_block():
    assert sorted({s for s, _, _ in CASES}) == sorted(SKILLS)


@pytest.mark.parametrize("skill, i, block", CASES, ids=[f"{s}-{i}" for s, i, _ in CASES])
def test_a_block_runs_alone_in_an_empty_folder(skill, i, block, tmp_path):
    r = subprocess.run([sys.executable, "-"], input=block, cwd=tmp_path, capture_output=True, text=True, timeout=600)
    assert r.returncode == 0, f"{skill} block {i} exited {r.returncode}:\n{(r.stdout + r.stderr)[-2000:]}"
