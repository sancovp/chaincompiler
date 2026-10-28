"""chapter.py — assemble a framework CHAPTER from two rendered blog posts.

A chapter = Blog 1 (narrative) + Blog 2 (deep dive), copied VERBATIM into one
self-contained dir, wired with relative cross-links + CTAs, plus a `chapter.md`
manifest (what the framework skill and the tome point at). The blogs' prose is
never rewritten — only the link/CTA block and the manifest are added.
"""
from __future__ import annotations

from pathlib import Path


# "## Chapter links", not "## Links": render_blog1 already emits a "## Links" section
# when the core carries URLs — the first dogfood produced a doubled heading. Distinct
# heading = no collision, and the chapter block stays a pure addition.
def _links_block(entries: list[str], cta: str) -> str:
    return "\n\n## Chapter links\n\n" + "\n".join(f"- {e}" for e in entries) + f"\n\n> **{cta}**\n"


def assemble_chapter(blog1_path: str | Path, blog2_path: str | Path, *,
                     chapter_dir: str | Path, framework_name: str,
                     plugin_url: str = "", skill_links: list[str] | None = None,
                     abstract: str = "") -> dict:
    """Copy blog1/blog2 into `chapter_dir`, append the cross-link/CTA block to
    each, and write the `chapter.md` manifest. Returns a report of what was
    written. Idempotent: re-running overwrites the chapter dir's three files.
    `skill_links` entries are "Name|url" pairs.
    """
    b1, b2 = Path(blog1_path), Path(blog2_path)
    if not b1.is_file():
        return {"ok": False, "error": f"blog1 not found: {b1}"}
    if not b2.is_file():
        return {"ok": False, "error": f"blog2 not found: {b2}"}
    out = Path(chapter_dir)
    out.mkdir(parents=True, exist_ok=True)
    skills = skill_links or []

    def skill_entries() -> list[str]:
        entries = []
        for pair in skills:
            name, _, url = pair.partition("|")
            entries.append(f"Skill — {name.strip()}: {url.strip() or '(link pending)'}")
        return entries

    blog1 = b1.read_text(encoding="utf-8").rstrip()
    blog1 += _links_block(
        ["Deep dive — how it works: ./blog2.md"]
        + ([f"Get the plugin: {plugin_url}"] if plugin_url else [])
        + skill_entries(),
        cta=f"Install the plugin and run it yourself: {plugin_url or './blog2.md'}")
    (out / "blog1.md").write_text(blog1 + "\n", encoding="utf-8")

    blog2 = b2.read_text(encoding="utf-8").rstrip()
    blog2 += _links_block(
        ["The story — why this exists: ./blog1.md"]
        + ([f"Get the plugin: {plugin_url}"] if plugin_url else []),
        cta=f"Read the story, then install: {plugin_url or './blog1.md'}")
    (out / "blog2.md").write_text(blog2 + "\n", encoding="utf-8")

    manifest = [f"# {framework_name} — chapter", ""]
    if abstract:
        manifest += [abstract, ""]
    manifest += ["## Contents", "",
                 "1. The narrative: ./blog1.md",
                 "2. The deep dive: ./blog2.md", ""]
    if plugin_url:
        manifest += [f"Plugin: {plugin_url}", ""]
    if skills:
        manifest += ["## Skills", ""] + [f"- {e}" for e in skill_entries()] + [""]
    (out / "chapter.md").write_text("\n".join(manifest), encoding="utf-8")

    return {"ok": True, "chapter_dir": str(out),
            "files": ["blog1.md", "blog2.md", "chapter.md"]}
