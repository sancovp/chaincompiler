"""accc — forge attention-chain languages, gate them, compile them to blocks."""
from __future__ import annotations

from pathlib import Path
import tempfile

import click

from .forge import forge, gate, grammar, prime
from .notation import SEED_LANGUAGES


@click.group()
@click.version_option(message="accc %(version)s")
def main() -> None:
    """Attention-Chain Compiler-Compiler."""


@main.command()
@click.argument("name")
@click.argument("examples_file", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--db", default=".accc.db")
@click.option("--strict/--shape-only", default=False, help="Pin focus vocabulary (strict) or shape only.")
def forge_cmd(name: str, examples_file: Path, db: str, strict: bool) -> None:
    """Forge an AC language NAME from EXAMPLES_FILE (one chain per line)."""
    examples = [ln for ln in examples_file.read_text(encoding="utf-8").splitlines() if ln.strip()]
    lang = forge(name, examples, db=db, strict=strict)
    click.echo(f"forged '{lang.name}' (scope {lang.scope}, {lang.rule_count} rules):")
    for line in grammar(lang):
        click.echo("  " + line)


main.add_command(forge_cmd, name="forge")


@main.command()
def demo() -> None:
    """Forge two distinct AC languages, gate them, and emit a prime block."""
    with tempfile.TemporaryDirectory() as tmp:
        db = str(Path(tmp) / "accc.db")

        click.echo("══ 1. FORGE — mint a generic AC language (shape only) ══")
        generic = forge("generic", SEED_LANGUAGES["generic"], db=db)
        for line in grammar(generic):
            click.echo("  " + line)

        click.echo("\n══ 2. FORGE — mint a DEBUG AC language (strict: pins the vocabulary) ══")
        debug = forge("debug", SEED_LANGUAGES["debug"], db=db, strict=True)
        click.echo(f"  debug language scope={debug.scope}, {debug.rule_count} rules "
                   "(distinct from generic — domain-specific attention)")

        click.echo("\n══ 3. PRIME — the re-injectable attention block for the debug language ══")
        click.echo(prime(debug, "[Symptom] ⇒ [Logs] ⇒ [Hypothesis] ⇒ |Localize|"))

        click.echo("\n══ 4. GATE — a valid debug AC (should pass) ══")
        good = "[Symptom] ⇒ [Repro] ⇒ [Diff] ⇒ |Localize|"
        v, _ = gate(debug, good)
        click.echo(f"  {good}\n    → {'clean ✓' if not v else 'REJECTED'}")

        click.echo("\n══ 5. GATE — an off-domain AC (planning foci in the debug language) ══")
        wrong = "[Goal] ⇒ [Constraints] ⇒ [Evidence] ⇒ |Plan|"
        v, fixes = gate(debug, wrong)
        if v:
            vio, fx = v[0], fixes[0]
            click.echo(f"  {wrong}\n    ✗ {vio.verdict}: expected {vio.expected_token!r}, "
                       f"found {vio.found_token!r}; fix: {list(fx.candidate_tokens) or fx.reason}")
        else:
            click.echo("  (clean — shape matched; strict vocab not violated)")

        click.echo("\n══ 6. The CC point ══")
        click.echo("  Two attention-chain LANGUAGES were minted from examples — not hand-written. "
                   "CORCC will embed a forged AC inside each reasoning step.")


if __name__ == "__main__":
    main()
