"""Lower the AST into boring, flat semantic statements (triples)."""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
from typing import Any

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

_CONNECTOR_PREDICATE = {
    "equiv": "equiv",
    "produces": "produces",
    "compiles": "compiles_to",
    "maps": "maps_to",
    "arrow": "points_to",
    "trans": "transitions_to",
    "runtime": "runtime_transform",
}


@dataclass
class Statement:
    subject: str
    predicate: str
    object: str
    meta: dict[str, Any] = field(default_factory=dict)

    def key(self) -> tuple:
        return (self.subject, self.predicate, self.object, tuple(sorted(self.meta.items())))


class _Normalizer:
    def __init__(self) -> None:
        self.statements: list[Statement] = []
        self._seen: set[tuple] = set()

    def add(self, subject: str, predicate: str, object_: str, **meta: Any) -> None:
        st = Statement(subject, predicate, object_, dict(meta))
        if st.key() in self._seen:
            return
        self._seen.add(st.key())
        self.statements.append(st)

    # Return the canonical id for a term and emit its intrinsic facts.
    def term_id(self, term: object) -> str:
        if isinstance(term, Entity):
            self.add(term.id, "entity", "true")
            return term.id
        if isinstance(term, Symbol):
            self.add(term.name, "symbol", "true")
            return term.name
        if isinstance(term, Glyph):
            self.add(term.id, "glyph", "true", name=term.name or "")
            return term.id
        if isinstance(term, Placeholder):
            return "📃"
        if isinstance(term, TypeAnn):
            inner = self.term_id(term.term)
            self.add(inner, "has_type", term.type_name)
            return inner
        if isinstance(term, Bounded):
            inner = self.term_id(term.term)
            self.add(inner, "bounded", "true")
            return inner
        if isinstance(term, Scope):
            return self.scope(term)
        if isinstance(term, Transform):
            return self.transform(term)
        return str(term)

    def chain(self, chain: Chain) -> None:
        ids = [self.term_id(t) for t in chain.terms]
        if not ids:
            return
        # Relation connectors (-rel->, <rel-, <rel>) hang their right operand as a
        # LEAF off the current backbone node. Equiv/produces/... advance the backbone.
        cur = 0
        backbone: list[int] = [0]
        for i, connector in enumerate(chain.connectors):
            if i + 1 >= len(ids):
                break
            right = i + 1
            if connector.kind == "rel":
                self.add(ids[cur], connector.value, ids[right])
            elif connector.kind == "rel:bi":
                self.add(ids[cur], connector.value, ids[right])
                self.add(ids[right], connector.value, ids[cur])
            elif connector.kind == "equiv":
                self.add(ids[cur], "equiv", ids[right])
                self.add(ids[right], "equiv", ids[cur])
                cur = right
                backbone.append(right)
            else:
                pred = _CONNECTOR_PREDICATE.get(connector.kind, connector.kind)
                self.add(ids[cur], pred, ids[right])
                cur = right
                backbone.append(right)
        # Bounded mediator: |X| sitting between two backbone neighbours.
        for pos, term_index in enumerate(backbone):
            if 0 < pos < len(backbone) - 1 and isinstance(chain.terms[term_index], Bounded):
                self.add(ids[term_index], "mediates", ids[backbone[pos - 1]], target=ids[backbone[pos + 1]])

    def scope(self, scope: Scope) -> str:
        owner = self.term_id(scope.owner)
        for child in scope.body:
            if isinstance(child, Placeholder):
                self.add(owner, "placeholder", "drilldown")
                continue
            child_id = self.term_id(child) if not isinstance(child, Chain) else None
            if child_id is not None:
                self.add(owner, "contains", child_id)
            else:
                # a chain inside a scope: normalize it and link the head
                self.chain(child)
                if child.terms:
                    self.add(owner, "contains", self.term_id(child.terms[0]))
        return owner

    def transform(self, transform: Transform) -> str:
        inner = transform.chain
        tid = "xf_" + hashlib.sha1(repr(inner).encode("utf-8")).hexdigest()[:8]
        self.add(tid, "transform", "true")
        if isinstance(inner, Chain):
            self.chain(inner)
            if inner.terms:
                self.add(tid, "source", self.term_id(inner.terms[0]))
                self.add(tid, "target", self.term_id(inner.terms[-1]))
            if inner.connectors:
                self.add(tid, "operator", inner.connectors[0].kind)
        else:
            self.add(tid, "source", self.term_id(inner))
        return tid

    def statement(self, node: object) -> None:
        if isinstance(node, Chain):
            self.chain(node)
        elif isinstance(node, Scope):
            self.scope(node)
        elif isinstance(node, Transform):
            self.transform(node)
        elif isinstance(node, Assignment):
            left = self.term_id(node.left)
            right = self.term_id(node.right)
            self.add(left, "assign", right)
        else:
            self.term_id(node)


def normalize(program: Program) -> list[Statement]:
    n = _Normalizer()
    for stmt in program.statements:
        n.statement(stmt)
    return n.statements
