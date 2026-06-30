"""CC — ChainCompiler. The top: construct a whole cognition-language for a domain.

The headline move (the bandit's first chain — "construct-chain-language"): given a
domain, mint its **AC** (how to think), its **CoR** (spoken reasoning → decision),
and an **SC** that chains them — a new domain language pre-powered with AC + CoR
by default. Every piece is a SKILL.md package; nothing here judges content.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import accc
import corcc
import sccc
from corcc.notation import PersonaSpec


@dataclass
class LanguageBundle:
    domain: str
    ac: Path           # <skills>/<domain>-attention/SKILL.md
    cor: Path          # <skills>/<persona>/SKILL.md
    sc: Path           # <out>/<domain>/SKILL.md  (chains ac + cor)
    sequence: str


def construct_language(
    domain: str,
    *,
    ac_chain: str,
    cor_persona: PersonaSpec | None = None,
    db: str,
    skills_dir: str,
    out_dir: str,
    sequence: str | None = None,
) -> LanguageBundle:
    """Mint a domain's AC + CoR + SC. Returns the three SKILL.md package paths.

    `cor_persona` defaults to `corcc.BANDIT` — the ChainSelector. A flavored
    persona (Einstein/Feynman) is a single constructed chain; the default is the
    selector that decides exploit (reuse a chain) vs explore (construct one)."""
    cor_persona = cor_persona or corcc.BANDIT
    ac_name = f"{domain}-attention"
    accc.forge(ac_name, [ac_chain], db=db)
    ac = accc.package(ac_name, ac_chain, out_dir=skills_dir)

    persona = corcc.forge_persona(cor_persona, db=db)
    cor = corcc.package(persona, out_dir=skills_dir)

    seq = sequence or f"[ac:{ac.parent.name}] ⇒ [cor:{cor.parent.name}] ⇒ |{domain.capitalize()}|"
    sccc.forge(domain, [seq], db=db)
    sc = sccc.package(domain, seq, out_dir=out_dir, skills_dir=skills_dir)
    return LanguageBundle(domain=domain, ac=ac, cor=cor, sc=sc, sequence=seq)
