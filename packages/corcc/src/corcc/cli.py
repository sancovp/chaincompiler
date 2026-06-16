"""corcc — forge personas (inner AC + outer CoR), lint CoR syntax, package."""
from __future__ import annotations

from pathlib import Path
import tempfile

import click

from .forge import forge_persona, inner_template, lint, outer_template, package, prime
from .notation import SEED_PERSONAS


@click.group()
@click.version_option(message="corcc %(version)s")
def main() -> None:
    """Chain-of-Reasoning Compiler-Compiler."""


@main.command()
def demo() -> None:
    """Forge ThinkLikeEinstein, lint CoR syntax, and emit a SKILL.md package."""
    with tempfile.TemporaryDirectory() as tmp:
        db = str(Path(tmp) / "corcc.db")
        persona = forge_persona(SEED_PERSONAS["ThinkLikeEinstein"], db=db)

        click.echo("══ 1. FORGE — a persona = inner AC (silent) + outer CoR (spoken) ══")
        click.echo(f"  forged '{persona.name}'  (chain grammar scope={persona.inner.scope})")

        click.echo("\n══ 2. INNER — attention chain (template for a section / thinking; NOT spoken) ══")
        click.echo(inner_template(persona))

        click.echo("\n══ 3. OUTER — the CoR the model MUST say (paragraph, ends in a decision) ══")
        click.echo(outer_template(persona))

        click.echo("\n══ 4. LINT — a well-formed CoR (valid syntax = persona intact) ══")
        good = "[Invariants] ⇒ [ThoughtExperiment] ⇒ [Simplicity] ⇒ |Reframe|"
        v, _ = lint(persona, good)
        click.echo(f"  {good}\n    → {'clean ✓ (intact)' if not v else 'violations'}")

        click.echo("\n══ 5. LINT — a malformed CoR (dropped a connector = melting) ══")
        bad = "[Invariants] [ThoughtExperiment] ⇒ |Reframe|"
        v, fixes = lint(persona, bad)
        if v:
            vio, fx = v[0], fixes[0]
            click.echo(f"  {bad}\n    ✗ {vio.verdict}: expected {vio.expected_token!r}, "
                       f"found {vio.found_token!r}; fix: insert {list(fx.candidate_tokens)}")
        else:
            click.echo("  (clean)")

        click.echo("\n══ 6. PACKAGE — compile the CoR to a publishable <name>/SKILL.md ══")
        path = package(persona, out_dir=tmp)
        click.echo(f"  wrote {path}")
        click.echo("  ── SKILL.md ──")
        click.echo("\n".join("  " + ln for ln in path.read_text().splitlines()))


@main.command(name="lint")
@click.argument("persona_name")
@click.argument("cor_text")
def lint_cmd(persona_name: str, cor_text: str) -> None:
    """Syntax-lint a CoR string against a seed persona's chain grammar."""
    import tempfile
    spec = SEED_PERSONAS.get(persona_name)
    if spec is None:
        raise click.ClickException(f"unknown persona {persona_name!r}; have {list(SEED_PERSONAS)}")
    with tempfile.TemporaryDirectory() as tmp:
        persona = forge_persona(spec, db=str(Path(tmp) / "c.db"))
        v, fixes = lint(persona, cor_text)
    if not v:
        click.echo("clean ✓ (valid CoR — persona intact)")
        return
    for vio, fx in zip(v, fixes):
        click.echo(f"✗ {vio.verdict}: expected {vio.expected_token!r}, found {vio.found_token!r}; "
                   f"fix: insert {list(fx.candidate_tokens)}")


if __name__ == "__main__":
    main()
