"""personapack — the LIBRARY of pre-bound PersonaBundles.

Not a list of characters: a library of full personas (`personacc.PersonaBundle` =
DESCRIPTION BLOCKS + attention chains + ≥1 CoR that uses them), each pre-bound to
handles the LLM's training already learned (like "samaya", "bodhicitta", "grand
slam offer") so seating one activates a whole reasoning bundle at ~zero prompt
cost. Each entry pairs a bundle with its invocation terms, an honest activation
grade, and a receipt.

Usage:
    import personapack
    from chainaios.gba import make_gba
    gba = make_gba("review", "./reviewer", **personapack.seat("samayareviewer"))
"""
from __future__ import annotations

__version__ = "0.3.2"

from .entry import PackEntry, GRADES
from .pack import PACK, get, bundle, by_domain, by_grade, seat

__all__ = ["PackEntry", "GRADES", "PACK", "get", "bundle", "by_domain", "by_grade", "seat"]
