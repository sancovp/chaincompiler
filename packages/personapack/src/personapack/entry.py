"""entry.py — the PackEntry: one library record wrapping a full PersonaBundle.

personapack is the LIBRARY of `personacc.PersonaBundle`s — full personas
(DESCRIPTION BLOCKS + attention chains + ≥1 CoR that uses them), not bare CoR
specs. A PackEntry pairs a bundle with its gazetteer metadata: the pre-bound
invocation terms that seat it, where the binding came from (provenance), how well
it is evidenced (activation_grade), and where that evidence lives (receipt).
"""
from __future__ import annotations

from dataclasses import dataclass

from personacc import PersonaBundle

# The honest grading ladder. NEVER inflate — a grade is a claim about evidence, and
# the receipt (or its absence) is the audit trail behind the claim.
#   seed                a corcc SEED_PERSONA compiled into a degenerate bundle — a
#                       shipped worked example, no separate experimental receipt.
#   proven-in-forge     minted + closed through a real forge script whose kill-criteria
#                       checks pass (structure proven); no separate LLM-behavior receipt.
#   tested-with-receipt an LLM actually ran seated as this persona and left an
#                       experimental artifact (a GBA + captured findings) as evidence.
GRADES: tuple[str, ...] = ("tested-with-receipt", "proven-in-forge", "seed")


@dataclass(frozen=True)
class PackEntry:
    """A single library record."""
    bundle: PersonaBundle                # the full persona (blocks + ACs + ≥1 CoR)
    invocation_terms: tuple[str, ...]    # the pre-bound handles that seat this attractor
    embedded_ac_notes: str               # what chain each term activates (the gazetteer body)
    provenance: str                      # which tradition / source bound the terms
    activation_grade: str                # one of GRADES — honest, never inflated
    receipt: str                         # path/description of experimental evidence, or ""
    domain: str                          # the domain the persona is a ChainSelector for

    def __post_init__(self) -> None:
        if self.activation_grade not in GRADES:
            raise ValueError(
                f"activation_grade {self.activation_grade!r} not in {GRADES}")

    @property
    def name(self) -> str:
        return self.bundle.name
