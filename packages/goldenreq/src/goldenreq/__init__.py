"""goldenreq — the ACCEPTANCE GATE for goldenization.

THE LAW (gauge ≠ handler). A *gauge* is an internal self-assessment: the
bandit's 2×🏆 on a chain, a rulecatcher candidate, a forged template, a
personapack grade claim. A gauge may detect quality but it may NEVER certify
itself. Promotion to golden/adopted/canon happens only through a *handler* — an
external acceptance authority. This package is that gate.

  - `queue.file_request(...)` — a gauge FILES a request carrying its receipts
    (evidence). That is the only move a gauge gets. The request sits pending.
  - `verdict.accept / verdict.reject` — a handler rules. Only `accept` fires the
    promotion effect (`effects.dispatch`). `reject` carries a reason.

Requests carry receipts; verdicts are the seed corpus for the learned acceptance
model that will one day staff this gate; rejections (with reasons) are its hard
negatives. The verdict record mirrors base/acceptance's `Verdict` schema so the
corpus is drop-in for that reader (field mapping: see `verdict.py`).
"""
from __future__ import annotations

__version__ = "0.3.0"

from .queue import KINDS, file_request, list_pending, get_request
from .verdict import accept, reject, list_verdicts
from . import effects

__all__ = [
    "KINDS", "file_request", "list_pending", "get_request",
    "accept", "reject", "list_verdicts", "effects", "__version__",
]
