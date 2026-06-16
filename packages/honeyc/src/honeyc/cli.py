"""HoneyC command-line interface."""
from __future__ import annotations

from pathlib import Path

import click

from .check import check_program
from .emit_cypher import emit_cypher
from .emit_prolog import emit_prolog
from .normalize import normalize
from .parser import parse_path
from .render import render


@click.group()
@click.version_option(message="honeyc %(version)s")
def main() -> None:
    """HoneyC — a compiler for Dense Rune-Chain Notation."""


@main.command()
@click.argument("input", type=click.Path(exists=True, dir_okay=False, path_type=Path))
def parse(input: Path) -> None:
    """Parse a rune-chain into an AST."""
    program = parse_path(input)
    for stmt in program.statements:
        click.echo(repr(stmt))


@main.command()
@click.argument("input", type=click.Path(exists=True, dir_okay=False, path_type=Path))
def norm(input: Path) -> None:
    """Normalize a rune-chain into semantic triples."""
    for s in normalize(parse_path(input)):
        if s.predicate == "mediates":
            click.echo(f"{s.subject} mediates {s.object} target={s.meta['target']}")
        else:
            click.echo(f"{s.subject} {s.predicate} {s.object}")


@main.command()
@click.argument("input", type=click.Path(exists=True, dir_okay=False, path_type=Path))
def prolog(input: Path) -> None:
    """Emit Prolog facts and base rules."""
    click.echo(emit_prolog(normalize(parse_path(input))))


@main.command()
@click.argument("input", type=click.Path(exists=True, dir_okay=False, path_type=Path))
def cypher(input: Path) -> None:
    """Emit Neo4j Cypher MERGE statements."""
    click.echo(emit_cypher(normalize(parse_path(input))))


@main.command(name="render")
@click.argument("input", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--as", "mode", type=click.Choice(["readable", "triples", "prose"]), default="readable")
def render_cmd(input: Path, mode: str) -> None:
    """Render a rune-chain through an adjacent lens."""
    click.echo(render(parse_path(input), mode))


@main.command()
@click.argument("input", type=click.Path(exists=True, dir_okay=False, path_type=Path))
def check(input: Path) -> None:
    """Validate a rune-chain and suggest rewrites."""
    issues = check_program(parse_path(input))
    if not issues:
        click.echo("ok")
        return
    for issue in issues:
        click.echo(f"[{issue.severity}] {issue.message}")
        if issue.suggested_rewrite:
            click.echo(f"  suggested rewrite: {issue.suggested_rewrite}")


if __name__ == "__main__":
    main()
