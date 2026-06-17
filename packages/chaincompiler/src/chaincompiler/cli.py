"""cc — ChainCompiler. Construct a whole cognition-language for a domain."""
from __future__ import annotations

from pathlib import Path
import tempfile

import click

from corcc.notation import Move, PersonaSpec

from .construct import construct_language

# A sample domain persona: triage an incident → decide severity.
TRIAGE = PersonaSpec(
    name="TriageIncident",
    blurb="scope the blast radius, find the trigger, decide severity",
    moves=(
        Move("BlastRadius", ("who is affected", "scope", "how many")),
        Move("Trigger", ("what changed", "trigger", "first seen")),
        Move("Severity", ("severity", "sev", "decide", "priority")),
    ),
)


@click.group()
@click.version_option(message="cc %(version)s")
def main() -> None:
    """ChainCompiler — the umbrella over ACCC / CORCC / SCCC."""


@main.command()
def layers() -> None:
    """Print the stack."""
    click.echo("CC (ChainCompiler)")
    click.echo("  ACCC  — attention template (how to think)        → SKILL.md")
    click.echo("  CORCC — spoken reasoning that makes a decision    → SKILL.md  (HAS AC)")
    click.echo("  SCCC  — chains AC + CoR + regular skills          → SKILL.md  (HAS CoR, AC, skills)")
    click.echo("  each: catch grammar → LINT (syntax only) → compile .md → package <name>/SKILL.md")


@main.command()
def demo() -> None:
    """Construct a brand-new domain language (AC + CoR + SC) in one call."""
    with tempfile.TemporaryDirectory() as tmp:
        bundle = construct_language(
            "triage",
            ac_chain="[Symptom] ⇒ [Scope] ⇒ [Change] ⇒ |Severity|",
            cor_persona=TRIAGE,
            db=str(Path(tmp) / "cc.db"),
            skills_dir=str(Path(tmp) / "skills"),
            out_dir=str(Path(tmp) / "dist"),
        )
        click.echo("══ CC.construct_language('triage') — minted a new cognition-language ══")
        click.echo(f"  AC  → {bundle.ac.parent.name}/SKILL.md   (how to think)")
        click.echo(f"  CoR → {bundle.cor.parent.name}/SKILL.md   (spoken reasoning → decision)")
        click.echo(f"  SC  → {bundle.sc.parent.name}/SKILL.md   (chains AC + CoR)")
        click.echo(f"\n  default sequence: {bundle.sequence}")
        click.echo("\n  ── the SC rollup (publishable, auto-loadable by any agent) ──")
        head = bundle.sc.read_text().splitlines()
        click.echo("\n".join("  " + ln for ln in head[:14]))
        click.echo("\n  A new domain language, pre-powered with AC + CoR by default. "
                   "That is the bandit's 'construct-chain-language' move.")


@main.command()
@click.argument("prompt_file", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--out", "out_dir", default="dist", type=click.Path(path_type=Path),
              help="output dir for the compiled <cogid>/ skill")
def persona(prompt_file: Path, out_dir: Path) -> None:
    """Compile a glyph-persona-program (e.g. BizziBee) → <cogid>/SKILL.md + legend.json.

    Parses the three layers — [VarDefs] legend, ⚙️ workflow, [ROLE] wrapper — into the
    artifacts the rest of ChainCompiler eats. Gates a legend chain via rulecatcher.
    """
    from .persona import compile_persona
    res = compile_persona(prompt_file.read_text(encoding="utf-8"), out_dir)
    click.echo(f"══ compiled persona '{res['name']}' ══")
    click.echo(f"  legend : {res['axes']} glyph axes → {res['legend']}")
    click.echo(f"  workflow: {res['steps']} ⚙️ steps")
    click.echo(f"  skill  : {res['skill']}")
    if res["gate"]:
        click.echo(f"  gate   : chain {res['gate']['chain']} → {res['gate']['verdict']} (rulecatcher)")


if __name__ == "__main__":
    main()
