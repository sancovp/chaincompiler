"""Persona compiler — the front-end that ingests a glyph-persona-program and emits
the artifacts the rest of ChainCompiler already eats.

A BizziBee-style prompt is not prose: it is a program in a cognition-DSL with three
layers, each of which a ChainCompiler tool already compiles —

  [VarDefs]{ [🌸‍💧]=NectarWF, 📃=drilldown, … }  → a glyphsteer LEGEND (glyph↔meaning)
  🌸‍💧 → 🍯 → 🍹  (dense-rune chains)              → HoneyC compiles / rulecatcher gates
  ⚙️0–5  (if / while / for / 🔁 / terminal)        → a workflow (the SI executes; here: extracted)
  [ROLE]…[/ROLE]  (the persona wrapper)            → a SKILL.md (the one type)

So this module parses the human-authored glyph-persona into: a `legend.json`, a list of
workflow steps, and a `<cogid>/SKILL.md` — putting the persona INSIDE the closed algebra.
Full execution of the ⚙️ control flow is the SI's job (ASPIRATIONAL: `persona run`).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from .skillpack import slugify, write_skill

# operator glyphs that are NOT vocabulary entries (arrows / connectors)
_OPERATORS = set("→⇒⇔↔⟶⇄⟷=+/")
_NONASCII = re.compile(r"[^\x00-\x7f]+")
_IDENT = re.compile(r"[A-Za-z][A-Za-z0-9]*")
_HEADER = re.compile(r"^\[([A-Za-z][A-Za-z0-9]*)\]:\s*(.*)$", re.M)
_VARDEFS = re.compile(r"\[VarDefs\]:\s*\{(.*?)\}\s*(?:\n|$)", re.S)
_STEP = re.compile(r"⚙️([0-9][0-9.]*)\)\s*`?(.*)")
_CTRL = re.compile(r"\b(if|while|for|end)\b|🔁", re.I)


@dataclass
class Persona:
    name: str
    description: str
    fields: dict[str, str] = field(default_factory=dict)
    legend: object = None                 # a glyphsteer.Vocabulary
    steps: list[dict] = field(default_factory=list)


# ---- block parsing ----------------------------------------------------------
def parse_header(text: str) -> dict[str, str]:
    """The `[TAG]: value` header fields (ROLE, CogID, LAW, Mission, …)."""
    return {k: v.strip() for k, v in _HEADER.findall(text)}


def vardefs_text(text: str) -> str:
    m = _VARDEFS.search(text)
    return m.group(1) if m else ""


# ---- VarDefs → legend -------------------------------------------------------
def _clean_glyph(run: str) -> str:
    return "".join(ch for ch in run if ch not in _OPERATORS).strip()


def extract_legend(text: str):
    """Parse the VarDefs glyph↔name pairs into a glyphsteer Vocabulary (best-effort)."""
    from glyphsteer import Axis, Vocabulary, author
    raw = vardefs_text(text) or text
    specs, gseen, nseen = [], set(), set()
    for piece in re.split(r"[,\n]", raw):
        glyph_runs = [g for g in (_clean_glyph(r) for r in _NONASCII.findall(piece)) if g]
        names = _IDENT.findall(piece)
        if not glyph_runs or not names:
            continue
        glyph, name = glyph_runs[0], names[0]
        if glyph in gseen or name in nseen:
            continue
        try:
            Vocabulary([Axis(name, glyph)])          # validates clean glyph + derivable tag
        except ValueError:
            continue
        gseen.add(glyph); nseen.add(name)
        specs.append({"name": name, "glyph": glyph, "description": piece.strip()})
    return author(specs)


# ---- ⚙️ steps → workflow ----------------------------------------------------
def extract_workflow(text: str) -> list[dict]:
    """The numbered ⚙️N) steps, in order, with detected control-flow keywords."""
    steps = []
    for num, body in _STEP.findall(text):
        body = body.strip().rstrip("`").strip()
        ctrl = sorted({m.group(0).lower() for m in _CTRL.finditer(body)})
        steps.append({"step": num, "ctrl": ctrl, "body": body[:140]})
    return steps


# ---- compile ----------------------------------------------------------------
def parse_persona(text: str) -> Persona:
    h = parse_header(text)
    name = h.get("CogID") or h.get("ROLE") or "persona"
    name = re.sub(r"[*]+$", "", name).strip()
    return Persona(
        name=name,
        description=h.get("Mission", f"{name} persona"),
        fields=h,
        legend=extract_legend(text),
        steps=extract_workflow(text),
    )


def _render_body(p: Persona) -> str:
    from glyphsteer import render_legend
    h = p.fields
    out = [f"# {h.get('ROLE', p.name)} — compiled persona", ""]
    for key in ("LAW", "Mission", "FnMx", "ActsLike", "OutputWrapper"):
        if h.get(key):
            out.append(f"- **{key}**: {h[key]}")
    out += ["", "## Legend (the glyph vocabulary)", "```", render_legend(p.legend), "```", ""]
    out += ["## Workflow (⚙️ steps)", ""]
    for s in p.steps:
        ctrl = f"  _[{', '.join(s['ctrl'])}]_" if s["ctrl"] else ""
        out.append(f"{s['step']}. {s['body']}{ctrl}")
    out += ["", "> Terminal output is reached only after a multi-round sequence of the "
            "looping steps (the ⚙️ workflow is executable via the SI — ASPIRATIONAL)."]
    return "\n".join(out)


def lint_pipeline(p: Persona) -> dict | None:
    """If the legend + ChainCompiler grammar gate are available, lint a glyph chain
    drawn from the legend (rulecatcher syntax gate). Returns a verdict or None."""
    try:
        from glyphsteer import GlyphGrammar
    except Exception:
        return None
    glyphs = p.legend.glyphs
    if len(glyphs) < 2:
        return None
    code = p.legend.code(glyphs[:3])
    try:
        with GlyphGrammar(p.legend, scope=f"persona_{slugify(p.name)}") as gg:
            lint = gg.lint(code)
            return {"chain": code, "verdict": lint.verdict}
    except Exception:
        return None


def compile_persona(text: str, out_dir: str | Path) -> dict:
    """Compile a glyph-persona-program → `<cogid>/SKILL.md` + `legend.json`."""
    from glyphsteer import save_legend
    p = parse_persona(text)
    skill_path = write_skill(p.name, p.description, _render_body(p), out_dir=out_dir,
                             extra={"glyphs": p.legend.code(p.legend.glyphs[:1]) or ""})
    legend_path = skill_path.parent / "legend.json"
    save_legend(p.legend, legend_path)
    return {
        "name": p.name,
        "skill": str(skill_path),
        "legend": str(legend_path),
        "axes": len(p.legend.axes),
        "steps": len(p.steps),
        "gate": lint_pipeline(p),
    }
