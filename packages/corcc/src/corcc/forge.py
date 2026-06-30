"""CORCC — the CoR Compiler-Compiler. Composes ACCC for the inner template.

A CoR IS A spoken, paragraphical AC that makes a decision. Like every *CC, CORCC
is a SYNTAX compiler — it catches the CoR notation's grammar, LINTS it (so the
model never writes malformed CoR), compiles it to a markdown file, and packages
that as `<name>/SKILL.md`. It judges no content.

A forged persona carries one chain notation rendered two ways:
- inner : an attention chain (ACCC) — the silent "how to think" template
- outer : the spoken CoR paragraph that converges on a DECISION

The chain's grammar (forged via ACCC) is what `lint` checks. A clean lint = the
model is writing valid CoR (persona intact); violations = it drifted out of the
syntax (melting).
"""
from __future__ import annotations

from dataclasses import dataclass

from accc import Language as ACLanguage
from accc import attention_block, forge as ac_forge
from accc import gate as ac_gate
from chaincompiler import write_skill   # made FROM CC (CC re-exports APE's write_skill)

from .notation import PersonaSpec
from .paragraph import cor_template, must_say_directive


def cor_chain(spec: PersonaSpec) -> str:
    """The reasoning-move sequence as a Dense Rune-Chain (the shared chain)."""
    foci = " ⇒ ".join(f"[{m.name}]" for m in spec.moves[:-1])
    return f"{foci} ⇒ |{spec.held.name}|"


@dataclass
class Persona:
    spec: PersonaSpec
    inner: ACLanguage      # the attention-chain language (from ACCC); also the lint grammar
    db: str

    @property
    def name(self) -> str:
        return self.spec.name


def forge_persona(spec: PersonaSpec, *, db: str) -> Persona:
    """Mint a persona: forge the chain grammar via ACCC (ACCC → CORCC composition)."""
    inner = ac_forge(spec.name, [cor_chain(spec)], db=db)
    return Persona(spec=spec, inner=inner, db=db)


def inner_template(persona: Persona) -> str:
    """INNER attention chain — a template for a section / thinking. Not spoken."""
    return attention_block(persona.name, cor_chain(persona.spec))


def outer_template(persona: Persona) -> str:
    """OUTER CoR — the spoken paragraph skeleton that converges on a decision."""
    return cor_template(persona.spec)


def lint(persona: Persona, cor_text: str) -> tuple[list, list]:
    """Syntax-lint a CoR written in the persona's chain notation.

    This is the only check CORCC makes: is the CoR well-formed? A clean result
    means the model is still writing valid CoR (persona intact); violations mean
    it drifted out of the custom syntax ("melting"). No content is judged.
    """
    return ac_gate(persona.inner, cor_text)


def package(persona: Persona, *, out_dir: str, description: str | None = None):
    """Compile the CoR to a publishable `<name>/SKILL.md` package."""
    spec = persona.spec
    chain = cor_chain(spec)
    desc = description or (
        f"Chain-of-reasoning (spoken, ends in a decision): {spec.blurb}."
        if spec.blurb else "Chain-of-reasoning: spoken reasoning that ends in a decision."
    )
    body = "\n".join([
        "This is a **chain of reasoning (CoR)** — a SPOKEN, paragraphical reasoning chain "
        "that ends in a DECISION. Say it as a paragraph; keep the moves in order.",
        "",
        "## CoR (custom syntax)",
        "```rune",
        chain,
        "```",
        "",
        "## Say it as a paragraph, in order",
        must_say_directive(spec),
        outer_template(persona),
        "",
        "## Inner attention chain (use silently to generate the above)",
        inner_template(persona),
    ])
    return write_skill(spec.name, desc, body, out_dir=out_dir, extra={"kind": "chain-of-reasoning"})


def prime(persona: Persona) -> str:
    spec = persona.spec
    return "\n".join([
        f'# PRIME — persona "{persona.name}"',
        f"({spec.blurb})" if spec.blurb else "",
        "",
        "## Inner attention chain (use silently; a template for this section / your thinking)",
        inner_template(persona),
        "",
        "## Outer chain-of-reasoning (you MUST say this, as a paragraph ending in a decision)",
        must_say_directive(spec),
        outer_template(persona),
        "",
        "## Syntax",
        "Write the CoR in the chain notation above; it is linted — if it is malformed, "
        "fix it before continuing (a malformed CoR = the persona is melting).",
    ])
