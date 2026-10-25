"""uvline.py — the one wording of a shipped skill's uv line (DESIGN.md §16).

A plugin install runs the packages from PyPI through uv, pinned to the release; a clone where `./install.sh` ran runs
them with its own `python3`. Every shipped skill that has an agent run package code says so once, before its first
code block, in these words. The skill generators (`build_meta_ape_skills.py`, `skills/bigdog/build.py`) write it from
here, the hand-written skills carry the same sentence, and `check_versions.py` parses the commands inside it.

    python_line(["chaincompiler-accc==0.3.0"])
    command_line("agent-skilltree>=0.4.0", "skilltree")
"""
from __future__ import annotations


def spec(s: str) -> str:
    """A requirement as a shell word: quoted when it holds a character the shell would read (`[`, `>`, `<`)."""
    return f'"{s}"' if any(ch in s for ch in "[]<>") else s


def python_line(specs: list[str]) -> str:
    """The sentence that tells an agent how to run a skill's Python, naming every distribution its code imports."""
    withs = " ".join(f"--with {spec(s)}" for s in specs)
    return (f"**Run its Python** from a plugin install with `uv run --no-project {withs} python3` — pipe a block in "
            "as `python3 - <<'PY'` … `PY` — and from a clone of the public repository where `./install.sh` ran, with "
            "the clone's `python3`.")


def command_line(requirement: str, command: str) -> str:
    """The sentence that tells an agent how to run a console command a distribution installs."""
    return (f"**Run `{command}`** from a plugin install as `uvx --from {spec(requirement)} {command} …`, and from a "
            f"clone where `./install.sh` ran, as `{command} …` in the environment it installed into.")
