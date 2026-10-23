"""PersonaCC notation — the PersonaBundle: what a persona actually IS.

THE RATIFIED DEFINITION (the author):

    a persona = a specific set of DESCRIPTION BLOCKS
              + a set of ACs (attention chains)
              + at least one CoR that USES them.

PersonaCC is the SYNTAX compiler for that bundle. Its source language is the 2023
SDNA-template block grammar: a persona prompt is a stack of `[KIND] … [/KIND]`
DESCRIPTION BLOCKS (role, description, approach, wrapper, invocation-terms, …)
wrapped around a reasoning core. Here that core is made rigorous: the reasoning
core is one-or-more `corcc.PersonaSpec` CoRs, each grounded in a set of `accc`
attention chains.

Two atoms compose UP into a bundle:
  - `Block`         — one description block. `kind` is a free string; NEW block
                      kinds are legal by design (the template-template rule: the
                      block grammar is extensible, not a closed enum).
  - `PersonaBundle` — the whole persona: blocks + ACs + ≥1 CoR + a blurb.

Note on the type below CORCC's `PersonaSpec`: that type is really the *COR SPEC*
(a half-persona — the spoken reasoning move-chain only). PersonaCC does NOT rename
it; it builds the FULL persona ABOVE it, adding the description blocks and the
attention chains the CoR is meant to use.
"""
from __future__ import annotations

from dataclasses import dataclass

from accc import parse_ac  # accc's REAL chain parser — used for the honest is_chain check
from corcc.notation import PersonaSpec  # NOTE: really the COR SPEC (half-persona). Do not rename.


@dataclass(frozen=True)
class Block:
    """One description block of a persona prompt (an SDNA-template block).

    TYPE ⊥ SYNTAX (the author's law): a block is really a triple — (type-`kind`, `lang`,
    `body` string). The TYPE (what the block IS, e.g. "wrapper") is orthogonal to the
    SYNTAX it is rendered in; the same block type renders differently in different
    chain LANGUAGES (one uses only `⇒`, another `-> * + =` in sequence). The `body`
    string is one RENDER of the canonical typed content in a chosen language.

    - `kind` is a FREE STRING (e.g. "role", "description", "approach", "wrapper",
      "invocation_terms" — or anything new). New kinds are legal by design; the
      block grammar is a template-template, so it never closes over a fixed enum.
    - `lang` names the chain language the `body` is written in. "rune" (the default)
      is the honeyc Dense Rune-Chain that accc parses/gates. Other languages are
      lintable only once a gate is registered for them (`forge.register_lang_gate`).
    - `body` is the block's string (a chain in `lang`, or — soup-grade — prose).
    """
    kind: str
    body: str
    lang: str = "rune"

    def __post_init__(self) -> None:
        if not self.kind or not self.kind.strip():
            raise ValueError("Block.kind must be a non-empty string")

    @property
    def is_chain(self) -> bool:
        """True iff this block's body is a conformant chain IN ITS OWN `lang`.

        Keyed to `lang`:
          - "rune" — HONEST DETECTION via accc's REAL parser (not a regex). accc
            exposes `parse_ac`, which runs the HoneyC parser and raises unless the
            body contains a well-formed attention chain (`[Focus] ⇒ … ⇒ |Held|`).
            That clean parse-check exists, so we use it directly; the
            forge-in-a-throwaway-db fallback is NOT needed and is deliberately not
            used. (Broad `except` because a non-chain body can trip the parser with
            parser-internal errors, not only ValueError.)
          - any OTHER lang — we cannot parse an arbitrary language, so it is a chain
            iff a gate is REGISTERED for that lang (an unknown language is unlintable
            = soup-grade). The gate itself (the melt-gauge) runs later in
            `forge.lint_blocks`.
        """
        if self.lang == "rune":
            try:
                parse_ac(self.body)
                return True
            except Exception:
                return False
        from .forge import LANG_GATES  # lazy: forge imports notation; avoid a cycle
        return self.lang in LANG_GATES

    @property
    def grade(self) -> str:
        """The syntaxification grade of this block:

        - "chain" — the body is real chain syntax in its `lang` (code-grade; melt-gaugeable).
        - "prose" — free natural language / an unlintable language (soup-grade; TOLERATED
          for migration only).

        This is the TOTAL-SYNTAXIFICATION gauge at the block level: every persona block
        should eventually grade "chain" (one notation all the way down); NL is licensed
        only as a component the syntax admits, never as a free-standing block.
        """
        return "chain" if self.is_chain else "prose"


@dataclass(frozen=True)
class PersonaBundle:
    """A persona: DESCRIPTION BLOCKS + ACs + ≥1 CoR that uses them.

    - `name`   : the persona's name (also the SKILL.md slug).
    - `blocks` : the description blocks (may be empty for a degenerate persona
                 whose identity is carried entirely by its CoR — e.g. the seeds).
    - `acs`    : attention-chain strings in the shared Dense-Rune notation
                 (`[Focus] ⇒ [Focus] ⇒ |Held|`), each parseable by `accc`.
    - `cors`   : one or more `corcc.PersonaSpec` CoRs. ≥1 is REQUIRED — a persona
                 with no reasoning core is not a persona.
    - `blurb`  : one-line description.
    """
    name: str
    blocks: tuple[Block, ...]
    acs: tuple[str, ...]
    cors: tuple[PersonaSpec, ...]
    blurb: str = ""

    def __post_init__(self) -> None:
        if not self.cors:
            raise ValueError(
                f"PersonaBundle {self.name!r} needs ≥1 CoR — a persona = description "
                "blocks + ACs + at least one CoR that uses them (the ratified definition)."
            )

    def block_kinds(self) -> tuple[str, ...]:
        return tuple(b.kind for b in self.blocks)
