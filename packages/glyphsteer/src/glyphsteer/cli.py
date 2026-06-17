"""GlyphSteer CLI — annotate / index / search / probe."""
from __future__ import annotations

import json
import sys

import click

from .annotate import RuleAnnotator
from .encode import Chunk, annotate_chunk, indexed_form, returned_form
from .index import build_index, search
from .vocab import SENTIMENT


def _load_chunks(path: str) -> list[Chunk]:
    """JSONL of {id, text} → chunks."""
    out = []
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if line:
            d = json.loads(line)
            out.append(Chunk(d["id"], d["text"], d.get("code", ""), d.get("meta", {})))
    return out


@click.group()
def main() -> None:
    """GlyphSteer — dual-regime retrieval steering via glyph annotations."""


@main.command()
@click.argument("corpus")
@click.option("--keyword", "-k", multiple=True, metavar="GLYPH=word,word",
              help="keyword rule, e.g. -k 😊=great,love")
def annotate(corpus: str, keyword: tuple[str, ...]) -> None:
    """Annotate a JSONL corpus with the sentiment vocabulary (keyword rules)."""
    kw: dict[str, list[str]] = {}
    for spec in keyword:
        g, _, words = spec.partition("=")
        kw[g] = [w for w in words.split(",") if w]
    ann = RuleAnnotator.keyword(SENTIMENT, kw) if kw else RuleAnnotator(SENTIMENT, {})
    for c in _load_chunks(corpus):
        ac = annotate_chunk(c, ann, SENTIMENT)
        click.echo(json.dumps({"id": ac.id, "text": ac.text, "code": ac.code,
                               "indexed": indexed_form(ac),
                               "returned": returned_form(ac, SENTIMENT)},
                              ensure_ascii=False))


@main.command()
@click.argument("corpus")
@click.argument("query")
@click.option("--facet", "-f", default=None, help="glyph to facet on")
def query(corpus: str, query: str, facet: str | None) -> None:
    """Index an (already-annotated) JSONL corpus and search it; returns CLEAN text."""
    con = build_index(_load_chunks(corpus))
    for h in search(con, query, facet=facet):
        click.echo(json.dumps(h, ensure_ascii=False))


@main.command()
def vocab() -> None:
    """Print the built-in sentiment vocabulary."""
    for a in SENTIMENT.axes:
        click.echo(f"{a.glyph}  {a.name:10s}  {a.description}")


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
