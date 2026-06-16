"""sccc — chain forged ACs + CoRs + regular skills into one SKILL.md rollup."""
from __future__ import annotations

from pathlib import Path
import tempfile

import click

from . import forge, lint, package, resolve_steps
from .notation import SEED_SEQUENCES

_STUB_SKILL = """---
name: summarize
description: Condense the prior step's result into a short answer.
---

Summarize the input into 3 sentences and state the single most important takeaway.
"""


@click.group()
@click.version_option(message="sccc %(version)s")
def main() -> None:
    """Skillchain Compiler-Compiler — the highest composite (AC + CoR + skills)."""


@main.command()
def demo() -> None:
    """Forge AC + CoR + a regular skill, chain them into one SKILL.md rollup."""
    import accc
    import corcc
    from corcc.notation import EINSTEIN

    with tempfile.TemporaryDirectory() as tmp:
        db = str(Path(tmp) / "cc.db")
        skills_dir = str(Path(tmp) / "skills")
        out_dir = str(Path(tmp) / "dist")

        click.echo("══ 1. FORGE + PACKAGE the parts (each a SKILL.md) ══")
        accc.forge("debug-attention", ["[Symptom] ⇒ [Repro] ⇒ [Hypothesis] ⇒ |Localize|"], db=db)
        ac_path = accc.package("debug-attention",
                               "[Symptom] ⇒ [Repro] ⇒ [Hypothesis] ⇒ |Localize|", out_dir=skills_dir)
        persona = corcc.forge_persona(EINSTEIN, db=db)
        cor_path = corcc.package(persona, out_dir=skills_dir)
        skill_path = Path(skills_dir) / "summarize" / "SKILL.md"
        skill_path.parent.mkdir(parents=True, exist_ok=True)
        skill_path.write_text(_STUB_SKILL, encoding="utf-8")
        ac_slug, cor_slug = ac_path.parent.name, cor_path.parent.name
        click.echo(f"  AC  → {ac_slug}/SKILL.md")
        click.echo(f"  CoR → {cor_slug}/SKILL.md")
        click.echo(f"  skill → summarize/SKILL.md  (a regular skill)")

        click.echo("\n══ 2. FORGE the SC sequence grammar (shape) ══")
        scl = forge("debug-then-explain", SEED_SEQUENCES, db=db)
        click.echo(f"  forged scope={scl.scope}, {scl.rule_count} rules")

        sequence = f"[ac:{ac_slug}] ⇒ [cor:{cor_slug}] ⇒ [skill:summarize] ⇒ |Answer|"
        click.echo(f"\n══ 3. LINT the SC sequence (syntax) ══\n  {sequence}")
        v, fixes = lint(scl, sequence)
        click.echo(f"    → {'clean ✓' if not v else 'violations'}")

        click.echo("\n══ 4. LINT a malformed sequence (dropped ⇒) ══")
        bad = f"[ac:{ac_slug}] [skill:summarize] ⇒ |Answer|"
        v2, fx2 = lint(scl, bad)
        if v2:
            click.echo(f"  {bad}\n    ✗ {v2[0].verdict}: expected {v2[0].expected_token!r}, "
                       f"found {v2[0].found_token!r}; fix insert {list(fx2[0].candidate_tokens)}")

        click.echo("\n══ 5. RESOLVE steps (each must exist on disk) ══")
        rows, missing = resolve_steps(sequence, skills_dir=skills_dir)
        for i, kind, ref, status, path in rows:
            click.echo(f"  {'✓' if status=='ok' else '✗'} [{i}] {kind:5} {ref}")

        click.echo("\n══ 6. PACKAGE — roll the chain up into one SKILL.md ══")
        sc_path = package("debug-then-explain", sequence, out_dir=out_dir, skills_dir=skills_dir)
        click.echo(f"  wrote {sc_path}")
        click.echo("  ── SKILL.md (rollup) ──")
        click.echo("\n".join("  " + ln for ln in sc_path.read_text().splitlines()[:24]))

        click.echo("\n══ 7. The capstone ══")
        click.echo("  AC → CoR → SC: an attention template, a spoken reasoning chain, and a regular "
                   "skill, composed into ONE publishable skillchain. All SKILL.md. All syntax-checked.")


if __name__ == "__main__":
    main()
