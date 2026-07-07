#!/usr/bin/env python3
"""wisdom_world — the abductive world with the consistency-penalty (option B + WISDOM).

The mechanism (from the Isaac×LLM design dialogue):
  - The world is NOT simulated forward. Facts are abduced BACKWARD from sampled
    interactions: a perception that fires WRITES the world-fact that would justify it
    (owl hoots -> dog's hear-roll fires -> "the dog was close enough" closes `near()`).
  - But abduction can confabulate. So the world-DB is a CONSTRAINT STORE: a new fact
    closes only if it is CONSISTENT with the already-closed facts (the consistency |=).
  - When the agent ACTS on a perception the world KNOWS is inconsistent (it "heard" an
    owl that was never there), we do NOT silently reject -- we choose (B): re-narrate the
    truth AND penalize. The penalty is RETURNED FROM THE TOOL, so it re-enters the LLM's
    context as a consequence it reads and conditions on:

        bark() -> "WISDOM -1: You thought you heard an owl. In fact, there was not one
                   when you looked."

  WISDOM is the calibration stat: how well belief (Mode A) tracks the certified world
  (Mode B). Losing WISDOM = acting on an uncertified belief. The gate is skinned as XP.

Dependency-free; runnable: `python3 examples/wisdom_world.py`.
"""
from __future__ import annotations

from dataclasses import dataclass, field


# == the world-DB: the constraint store of CLOSED facts (the only certifier) ==========
class World:
    def __init__(self) -> None:
        self.facts: set[str] = set()      # closed facts, e.g. "owl_hooted@3", "near(dog,owl)"
        self.events: list[str] = []       # the certified trace

    def close(self, fact: str) -> None:   # closing a fact = reifying it on warrant
        self.facts.add(fact)

    def warrants(self, fact: str) -> bool:
        """Does the world KNOW this fact (is it closed)? The Mode-B 'when you looked' check."""
        return fact in self.facts

    def dump(self) -> str:
        return ("WORLD -- closed facts: " + (", ".join(sorted(self.facts)) or "(none)")
                + "\n        trace: " + " | ".join(self.events))


# == the agents: methods reflect themselves into actions; perceptions are soft-RNG =====
@dataclass
class Owl:
    world: World
    name: str = "Great Horned Owl"

    def hoot(self, tick: int) -> str:
        # a method that GOES OFF and interacts with the world: it closes a real fact.
        self.world.close(f"owl_hooted@{tick}")
        self.world.events.append(f"{self.name}.hoot@{tick}")
        return f"{self.name}: HOOOO-HOOOO"


@dataclass
class Dog:
    world: World
    name: str = "Dog"
    wisdom: int = 10

    def bark(self, *, heard_owl_at: int) -> str:
        """The dog barks BECAUSE it believes it heard an owl at tick `heard_owl_at`.

        Abduction: if the belief is WARRANTED (the world has the owl-hoot fact), the
        bark closes `near(dog,owl)` -- the proximity is abduced backward from the
        perception. If the world KNOWS there was no such hoot, the belief is
        inconsistent: choice (B) -- re-narrate the truth, dock WISDOM, return the penalty.
        """
        warrant = f"owl_hooted@{heard_owl_at}"
        if self.world.warrants(warrant):
            # certified: abduce proximity (reify the relation on warrant) and bark for real
            self.world.close("near(dog,owl)")
            self.world.events.append(f"{self.name}.bark (warranted by {warrant}) -> near(dog,owl)")
            return f"{self.name}: WOOF! (heard the owl -- so it was close enough; near(dog,owl) closed)"
        # KNOWN-inconsistent selection: penalize + re-narrate (option B)
        self.wisdom -= 1
        self.world.events.append(f"{self.name}.bark UNWARRANTED -> WISDOM {self.wisdom}")
        return "WISDOM -1: You thought you heard an owl. In fact, there was not one when you looked."


# == the run: both branches, so the gate is visible ===================================
def main() -> None:
    w = World()
    owl, dog = Owl(w), Dog(w)

    print("== TICK 1 -- the owl actually hoots, the dog hears it (WARRANTED) ==")
    print(" ", owl.hoot(tick=1))
    print(" ", dog.bark(heard_owl_at=1))          # warrant exists -> WOOF + near() closes
    print()

    print("== TICK 2 -- the dog 'hears' an owl that never hooted (KNOWN-INCONSISTENT) ==")
    # nothing hooted at tick 2; the agent SELECTED a belief the world does not warrant
    print(" ", dog.bark(heard_owl_at=2))          # no warrant -> WISDOM -1 + re-narration
    print()

    print("== TICK 3 -- it confabulates again; WISDOM keeps dropping ==")
    print(" ", dog.bark(heard_owl_at=3))
    print()

    print(w.dump())
    print(f"\nDog WISDOM = {dog.wisdom}  (started 10; -1 per uncertified belief acted on)")
    print("=> WISDOM is the Mode-A-vs-Mode-B calibration gap, made a stat. The gate is the XP.")

    # the seedling gate: the warranted bark closes near(); the unwarranted ones cost WISDOM
    assert w.warrants("near(dog,owl)"), "warranted bark must abduce proximity"
    assert dog.wisdom == 8, "two uncertified beliefs must cost two WISDOM"
    print("\nself-test OK")


if __name__ == "__main__":
    main()
