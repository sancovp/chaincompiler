"""Render a parsed program / its statements into adjacent lenses."""
from __future__ import annotations

from .ast_nodes import (
    Assignment,
    Bounded,
    Chain,
    Entity,
    Glyph,
    Placeholder,
    Program,
    Scope,
    Symbol,
    Transform,
    TypeAnn,
)
from .normalize import Statement, normalize
from .symbols import glyph_name

_CONNECTOR_GLYPH = {
    "equiv": "⇔", "produces": "⇒", "compiles": "⇢",
    "maps": "↦", "arrow": "→", "trans": "⟶", "runtime": "⟼",
}

# markers that don't belong in a human triples view
_TRIPLE_SKIP = {"entity", "symbol", "glyph"}


def _term(t: object) -> str:
    if isinstance(t, (Chain, Assignment)):
        return _readable_node(t)
    if isinstance(t, Entity):
        return f"[{t.id}]"
    if isinstance(t, Symbol):
        return t.name
    if isinstance(t, Glyph):
        return f"[{t.id}: {t.name}]" if t.name else t.id
    if isinstance(t, Placeholder):
        return "📃"
    if isinstance(t, TypeAnn):
        inner = t.term
        if isinstance(inner, Entity):
            return f"[{inner.id}: {t.type_name}]"
        if isinstance(inner, Glyph):
            label = f"{inner.id}: {inner.name}" if inner.name else inner.id
            return f"[{label}: {t.type_name}]"
        return f"{_term(inner)}: {t.type_name}"
    if isinstance(t, Bounded):
        return f"|{_strip_brackets(_term(t.term))}|"
    if isinstance(t, Scope):
        body = ", ".join(_term(c) for c in t.body)
        if isinstance(t.owner, Symbol) and t.owner.name == "_group":
            return f"{{ {body} }}"
        return f"{_term(t.owner)}:{{ {body} }}"
    if isinstance(t, Transform):
        return "${" + _readable_node(t.chain) + "}"
    return str(t)


def _strip_brackets(text: str) -> str:
    return text[1:-1] if text.startswith("[") and text.endswith("]") else text


def _connector(kind: str, value: str, reverse: bool = False) -> str:
    if kind == "rel":
        return f"<{value}-" if reverse else f"-{value}->"
    if kind == "rel:bi":
        return f"<{value}>"
    return _CONNECTOR_GLYPH.get(kind, value)


def _readable_node(node: object) -> str:
    if isinstance(node, Chain):
        out = [_term(node.terms[0])] if node.terms else []
        for i, c in enumerate(node.connectors):
            if i + 1 < len(node.terms):
                out.append(_connector(c.kind, c.value, getattr(c, "reverse", False)))
                out.append(_term(node.terms[i + 1]))
        return " ".join(out)
    if isinstance(node, Assignment):
        return f"{_term(node.left)} := {_term(node.right)}"
    return _term(node)


def render_readable(program: Program) -> str:
    return "\n".join(_readable_node(s) for s in program.statements)


def render_triples(statements: list[Statement]) -> str:
    lines = []
    for s in statements:
        if s.predicate in _TRIPLE_SKIP:
            continue
        if s.predicate == "mediates" and "target" in s.meta:
            lines.append(f"{s.subject} mediates {s.object} target={s.meta['target']}")
        else:
            lines.append(f"{s.subject} {s.predicate} {s.object}")
    return "\n".join(lines)


def render_prose(statements: list[Statement]) -> str:
    types: dict[str, str] = {}
    is_a: dict[str, str] = {}
    bounded: set[str] = set()
    mediations: list[tuple[str, str, str]] = []
    for s in statements:
        if s.predicate == "has_type":
            types[s.subject] = s.object
        elif s.predicate == "is_a":
            is_a[s.subject] = s.object
        elif s.predicate == "bounded":
            bounded.add(s.subject)
        elif s.predicate == "mediates" and "target" in s.meta:
            mediations.append((s.subject, s.object, s.meta["target"]))

    sentences: list[str] = []
    for subj, typ in types.items():
        sent = f"{subj} is an entity of type {typ}."
        if subj in is_a:
            level = glyph_name(is_a[subj]) or is_a[subj]
            sent += f" It is treated as a {level}-level object."
        sentences.append(sent)
    for x, a, b in mediations:
        name = glyph_name(x) or x
        word = "bounded into a stable mediator object" if x in bounded else "an (unbounded) mediator"
        sentences.append(f"{name} is {word} that links {a} to {b}.")
    return " ".join(sentences)


def render(program: Program, mode: str) -> str:
    if mode == "readable":
        return render_readable(program)
    statements = normalize(program)
    if mode == "triples":
        return render_triples(statements)
    if mode == "prose":
        return render_prose(statements)
    raise ValueError(f"unknown render mode: {mode!r}")
