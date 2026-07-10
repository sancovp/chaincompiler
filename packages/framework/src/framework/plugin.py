"""plugin.py — package a framework as a Claude Code plugin (its operational face).

A framework package is ALWAYS a plugin. This assembles a valid plugin dir from
the generated framework skill (the {aios}-volume index/router) + its chapter,
and repaths the skill's chapter links to the bundled copy so the plugin is
self-contained. Only the chapter link paths are rewritten — never the prose.
"""
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path


def package_plugin(framework_skill_path: str | Path, chapter_dir: str | Path, *,
                   out_dir: str | Path, name: str, author: str = "",
                   description: str = "", version: str = "0.1.0") -> dict:
    """Build `<out_dir>/` as a plugin: plugin.json + skills/<name>/SKILL.md +
    the chapter bundled under resources/chapter/, chapter links repathed to the
    bundle. Returns a report with the repath count and a resolution check."""
    skill_src = Path(framework_skill_path)
    chap = Path(chapter_dir)
    if not skill_src.is_file():
        return {"ok": False, "error": f"framework skill not found: {skill_src}"}
    if not (chap / "chapter.md").is_file():
        return {"ok": False, "error": f"no chapter.md in chapter dir: {chap}"}

    out = Path(out_dir)
    skill_dir = out / "skills" / name
    res_dir = skill_dir / "resources" / "chapter"
    res_dir.mkdir(parents=True, exist_ok=True)

    for f in ("blog1.md", "blog2.md", "chapter.md"):
        if (chap / f).is_file():
            shutil.copy2(chap / f, res_dir / f)

    # repath: any path (absolute or relative) that ends in the chapter files
    # becomes the bundled relative reference. Nothing else in the body changes.
    body = skill_src.read_text(encoding="utf-8")
    body, n = re.subn(r"[^\s()`\[\]]*\b(blog1\.md|blog2\.md|chapter\.md)\b",
                      r"./resources/chapter/\1", body)
    (skill_dir / "SKILL.md").write_text(body, encoding="utf-8")

    manifest = {"name": name, "version": version,
                "description": description or f"The {name} framework plugin.",
                "author": author}
    (out / "plugin.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    # resolution check: every bundled reference in the written skill must exist
    dead = [m.group(0) for m in
            re.finditer(r"\./resources/chapter/(?:blog1|blog2|chapter)\.md",
                        (skill_dir / "SKILL.md").read_text(encoding="utf-8"))
            if not (skill_dir / m.group(0)).is_file()]
    return {"ok": not dead, "plugin_dir": str(out), "repathed": n,
            "dead_refs": dead}
