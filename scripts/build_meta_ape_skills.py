#!/usr/bin/env python3
"""build_meta_ape_skills.py — emit the meta-APE skill set into the chaincompiler PLUGIN (spec §4.4/§6).

meta-APE = each compiler build-function becomes a real SKILL. This assembles the FULL catalog —
  APE_CAPABILITIES (from prompt_engineering)  +  the *CC capabilities (forge AC/CoR/SC, construct a language)
— and emits one `skills/<name>/SKILL.md` per capability via APE's own write_skill (skillpack). "CC makes
everything": every capability skill is a CC/*CC build-function. No heaven anywhere.

    python scripts/build_meta_ape_skills.py            # writes skills/<name>/SKILL.md for each capability
"""
from __future__ import annotations

import sys
from pathlib import Path

from prompt_engineering import Capability, APE_CAPABILITIES, emit_meta_ape

REPO = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO / "skills"


# ── the *CC build-function catalog (made of CC/*CC objects: accc / corcc / sccc / chainaios) ──────────
CC_CAPABILITIES = [
    Capability(
        "forge-attention-chain",
        "ACCC — forge an attention-chain language, gate candidates against it, package it as a SKILL.md.",
        "An attention chain is an INNER 'how to think' template. ACCC is made FROM chaincompiler's forge.\n\n"
        "```python\n"
        "import accc\n"
        "lang = accc.forge('debug', ['[Symptom] ⇒ [Repro] ⇒ |Localize|'], db='cc.db')\n"
        "accc.gate(lang, '[Goal] ⇒ [Repro] ⇒ |Localize|')   # lint a candidate against the language\n"
        "accc.package('debug', '[Symptom] ⇒ [Repro] ⇒ |Localize|', out_dir='skills')  # → <name>/SKILL.md\n"
        "```",
    ),
    Capability(
        "forge-cor",
        "CORCC — forge a chain-of-reasoning persona (NESTS an attention chain); lint + package it.",
        "A CoR is a SPOKEN paragraph that ends in a decision; it nests a forged AC. CORCC is made FROM ACCC.\n\n"
        "```python\n"
        "import corcc\n"
        "from corcc.notation import Move, PersonaSpec\n"
        "spec = PersonaSpec(name='Debugger', moves=(Move('Symptom', ()), Move('Repro', ())), blurb='find the cause')\n"
        "persona = corcc.forge_persona(spec, db='cc.db')\n"
        "corcc.package(persona, out_dir='skills')   # → <name>/SKILL.md (inner AC nested inside)\n"
        "```",
    ),
    Capability(
        "forge-skillchain",
        "SCCC — forge a skill-chain language: resolve [ac|cor|skill] steps to packages and roll them up.",
        "An SC chains forged AC/CoR/skill steps toward a goal. SCCC is made FROM CORCC+ACCC+chaincompiler.\n\n"
        "```python\n"
        "import sccc\n"
        "seq = '[ac:debug] ⇒ [cor:Debugger] ⇒ |ShippedFix|'\n"
        "sccc.forge('ship', [seq], db='cc.db')\n"
        "sccc.package('ship', seq, out_dir='dist', skills_dir='skills')   # → rollup <name>/SKILL.md\n"
        "```",
    ),
    Capability(
        "construct-language",
        "Construct a whole cognition-language for a domain (AC + CoR + SC) in one call (the AIOS top-door).",
        "Mint a domain's attention chain, chain-of-reasoning, and a skill chain that chains them — a new "
        "domain language pre-powered with AC + CoR. Lives in chainaios (ABOVE the *CC).\n\n"
        "```python\n"
        "import chainaios\n"
        "bundle = chainaios.construct_language('triage',\n"
        "    ac_chain='[Symptom] ⇒ [Scope] ⇒ |Severity|',\n"
        "    db='cc.db', skills_dir='skills', out_dir='dist')\n"
        "# bundle.ac / bundle.cor / bundle.sc → three SKILL.md packages\n"
        "```",
    ),
]


def main() -> int:
    catalog = APE_CAPABILITIES + CC_CAPABILITIES
    # flat skill dirs (skills/<name>/SKILL.md) — the plugin layout Claude Code auto-loads.
    rep = emit_meta_ape(SKILLS_DIR, caps=catalog, coordinate=False)
    print(f"══ meta-APE: emitted {len(rep['skills'])} capability skills into {SKILLS_DIR} ══")
    for p in rep["skills"]:
        print("  ", Path(p).parent.name)
    print("\nAPE:", ", ".join(c.name for c in APE_CAPABILITIES))
    print("*CC:", ", ".join(c.name for c in CC_CAPABILITIES))
    return 0


if __name__ == "__main__":
    sys.exit(main())
