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


@main.group()
def gba() -> None:
    """General BanditAgent — a persistent AIOS dir an agent goes to and BECOMES."""


@gba.command("new")
@click.argument("domain")
@click.argument("root", type=click.Path(path_type=Path))
@click.option("--atom", "-a", "atoms", multiple=True, required=True,
              help="an attention chain, e.g. -a '[Symptom] ⇒ [Scope] ⇒ |Severity|'")
def gba_new(domain: str, root: Path, atoms: tuple[str, ...]) -> None:
    """Emit a persistent GBA AIOS at ROOT (CLAUDE.md + live tree + index + kb)."""
    from .gba import make_gba
    g = make_gba(domain, root, atoms=list(atoms))
    click.echo(f"══ GBA '{domain}' → {g.root} ══")
    click.echo(f"  closed={g.closed}  ·  {g.report['indexed_skills']} skills indexed  ·  persona: CLAUDE.md")
    click.echo(f"  become it: cd {g.root} and run an agent there.")


@gba.command("construct")
@click.argument("root", type=click.Path(exists=True, path_type=Path))
@click.argument("name")
@click.argument("atoms", nargs=-1, required=True)
def gba_construct(root: Path, name: str, atoms: tuple[str, ...]) -> None:
    """Mint a new chain system NAME into the GBA at ROOT (persists into the tree + re-indexes)."""
    from .gba import load_gba, construct_into
    g = load_gba(root)
    sysd = construct_into(g, name, list(atoms))
    click.echo(f"constructed '{name}' → {sysd.sc.parent.name}  ({g.report['indexed_skills']} skills now)")


@gba.command("search")
@click.argument("root", type=click.Path(exists=True, path_type=Path))
@click.argument("query")
@click.option("--scope", "scope_coord", default=None,
              help="restrict to a coordinate subtree, e.g. --scope 0.1 (where you are = what you see)")
@click.option("--newest", "newest_only", is_flag=True, default=False,
              help="forward only the newest version per logical skill (the self-expansion routing)")
def gba_search(root: Path, query: str, scope_coord: str | None, newest_only: bool) -> None:
    """Select's search half: BM25 over the GBA's live tree, optionally scoped + newest-version-routed."""
    from .gba import load_gba, search
    g = load_gba(root)
    hits = search(g, query, scope_coord=scope_coord, newest_only=newest_only)
    if not hits:
        click.echo("  (no hits)")
    for h in hits:
        click.echo(f"  [{h.get('coord','') or '–'}] {h['name']:28s} — {h.get('description','')}")


@gba.command("hba")
@click.argument("domain")
@click.argument("root", type=click.Path(path_type=Path))
@click.option("--atom", "-a", "atoms", multiple=True, required=True,
              help="an attention chain for the HBA's tree")
def gba_hba(domain: str, root: Path, atoms: tuple[str, ...]) -> None:
    """Emit an HBA AIOS at ROOT: a GBA + select/construct seat subagents + the dispatch protocol."""
    from .hba import make_hba
    h = make_hba(domain, root, atoms=list(atoms))
    click.echo(f"══ HBA '{domain}' → {h.root} ══")
    click.echo(f"  seats (subagents): {', '.join(p.name for p in sorted(h.agents_dir.glob('*.md')))}")
    click.echo(f"  dispatch protocol: .claude/rules/01-hba-dispatch.md  ·  base GBA tree + index")


@main.group()
def cog() -> None:
    """COG — a Challenger·Observer·Generator whose three seats are each a GBA."""


@cog.command("new")
@click.argument("domain")
@click.argument("root", type=click.Path(path_type=Path))
@click.option("--atom", "-a", "atoms", multiple=True, required=True,
              help="an attention chain for the Generator seat")
def cog_new(domain: str, root: Path, atoms: tuple[str, ...]) -> None:
    """Emit a COG AIOS at ROOT: the C→G→O flow skill + three role-AIOS seats (C/O/G) + a workspace."""
    from .cog import make_cog
    c = make_cog(domain, root, atoms=list(atoms))
    click.echo(f"══ COG '{domain}' → {c.root}  (flow valid: {c.closed}) ══")
    click.echo(f"  seats: ./C ./G ./O (each an AIOS you go to)  ·  shared: ./workspace")
    click.echo(f"  flow : cat {c.flow.relative_to(c.root) if c.flow else '—'}  (the C→G→O workflow you walk)")


@cog.command("flow")
@click.argument("root", type=click.Path(exists=True, path_type=Path))
def cog_flow(root: Path) -> None:
    """Print the COG's default-workflow flow skill — the C→G→O flow you walk (it's a prompt, not a run)."""
    from .cog import load_cog
    c = load_cog(root)
    if c.flow and c.flow.exists():
        click.echo(c.flow.read_text())
    else:
        click.echo("(no flow skill found — re-run `cog new`)")


if __name__ == "__main__":
    main()
