"""Glyph names and atom helpers. Keep glyph vocabulary configurable here."""
from __future__ import annotations

import re

# Surface glyph -> human name. The Nectar glyph is a ZWJ sequence (🌸 + ZWJ + 💧).
GLYPH_NAMES: dict[str, str] = {
    "🌸‍💧": "Nectar",
    "🌸💧": "Nectar",
    "🍯": "Honey",
    "🍹": "RoyalJelly",
    "🌼": "Flower",
    "📃": "Drilldown",
}

# Atom names used when lowering to Prolog (must be valid lowercase atoms).
GLYPH_ATOMS: dict[str, str] = {
    "🌸‍💧": "nectar",
    "🌸💧": "nectar",
    "🍯": "honey",
    "🍹": "royal_jelly",
    "🌼": "flower",
    "📃": "drilldown",
}


def glyph_name(glyph: str) -> str | None:
    return GLYPH_NAMES.get(glyph)


def is_known_glyph(text: str) -> bool:
    return text in GLYPH_NAMES


def to_atom(text: str) -> str:
    """Lower a symbol/glyph/id into a safe Prolog atom."""
    if text in GLYPH_ATOMS:
        return GLYPH_ATOMS[text]
    atom = text.replace("*", "star").replace("+", "plus")
    # split camelCase boundaries so M*Boundary -> mstar_boundary
    atom = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", atom)
    atom = atom.lower()
    atom = re.sub(r"[^a-z0-9_]+", "_", atom)
    atom = re.sub(r"_+", "_", atom).strip("_")
    if not atom:
        atom = "x"
    if not re.match(r"[a-z_]", atom[0]):
        atom = "n_" + atom
    return atom
