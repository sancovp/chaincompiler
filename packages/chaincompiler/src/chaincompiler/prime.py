"""Build the re-injectable PRIME block — the output that closes the loop.

A prime is a context block that (a) tells the LLM the ratified grammar of the
notation so it generates in-shape, and (b) shows a compiled example so it knows
what the notation MEANS. Re-injecting the prime self-primes the model; every
chain it then emits is gated by the same grammar (bridge.gate).
"""
from __future__ import annotations

from .bridge import compile_chain, grammar_lines


def build_prime(scope: str, adopted_rows: list, example_chain: str) -> str:
    compiled = compile_chain(example_chain)
    g = grammar_lines(adopted_rows)

    sections = [
        f'# PRIME — "{scope}" cognition-chain notation',
        "",
        "You think in this notation. Write cognition chains in the shape below; "
        "every chain you emit is gated against the grammar (fix violations before continuing).",
        "",
        f"## Ratified grammar ({len(g)} rules, learned from examples)",
        *(g or ["(none ratified yet)"]),
        "",
        "## A compiled chain (what one MEANS)",
        f"chain:    {example_chain.strip()}",
        f"readable: {compiled['readable']}",
        "",
        "triples:",
        *(f"  {line}" for line in compiled["triples"].splitlines()),
    ]
    if compiled["prose"].strip():
        sections += ["", "prose:", f"  {compiled['prose']}"]
    sections += [
        "",
        "## Directive",
        "Emit chains of this form. End a reasoning chain with a bounded |Predict| "
        "(the kill-criterion). Stay inside the grammar; the gate will reject drift.",
    ]
    return "\n".join(sections)
