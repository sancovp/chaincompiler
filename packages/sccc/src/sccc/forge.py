"""SCCC — the Skillchain Compiler-Compiler. Composes ACCC + CORCC + regular skills.

Same *CC shape: catch the SC sequence grammar → LINT its syntax → resolve each
step to a SKILL.md package (forged AC/CoR or regular skill) → compile the rollup
to `<name>/SKILL.md`. Built on the existing `skillchain` module for indexing,
resolution, and rollup compilation. Syntax + resolution only — never content.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import re

import skillchain as sc

from prompt_engineering import slugify, learn
from prompt_engineering.grammar import gate as cp_gate
from rulecatcher.db import connect

_STEP_RE = re.compile(r"\[(ac|cor|skill):([^\]]+)\]")
_HELD_RE = re.compile(r"\|([^|]+)\|")


@dataclass
class SCLanguage:
    name: str
    scope: str
    db: str
    rule_count: int


@dataclass
class StepRef:
    kind: str        # ac | cor | skill
    ref: str         # the referenced package name
    slug: str        # resolved package slug


def forge(name: str, sequences: list[str], *, db: str) -> SCLanguage:
    """Catch + ratify the SC sequence notation grammar (shape only)."""
    scope = f"sc:{name}"
    with connect(db) as cx:
        adopted = learn(cx, sequences, scope=scope, rule_types=("next_kind",), label=f"sc:{name}")
    return SCLanguage(name=name, scope=scope, db=db, rule_count=len(adopted))


def lint(language: SCLanguage, sequence: str) -> tuple[list, list]:
    """Syntax-lint an SC sequence against the ratified grammar (the *CC check)."""
    with connect(language.db) as cx:
        return cp_gate(cx, sequence, scope=language.scope)


def parse_sequence(sequence: str) -> tuple[list[StepRef], str | None]:
    steps = [StepRef(kind=m.group(1), ref=m.group(2).strip(), slug=slugify(m.group(2).strip()))
             for m in _STEP_RE.finditer(sequence)]
    held = _HELD_RE.search(sequence)
    return steps, (held.group(1).strip() if held else None)


def _index(skills_dir: str | None):
    roots = list(sc.SKILL_ROOTS)
    if skills_dir:
        roots.insert(0, Path(skills_dir))
    return sc.index_skills(roots=roots)


def resolve_steps(sequence: str, *, skills_dir: str | None = None) -> tuple[list, list[str]]:
    """Resolve each step to a package. Returns (rows, missing)."""
    steps, _ = parse_sequence(sequence)
    idx = _index(skills_dir)
    rows, missing = [], []
    for i, step in enumerate(steps, 1):
        rec = sc.resolve(step.slug, idx) or sc.resolve(step.ref, idx)
        if rec:
            rows.append((i, step.kind, step.ref, "ok", str(rec["path"])))
        else:
            rows.append((i, step.kind, step.ref, "MISSING", ""))
            missing.append(f"{step.kind}:{step.ref}")
    return rows, missing


def package(name: str, sequence: str, *, out_dir: str, skills_dir: str | None = None,
            description: str | None = None) -> Path:
    """Compile an SC sequence into a rollup `<name>/SKILL.md`.

    Resolves AC/CoR/skill steps to their packages (validated present) and rolls
    them up in order via the skillchain compiler.
    """
    steps, held = parse_sequence(sequence)
    spec = {
        "name": slugify(name),
        "description": description or (
            f"Skillchain: {' → '.join(f'{s.kind}:{s.ref}' for s in steps)}"
            + (f" → {held}" if held else "")
        ),
        "steps": [{"skill": s.slug} for s in steps],
    }
    idx = _index(skills_dir)
    ok, _rows, missing = sc.validate(spec, idx)
    if not ok:
        raise ValueError(f"cannot compile SC '{name}': unresolved steps {missing}")
    pkg, _deps = sc.compile_package(spec, idx, out_dir)
    return pkg / "SKILL.md"
