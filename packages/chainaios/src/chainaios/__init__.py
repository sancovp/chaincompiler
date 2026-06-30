"""chainaios — the Bandit AIOS application, ABOVE the cognition-chain stack.

This is the AIOS/orchestration tier that sits ON TOP of ACCC/CORCC/SCCC (it mints a domain's AC + CoR + SC
and rolls them up into persistent BanditChain-system AIOS dirs). It imports the *CC + the CC base; the CC
base and the *CC never import it. (META-APE spec §3 keeps `chaincompiler` the compiler-compiler BASE — the
*CC are made FROM CC; this AIOS app is a separate top layer, extracted out of the CC package so CC no
longer imports the *CC.)

The `chaincompiler` console command lives here (entry `chainaios.cli:main`), so the CLI name is unchanged.
"""
from __future__ import annotations

__version__ = "0.1.0"

from .construct import construct_language, LanguageBundle
from .bandit import (
    domain_bandit, BanditChainSystem, roll_up_algebra, SelfView, hierarchicalize, COMPONENTS,
)
from .gba import GBA, make_gba, construct_into, search, load_gba
from .hba import HBA, make_hba
from .cog import COG, make_cog, load_cog, PATTERNS, SEATS

__all__ = [
    "construct_language", "LanguageBundle",
    "domain_bandit", "BanditChainSystem", "roll_up_algebra", "SelfView", "hierarchicalize", "COMPONENTS",
    "GBA", "make_gba", "construct_into", "search", "load_gba",
    "HBA", "make_hba",
    "COG", "make_cog", "load_cog", "PATTERNS", "SEATS",
    "__version__",
]
