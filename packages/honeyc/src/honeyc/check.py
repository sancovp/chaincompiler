"""Validate rune-chains and suggest rewrites."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .ast_nodes import Assignment, Bounded, Chain, Entity, Glyph, Program, Scope, Transform, TypeAnn
from .render import _term


def _bounded_form(term: object) -> str:
    return _term(Bounded(term))


@dataclass
class CheckIssue:
    severity: Literal["info", "warning", "error"]
    message: str
    span: str | None = None
    suggested_rewrite: str | None = None


def _underlying(term: object) -> object:
    return term.term if isinstance(term, TypeAnn) else term


def check_program(program: Program) -> list[CheckIssue]:
    issues: list[CheckIssue] = []
    typed_entities: set[str] = set()
    seen_entities: set[str] = set()

    def visit(node: object) -> None:
        if isinstance(node, Chain):
            _check_chain(node, issues)
            for t in node.terms:
                visit(t)
        elif isinstance(node, Scope):
            visit(node.owner)
            for c in node.body:
                visit(c)
        elif isinstance(node, TypeAnn):
            u = _underlying(node)
            if isinstance(u, Entity):
                typed_entities.add(u.id)
            visit(node.term)
        elif isinstance(node, Bounded):
            visit(node.term)
        elif isinstance(node, Assignment):
            visit(node.left)
            visit(node.right)
        elif isinstance(node, Transform):
            visit(node.chain)
        elif isinstance(node, Entity):
            seen_entities.add(node.id)

    for stmt in program.statements:
        visit(stmt)

    for ent in sorted(seen_entities - typed_entities):
        issues.append(CheckIssue("info", f"entity [{ent}] has no type annotation."))
    return issues


def _check_chain(chain: Chain, issues: list[CheckIssue]) -> None:
    # Walk the equiv/producing backbone; a term sitting between two backbone links
    # that is NOT bounded but acts as a mediator should be flagged.
    cur = 0
    backbone: list[int] = [0]
    for i, c in enumerate(chain.connectors):
        if i + 1 >= len(chain.terms):
            break
        if c.kind in ("equiv", "produces", "compiles", "maps", "arrow", "trans", "runtime"):
            cur = i + 1
            backbone.append(cur)
    for pos, term_index in enumerate(backbone):
        if 0 < pos < len(backbone) - 1:
            term = chain.terms[term_index]
            if not isinstance(term, Bounded):
                rendered = _term(term)
                left = _term(chain.terms[backbone[pos - 1]])
                right = _term(chain.terms[backbone[pos + 1]])
                issues.append(
                    CheckIssue(
                        "warning",
                        f"{rendered} appears as a mediator between {left} and {right} but is not bounded.",
                        span=rendered,
                        suggested_rewrite=f"{left} ⇔ {_bounded_form(term)} ⇔ {right}",
                    )
                )
