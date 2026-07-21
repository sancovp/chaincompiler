"""Parse Dense Rune-Chain text into AST dataclasses via a Lark transformer."""
from __future__ import annotations

from pathlib import Path

from lark import Lark, Transformer, v_args

from .ast_nodes import (
    Assignment,
    Bounded,
    Chain,
    Connector,
    Entity,
    Glyph,
    Placeholder,
    Program,
    Scope,
    Symbol,
    Transform,
    TypeAnn,
)
from .symbols import glyph_name

_GRAMMAR_PATH = Path(__file__).with_name("grammar.lark")
_CONNECTOR_GLYPHS = {
    "equiv": "⇔",
    "produces": "⇒",
    "compiles": "⇢",
    "maps": "↦",
    "arrow": "→",
    "trans": "⟶",
    "runtime": "⟼",
}


@v_args(inline=True)
class _ToAst(Transformer):
    # --- atoms ---
    def entity(self, name):
        return Entity(str(name))

    def symbol(self, name):
        return Symbol(str(name))

    def glyph(self, token):
        g = str(token)
        return Glyph(g, glyph_name(g))

    def placeholder(self, _token):
        return Placeholder()

    def typed(self, term, type_symbol):
        type_name = type_symbol.name if isinstance(type_symbol, Symbol) else str(type_symbol)
        return TypeAnn(term, type_name)

    def bounded(self, term):
        return Bounded(term)

    def xform(self, inner):
        return Transform(inner)

    # --- connectors (aliased rules) ---
    def equiv(self, _=None):
        return Connector("equiv", _CONNECTOR_GLYPHS["equiv"])

    def produces(self, _=None):
        return Connector("produces", _CONNECTOR_GLYPHS["produces"])

    def compiles(self, _=None):
        return Connector("compiles", _CONNECTOR_GLYPHS["compiles"])

    def maps(self, _=None):
        return Connector("maps", _CONNECTOR_GLYPHS["maps"])

    def arrow(self, _=None):
        return Connector("arrow", _CONNECTOR_GLYPHS["arrow"])

    def trans(self, _=None):
        return Connector("trans", _CONNECTOR_GLYPHS["trans"])

    def runtime(self, _=None):
        return Connector("runtime", _CONNECTOR_GLYPHS["runtime"])

    def rel_fwd(self, token):
        # -name->
        name = str(token)[1:-2]
        return Connector("rel", name)

    def rel_rev(self, token):
        # <name-
        name = str(token)[1:-1]
        return Connector("rel", name, reverse=True)

    def rel_bi(self, token):
        # <name>
        name = str(token)[1:-1]
        return Connector("rel:bi", name)

    # --- composite ---
    @v_args(inline=False)
    def chain(self, children):
        terms = [c for c in children if not isinstance(c, Connector)]
        connectors = [c for c in children if isinstance(c, Connector)]
        return Chain(terms, connectors)

    @v_args(inline=False)
    def scope_body(self, children):
        return list(children)

    def scoped(self, head, body=None):
        return Scope(head, body if body is not None else [])

    def group(self, body=None):
        return Scope(Symbol("_group"), body if body is not None else [])

    def assignment(self, left, right):
        return Assignment(left, right)

    @v_args(inline=False)
    def start(self, children):
        return Program(list(children))


def _build_parser() -> Lark:
    return Lark(_GRAMMAR_PATH.read_text(encoding="utf-8"), parser="earley", maybe_placeholders=False)


_PARSER: Lark | None = None


def get_parser() -> Lark:
    global _PARSER
    if _PARSER is None:
        _PARSER = _build_parser()
    return _PARSER


def parse_text(text: str) -> Program:
    tree = get_parser().parse(text)
    return _ToAst().transform(tree)


def parse_path(path: Path | str) -> Program:
    return parse_text(Path(path).read_text(encoding="utf-8"))
