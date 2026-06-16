"""Shared skill-packager: a markdown body → a publishable `<name>/SKILL.md` dir.

The canonical output of every *CC is a MARKDOWN FILE carrying the chain /
instructions in its custom syntax. Wrapping it as `<name>/SKILL.md` is just the
easiest way to publish it everywhere so any agent auto-loads it. This module is
the one place that wrapper is written, shared by ACCC / CORCC / SCCC.
"""
from __future__ import annotations

from pathlib import Path
import re


def slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug or "skill"


def skill_markdown(name: str, description: str, body: str, *, extra: dict[str, str] | None = None) -> str:
    """Render the SKILL.md text (frontmatter + body). This IS the artifact."""
    fm = [f"name: {slugify(name)}", f"description: {description}"]
    for k, v in (extra or {}).items():
        fm.append(f"{k}: {v}")
    front = "\n".join(fm)
    return f"---\n{front}\n---\n\n{body.rstrip()}\n"


def write_skill(
    name: str,
    description: str,
    body: str,
    *,
    out_dir: str | Path,
    extra: dict[str, str] | None = None,
) -> Path:
    """Write `<out_dir>/<slug>/SKILL.md` and return its path."""
    slug = slugify(name)
    pkg = Path(out_dir) / slug
    pkg.mkdir(parents=True, exist_ok=True)
    md = skill_markdown(name, description, body, extra=extra)
    skill_path = pkg / "SKILL.md"
    skill_path.write_text(md, encoding="utf-8")
    return skill_path
