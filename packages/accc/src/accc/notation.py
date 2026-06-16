"""The Attention-Chain notation + seed corpora.

An ATTENTION CHAIN (AC) is the atom of the cognition stack: a prompt block that
sequences attention foci and converges on a held focus. It is what powers ONE
reasoning step (a CoR step embeds an AC). Written in Dense Rune-Chain so HoneyC
compiles it and rulecatcher catches its grammar:

    [Focus_1] ⇒ [Focus_2] ⇒ ... ⇒ |Held|

- each [Focus_i] is something to attend to, in order
- ⇒ flows attention forward
- |Held| (bounded) is the convergence point attention is stabilized on

Different domains forge different AC languages: the SHAPE is shared, the focus
vocabulary and the held target differ. That is what makes ACCC a
compiler-compiler — it mints AC *languages*, not just compiles one AC.
"""
from __future__ import annotations

# Generic planning attention chain: orient → converge on a plan.
GENERIC_AC = [
    "[Goal] ⇒ [Constraints] ⇒ [Evidence] ⇒ |Plan|",
    "[Goal] ⇒ [Risks] ⇒ [Evidence] ⇒ |Plan|",
    "[Goal] ⇒ [Constraints] ⇒ [Options] ⇒ |Plan|",
]

# Domain-specific AC: debugging. Different vocabulary, different held target.
DEBUG_AC = [
    "[Symptom] ⇒ [Repro] ⇒ [Hypothesis] ⇒ |Localize|",
    "[Symptom] ⇒ [Logs] ⇒ [Hypothesis] ⇒ |Localize|",
    "[Symptom] ⇒ [Repro] ⇒ [Diff] ⇒ |Localize|",
]

# Another domain: literature research.
RESEARCH_AC = [
    "[Question] ⇒ [Sources] ⇒ [Claims] ⇒ |Synthesis|",
    "[Question] ⇒ [Sources] ⇒ [Conflicts] ⇒ |Synthesis|",
    "[Question] ⇒ [Gaps] ⇒ [Claims] ⇒ |Synthesis|",
]

SEED_LANGUAGES = {
    "generic": GENERIC_AC,
    "debug": DEBUG_AC,
    "research": RESEARCH_AC,
}
