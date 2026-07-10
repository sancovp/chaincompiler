"""framework package tests: the deterministic glue of the chapter rung."""
from __future__ import annotations

import json
from pathlib import Path

from framework import (
    JourneyCore,
    assemble_chapter,
    fold_into_tome,
    package_plugin,
    render_blog1,
)


def _core(**over) -> JourneyCore:
    base = dict(
        journey_name="demo-aios", domain="testing",
        hook="One sentence that actually hooks.",
        status_quo="I was drowning in flat skills.",
        obstacle="I identified the melt when the pile hit 100.",
        overcome="I finally built the tree and tried walking it.",
        accomplishment="And now I load one layer and walk.",
        the_boon="Structure is a render, not a burden.",
        demo_description="A session descending three layers by Read.",
        why_this_matters="Substrates ship forests; agents need trees.",
        universal_application="Root any flat pile you own.",
        plugin_url="https://example.com/plugin",
        skill_urls=["Walker|https://example.com/walker"],
        hashtags=["skilltree"],
    )
    base.update(over)
    return JourneyCore(**base)


def test_render_blog1_each_datum_once_and_links():
    md = render_blog1(_core())
    assert md.count("One sentence that actually hooks.") == 1
    assert md.count("Root any flat pile you own.") == 1          # renders exactly once
    assert "Get the plugin: https://example.com/plugin" in md
    assert "Skill — Walker: https://example.com/walker" in md
    assert "#skilltree" in md
    # optional field absent → section omitted
    assert "Deep dive" not in md
    assert "Deep dive — how it works: https://x/b2" in render_blog1(_core(deep_dive_url="https://x/b2"))


def test_assemble_chapter_verbatim_plus_links(tmp_path: Path):
    b1 = tmp_path / "b1.md"; b1.write_text("# story\n\nProse one.\n")
    b2 = tmp_path / "b2.md"; b2.write_text("# mechanics\n\nProse two.\n")
    rep = assemble_chapter(b1, b2, chapter_dir=tmp_path / "chap", framework_name="demo",
                           plugin_url="https://example.com/p",
                           skill_links=["Walker|https://example.com/w"], abstract="Two posts.")
    assert rep["ok"]
    out1 = (tmp_path / "chap" / "blog1.md").read_text()
    out2 = (tmp_path / "chap" / "blog2.md").read_text()
    man = (tmp_path / "chap" / "chapter.md").read_text()
    assert out1.startswith("# story\n\nProse one.")               # prose verbatim, additions only
    assert "./blog2.md" in out1 and "https://example.com/p" in out1
    assert "./blog1.md" in out2
    assert "1. The narrative: ./blog1.md" in man and "Walker" in man


def test_assemble_chapter_missing_blog_reports(tmp_path: Path):
    rep = assemble_chapter(tmp_path / "nope.md", tmp_path / "also-nope.md",
                           chapter_dir=tmp_path / "chap", framework_name="demo")
    assert not rep["ok"] and "blog1" in rep["error"]


def test_package_plugin_repaths_and_resolves(tmp_path: Path):
    chap = tmp_path / "chap"; chap.mkdir()
    for f in ("blog1.md", "blog2.md", "chapter.md"):
        (chap / f).write_text(f"content of {f}\n")
    fw = tmp_path / "demo-volume"; fw.mkdir()
    skill = fw / "SKILL.md"
    skill.write_text("---\nname: demo-volume\ndescription: d\n---\n\n"
                     f"The chapter: {chap}/blog1.md and {chap}/blog2.md\n")
    rep = package_plugin(skill, chap, out_dir=tmp_path / "plug", name="demo-volume",
                         author="tester")
    assert rep["ok"] and rep["repathed"] == 2 and rep["dead_refs"] == []
    body = (tmp_path / "plug" / "skills" / "demo-volume" / "SKILL.md").read_text()
    assert "./resources/chapter/blog1.md" in body and str(chap) not in body
    manifest = json.loads((tmp_path / "plug" / "plugin.json").read_text())
    assert manifest["name"] == "demo-volume" and manifest["author"] == "tester"


def test_package_plugin_preserves_link_display_text(tmp_path: Path):
    # the first dogfood's finding: bare filenames in link LABELS are not paths —
    # only the link target (and path-shaped tokens) may be repathed
    chap = tmp_path / "chap"; chap.mkdir()
    for f in ("blog1.md", "blog2.md", "chapter.md"):
        (chap / f).write_text(f"content of {f}\n")
    fw = tmp_path / "v"; fw.mkdir()
    (fw / "SKILL.md").write_text("---\nname: v\ndescription: d\n---\n\n"
                                 f"Read [blog1.md]({chap}/blog1.md) and [the story](blog2.md).\n")
    rep = package_plugin(fw / "SKILL.md", chap, out_dir=tmp_path / "plug", name="v")
    assert rep["ok"] and rep["repathed"] == 2
    body = (tmp_path / "plug" / "skills" / "v" / "SKILL.md").read_text()
    assert "[blog1.md](./resources/chapter/blog1.md)" in body    # label intact, target repathed
    assert "[the story](./resources/chapter/blog2.md)" in body   # bare-filename target repathed


def test_fold_into_tome_delegates_to_skilltree(tmp_path: Path):
    from skilltree import SkillTree, TreeNode, is_valid, materialize
    root = tmp_path / "tome"
    materialize(SkillTree(TreeNode("my-tome", "sc", children=[
        TreeNode("patterns", "sc", description="the volume")])), root)
    fw = tmp_path / "demo-volume"; fw.mkdir()
    (fw / "SKILL.md").write_text("---\nname: demo-volume\ndescription: routes demo\n---\n\nbody\n")
    rep = fold_into_tome(fw, volume="patterns", tome_root=root)
    assert rep["ok"] and rep["rows"] == 1
    assert not Path(rep["row"]["skill_path"]).is_absolute()      # relative by default
    assert is_valid(root)
    # idempotent
    assert fold_into_tome(fw, volume="patterns", tome_root=root)["updated"]
