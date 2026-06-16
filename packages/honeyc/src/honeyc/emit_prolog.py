"""Lower normalized statements into Prolog facts and a few base rules."""
from __future__ import annotations

from .normalize import Statement
from .symbols import to_atom

# Marker predicates that lower to a unary fact `pred(atom).`
_UNARY = {"entity": "entity", "glyph": "glyph", "symbol": "symbol", "transform": "transform"}

_BASE_RULES = """
linked(A, B) :- equiv(A, B).
linked(A, B) :- equiv(A, X), X \\= B, linked(X, B).

bounded_bridge(X, A, B) :-
    bounded(X),
    mediates(X, A, B).

needs_expansion(X) :- placeholder(X, drilldown).
""".strip()


def emit_prolog(statements: list[Statement]) -> str:
    facts: list[str] = []
    for s in statements:
        subj = to_atom(s.subject)
        if s.predicate in _UNARY:
            facts.append(f"{_UNARY[s.predicate]}({subj}).")
        elif s.predicate == "bounded":
            facts.append(f"bounded({subj}).")
        elif s.predicate == "has_type":
            facts.append(f"type({subj}, {to_atom(s.object)}).")
        elif s.predicate == "placeholder":
            facts.append(f"placeholder({subj}, {to_atom(s.object)}).")
        elif s.predicate == "mediates":
            facts.append(f"mediates({subj}, {to_atom(s.object)}, {to_atom(s.meta['target'])}).")
        elif s.predicate == "assign":
            facts.append(f"assign({subj}, {to_atom(s.object)}).")
        else:
            # equiv, produces, compiles_to, maps_to, points_to, is_a, custom rels...
            facts.append(f"{to_atom(s.predicate)}({subj}, {to_atom(s.object)}).")

    # stable de-dup, preserve order
    seen: set[str] = set()
    ordered = [f for f in facts if not (f in seen or seen.add(f))]
    return "\n".join(ordered) + "\n\n% --- base rules ---\n" + _BASE_RULES + "\n"
