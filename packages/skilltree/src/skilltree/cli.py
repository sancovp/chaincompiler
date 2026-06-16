"""skilltree — build a `cat`-breadcrumb tree of skill dirs from JSON, and validate it."""
from __future__ import annotations

from pathlib import Path
import tempfile

import click

from .materialize import materialize, node_skill_md
from .model import SkillTree, TreeNode
from .validate import validate


@click.group()
@click.version_option(message="skilltree %(version)s")
def main() -> None:
    """SkillTree — a nested tree of skill dirs wired by `cat`-breadcrumbs (validated)."""


@main.command(name="build")
@click.argument("manifest", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.argument("root", type=click.Path(path_type=Path))
def build_cmd(manifest: Path, root: Path) -> None:
    """Materialize a SkillTree from a JSON MANIFEST into ROOT, then validate."""
    tree = SkillTree.load(manifest)
    materialize(tree, root)
    issues = validate(root)
    errors = [v for v in issues if v.severity == "error"]
    click.echo(f"built {len(tree.nodes())} nodes at {root}")
    for v in issues:
        click.echo(f"  {'✗' if v.severity == 'error' else '⚠'} [{v.where}] {v.message}")
    if errors:
        raise SystemExit(f"✗ INVALID — {len(errors)} error(s)")
    click.echo(f"✓ valid — root: cat {node_skill_md(root, tree.root.name)}")


@main.command(name="validate")
@click.argument("root", type=click.Path(exists=True, file_okay=False, path_type=Path))
def validate_cmd(root: Path) -> None:
    """Validate a materialized SkillTree at ROOT."""
    issues = validate(root)
    for v in issues:
        click.echo(f"  {'✗' if v.severity == 'error' else '⚠'} [{v.where}] {v.message}")
    if any(v.severity == "error" for v in issues):
        raise SystemExit("✗ INVALID")
    click.echo("✓ valid — every breadcrumb resolves.")


@main.group()
def exchange() -> None:
    """Many skill trees in one repo, under a master."""


@exchange.command(name="build")
@click.argument("manifest", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.argument("repo", type=click.Path(path_type=Path))
def exchange_build(manifest: Path, repo: Path) -> None:
    """Materialize every member tree + the master from an exchange MANIFEST."""
    from .exchange import build, load_exchange, validate
    ex = load_exchange(manifest)
    master = build(ex, repo)
    issues = validate(repo, ex)
    click.echo(f"built exchange '{ex.name}' — {len(ex.trees)} tree(s) + master at {master}")
    for v in issues:
        click.echo(f"  {'✗' if v.severity == 'error' else '⚠'} [{v.where}] {v.message}")
    if any(v.severity == "error" for v in issues):
        raise SystemExit("✗ INVALID")
    click.echo("✓ valid — master + every member tree resolve.")


@exchange.command(name="validate")
@click.argument("manifest", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.argument("repo", type=click.Path(exists=True, file_okay=False, path_type=Path))
def exchange_validate(manifest: Path, repo: Path) -> None:
    """Validate a built exchange REPO against its MANIFEST."""
    from .exchange import load_exchange, validate
    for v in validate(repo, load_exchange(manifest)):
        click.echo(f"  {'✗' if v.severity == 'error' else '⚠'} [{v.where}] {v.message}")


@main.command()
def demo() -> None:
    """Build a breadcrumb tree, walk it by `cat`, validate, then break a breadcrumb."""
    tree = SkillTree(TreeNode("cc-skill-tree", "sc", description="root of the cognition skill tree", children=[
        TreeNode("debug", "cor", description="how to debug", children=[
            TreeNode("symptom-attn", "ac", description="attend to the symptom"),
        ]),
        TreeNode("explain", "cor", description="how to explain", children=[
            TreeNode("simplify-attn", "ac", description="attend to the simplest form"),
        ]),
    ]))
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "cc_tree_test"
        materialize(tree, root)

        click.echo("══ 1. only the ROOT auto-loads; everything else is reached by `cat` ══")
        rootmd = node_skill_md(root, "cc-skill-tree")
        click.echo(f"  auto-loaded: {rootmd}")
        click.echo("  ── its body (the breadcrumbs) ──")
        click.echo("\n".join("    " + l for l in rootmd.read_text().splitlines() if l.strip()))

        click.echo("\n══ 2. follow a breadcrumb down to a leaf ══")
        debugmd = node_skill_md(root / "debug", "debug")
        leafmd = node_skill_md(root / "debug" / "symptom-attn", "symptom-attn")
        click.echo(f"  cat {debugmd}  → then → cat {leafmd}")

        click.echo("\n══ 3. validate (the harness) ══")
        click.echo(f"  {'✓ valid' if not validate(root) else 'issues:'}")
        for v in validate(root):
            click.echo(f"    {v.severity}: [{v.where}] {v.message}")

        click.echo("\n══ 4. corrupt a breadcrumb (rename a child dir); substrate stays silent ══")
        (root / "debug" / "symptom-attn").rename(root / "debug" / "renamed-away")
        for v in validate(root):
            click.echo(f"    ✗ [{v.where}] {v.message}")


if __name__ == "__main__":
    main()
