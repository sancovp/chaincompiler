"""archetype CLI (§7): compile an archetype and emit its individuation circuit.

    archetype compile Hero --substrate "example world" --depth 4 --emit all
    archetype demo
"""
from __future__ import annotations

import click

from .compile import compile_archetype, compile_chain, compile_world
from .emit import cypher, prolog, readable, to_json, triples
from .stdlib import CYBERNETIC_CITY, CYCLE
from .validate import validate

_LENSES = {"readable": readable, "cypher": cypher, "prolog": prolog, "json": to_json}


@click.group()
def main() -> None:
    """The Archetype Compiler — archetype as state machine."""


@main.command()
@click.argument("name")
@click.option("--substrate", default=None)
@click.option("--domain", default=None)
@click.option("--conflict", default=None)
@click.option("--boundary", default=None)
@click.option("--integration-mode", default=None)
@click.option("--depth", type=int, default=None, help="how many pantheon members to visit in the Odyssey")
@click.option("--emit", "fmt", default="readable",
              type=click.Choice(["readable", "cypher", "prolog", "json", "triples", "all"]))
def compile(name, substrate, domain, conflict, boundary, integration_mode, depth, fmt):
    """Compile an archetype into its full individuation circuit."""
    knobs = {k: v for k, v in {
        "substrate": substrate, "domain": domain, "conflict": conflict,
        "boundary": boundary, "integration_mode": integration_mode}.items() if v}
    a = compile_archetype(name, knobs=knobs, depth=depth)
    viol = validate(a)
    if fmt == "all":
        click.echo(readable(a, CYCLE))
        click.echo("\n── cypher ──\n" + cypher(a))
        click.echo("\n── prolog ──\n" + prolog(a))
    elif fmt == "triples":
        for s, p, o in triples(a):
            click.echo(f"{s} —{p}→ {o}")
    else:
        click.echo(_LENSES[fmt](a, CYCLE) if fmt == "readable" else _LENSES[fmt](a))
    click.echo(f"\n{'✓ valid' if not viol else '✗ ' + '; '.join(viol)}")


@main.command()
def demo() -> None:
    """Compile the Hero, then the Example World world."""
    click.echo("══ Hero — the individuation circuit + Odyssey ══")
    a = compile_archetype("Hero", knobs={"substrate": "founder building autonomous AI"})
    click.echo(readable(a, CYCLE))
    click.echo(f"\nvalid: {not validate(a)}")

    click.echo("\n══ Example World — a compiled world ══")
    world = compile_world(CYBERNETIC_CITY, with_odyssey=False)
    for nm, m in world.items():
        click.echo(f"  {nm}: {m.persona} → ⟂{m.shadow} → ⊕{m.self_} ⇒ {m.becoming}")


if __name__ == "__main__":
    main()
