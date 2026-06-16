"""DietC command-line interface."""
from __future__ import annotations

from pathlib import Path

import click

from .engine import compile_day
from .load import load_modules, load_profile
from .render import render_prose
from .rune import render_rune, render_rune_block, render_via_honeyc

_day_arg = click.argument("day", type=click.Path(exists=True, dir_okay=False, path_type=Path))
_profile_opt = click.option("--profile", required=True, type=click.Path(exists=True, dir_okay=False, path_type=Path))
_modules_opt = click.option("--modules", type=click.Path(exists=True, dir_okay=False, path_type=Path), default=None)


@click.group()
@click.version_option(message="dietc %(version)s")
def main() -> None:
    """DietC — modular nutrition compiler on HoneyC. Not medical advice."""


@main.command()
@_day_arg
@_profile_opt
@_modules_opt
def compile(day: Path, profile: Path, modules: Path | None) -> None:
    """Compile a day: totals, gaps, caps, and recommended patches."""
    state = compile_day(day, load_profile(profile), load_modules(modules) if modules else None)
    click.echo(f"Day summary: {state.label}")
    click.echo(f"  gaps:    {', '.join(state.gaps) or 'none'}")
    click.echo(f"  caps:    {', '.join(state.caps) or 'none'}")
    click.echo(f"  matrix:  {', '.join(state.matrix_gaps) or 'ok'}")
    click.echo(f"  patches: {', '.join(r.name for r in state.patches) or 'none'}")
    for w in state.warnings:
        click.echo(f"  ! {w}")


@main.command()
@_day_arg
@_profile_opt
def summary(day: Path, profile: Path) -> None:
    """Prose summary of the day (no patch modules required)."""
    state = compile_day(day, load_profile(profile))
    click.echo(render_prose(state))


@main.command()
@_day_arg
@_profile_opt
@_modules_opt
@click.option("--honeyc/--no-honeyc", default=False, help="Pass the rune block through HoneyC.")
def rune(day: Path, profile: Path, modules: Path | None, honeyc: bool) -> None:
    """Render the day as Dense Rune-Chain notation."""
    state = compile_day(day, load_profile(profile), load_modules(modules) if modules else None)
    click.echo(render_rune(state))
    if honeyc:
        out = render_via_honeyc(state)
        click.echo("\n# via HoneyC:\n" + out if out else "\n(HoneyC not available)")


@main.command()
@_day_arg
@_profile_opt
@_modules_opt
def check(day: Path, profile: Path, modules: Path | None) -> None:
    """Show prose + the recommended patches with their reasons."""
    state = compile_day(day, load_profile(profile), load_modules(modules) if modules else None)
    click.echo(render_prose(state))


if __name__ == "__main__":
    main()
