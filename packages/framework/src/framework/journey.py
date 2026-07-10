"""journey.py — the JourneyCore model + the deterministic Blog-1 renderer.

The BLOG ORGAN law: the narrative blog is never hand-written — an agent FILLS
this model from the AIOS's real journey (its CLAUDE.md / README / dev log) and
runs `render_blog1`, so the output shape is deterministic and every datum
renders exactly once. This is the DIY (dependency-free) renderer; the fields
are the Hero-arc set the skill2framework pipeline fills.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class JourneyCore:
    journey_name: str                 # the AIOS/framework this is the journey OF
    domain: str                       # free-form domain label ("publishing", "health", …)
    hook: str                         # AUTHORED opening sentence (never string-derived)
    status_quo: str                   # "I was …" — the painful state BEFORE
    obstacle: str                     # "I identified … when …" — the blocker + the moment seen
    overcome: str                     # "I finally … and tried …" — the shift + what was built
    accomplishment: str               # "… and now …" — the result as feeling + proof
    the_boon: str                     # the ONE transferable reframe (not the artifact)
    demo_description: str             # what a demo would show
    why_this_matters: str             # the meta-level
    universal_application: str        # how a reader applies it to THEIR domain
    github_url: str = ""              # the code
    plugin_url: str = ""              # the installable face
    deep_dive_url: str = ""           # Blog 2, when known (the chapter step wires it later)
    skill_urls: list[str] = field(default_factory=list)   # "Name|url" pairs
    hashtags: list[str] = field(default_factory=list)


def render_blog1(core: JourneyCore) -> str:
    """Render Blog 1 (the narrative chapter-opener) from a filled JourneyCore.

    Deterministic template: the authored hook opens, each field renders once, the
    links/CTA block closes. Optional fields render only when present.
    """
    lines: list[str] = [f"# {core.journey_name} — the story", ""]
    lines += [f"*{core.hook}*", ""]
    lines += ["## Where I was", "", core.status_quo, ""]
    lines += ["## The wall", "", core.obstacle, ""]
    lines += ["## The turn", "", core.overcome, ""]
    lines += ["## Where I am now", "", core.accomplishment, ""]
    lines += ["## The boon — what transfers", "", core.the_boon, ""]
    lines += ["## See it", "", core.demo_description, ""]
    lines += ["## Why this matters", "", core.why_this_matters, ""]
    lines += ["## Take action", "", core.universal_application, ""]

    links: list[str] = []
    if core.deep_dive_url:
        links.append(f"- Deep dive — how it works: {core.deep_dive_url}")
    if core.plugin_url:
        links.append(f"- Get the plugin: {core.plugin_url}")
    if core.github_url and core.github_url != core.plugin_url:
        links.append(f"- The code: {core.github_url}")
    for pair in core.skill_urls:
        name, _, url = pair.partition("|")
        links.append(f"- Skill — {name.strip()}: {url.strip() or '(link pending)'}")
    if links:
        lines += ["## Links", ""] + links + [""]
    if core.hashtags:
        lines += [" ".join(f"#{h.lstrip('#')}" for h in core.hashtags), ""]
    return "\n".join(lines)
