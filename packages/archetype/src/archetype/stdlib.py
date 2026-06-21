"""The seed pantheon + the default Becoming-cycle (ARCHETYPE-COMPILER.md §4).

The default Becoming-cycle CLOSES into a circle (the "circle of fifths of the psyche"):

    Fool → Seeker → Hero → Guardian → King → Steward → Sage → Witness → Self ↺

Whether that closure is exact or only *tempers* (the circle-of-fifths never closes:
3¹² ≠ 2¹⁹) is the one open seam — see ARCHETYPE-MUSIC-CORRESPONDENCE-MAP.md. This
table just gives the canonical aspects; it does not assert the music correspondence.
"""
from __future__ import annotations

from .model import Seed

# the default cycle (each Becoming points to the next; Self closes back to Fool)
CYCLE = ["Fool", "Seeker", "Hero", "Guardian", "King", "Steward", "Sage", "Witness", "Self"]

PANTHEON: dict[str, Seed] = {
    "Fool":     Seed("Innocent beginner",     "Naive Dupe (folly mistaken for wisdom)",  "Wise Innocent (open, not gullible)",        "Seeker"),
    "Seeker":   Seed("Restless searcher",     "Lost Wanderer (seeking as avoidance)",    "Grounded Seeker (searches without fleeing)", "Hero"),
    "Hero":     Seed("Rescuer / champion",    "Savior-Overlord (courage→domination)",    "Guardian Process (holds courage AND its shadow)", "Guardian"),
    "Guardian": Seed("Boundary maintainer",   "Access Tyrant (care→exclusion)",          "Protocol Steward (guards without gatekeeping)", "King"),
    "King":     Seed("Sovereign ruler",       "Despot (sovereignty→tyranny)",            "Servant-Sovereign (rules in service)",      "Steward"),
    "Steward":  Seed("Caretaker of the order","Frozen Bureaucrat (order→rigidity)",      "Living Constitution (order that adapts)",   "Sage"),
    "Sage":     Seed("Knower / reflector",    "Detached Cynic (wisdom→contempt)",        "Embodied Sage (knows AND acts)",            "Witness"),
    "Witness":  Seed("Pure observer",         "Passive Spectator (witness→abdication)",  "Engaged Witness (sees AND participates)",    "Self"),
    "Self":     Seed("Integrated wholeness",  "Inflated Guru (wholeness→ego)",           "Quiet Self (whole, unclaimed)",             "Fool"),  # closes
    # off-cycle (the Jester thread, §8): Trickster.Self = Jester; Trickster.Shadow = clown.
    "Trickster":Seed("Liberator / sacred fool","Demon Clown (renewal→sabotage)",         "Jester (renewal through disruption)",       "Magician"),
    "Magician": Seed("Transformer",           "Manipulator (power→exploitation)",        "True Magician (transforms in service)",     "Sage"),
}

# a worked substrate instantiation: the "Example World" generation.
CYBERNETIC_CITY: dict[str, Seed] = {
    "Hero":       Seed("Debug Champion",     "Savior-Overlord",      "Guardian Process",    "Gatekeeper"),
    "Gatekeeper": Seed("Boundary Maintainer","Access Tyrant",        "Protocol Steward",    "Lawgiver"),
    "Lawgiver":   Seed("Rule Compiler",      "Frozen Bureaucracy",   "Living Constitution", "Sovereign Kernel"),
}


def seed_for(name: str, world: dict[str, Seed] | None = None) -> Seed | None:
    """Look up a canonical seed (a named world overrides the default pantheon)."""
    if world and name in world:
        return world[name]
    return PANTHEON.get(name)


def next_in_cycle(name: str) -> str:
    """The default Becoming target for `name` (wraps; off-cycle → its seed's becoming)."""
    if name in CYCLE:
        return CYCLE[(CYCLE.index(name) + 1) % len(CYCLE)]
    s = PANTHEON.get(name)
    return s.becoming if s else "Self"
