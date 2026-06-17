"""Specialist Stewards + the MetaSteward — the specialist layer at the Steward level.

Bottom-up: each specialist Steward concentrates on ONE part-kind (the parts a Cybernet is
made of — Core / SM / Chain / Compiler; CCC DESIGN.md §6). A `MetaSteward` is a Steward
whose maker calls a SEQUENCE of Stewards — it **presents as one** ("done from 1 LLM") but
**runs many** autonomous Stewards. Because a MetaSteward is itself a Steward, meta-Stewards
nest (the homoicon: a Chain is a Link; a Steward-of-Stewards is a Steward).
"""
from __future__ import annotations

from .core import Artifact, Steward, Task, Warrant
from .warrants import non_empty


def _slug(goal: str) -> str:
    return "-".join(goal.lower().split())[:48] or "artifact"


# ── specialist Stewards (each makes one part-kind) ──────────────────────────
def chain_steward(warrant: Warrant | None = None) -> Steward:
    """Makes a Chain: an ordered line of links. params['links'] = [str]."""
    def maker(task: Task) -> Artifact:
        links = task.params.get("links", [])
        return Artifact(_slug(task.goal), "chain", " → ".join(links),
                        meta={"links": links})
    return Steward("chain", warrant or non_empty(), maker)


def sm_steward(warrant: Warrant | None = None) -> Steward:
    """Makes a StateMachine: gated steps. params['steps'] = [{'id','gate'}]."""
    def maker(task: Task) -> Artifact:
        steps = task.params.get("steps", [])
        body = "\n".join(f"{i}. {s['id']}  ⟨gate: {s.get('gate','-')}⟩"
                         for i, s in enumerate(steps))
        return Artifact(_slug(task.goal), "sm", body, meta={"steps": steps})
    return Steward("sm", warrant or non_empty(), maker)


def compiler_steward(warrant: Warrant | None = None) -> Steward:
    """Makes a Compiler: an SM that CALLS other SMs. params['calls'] = [str]."""
    def maker(task: Task) -> Artifact:
        calls = task.params.get("calls", [])
        body = "compiler calls:\n" + "\n".join(f"  → {c}" for c in calls)
        return Artifact(_slug(task.goal), "compiler", body, meta={"calls": calls})
    return Steward("compiler", warrant or non_empty(), maker)


def core_steward(warrant: Warrant | None = None) -> Steward:
    """Makes a Core: the ordered always-on SM sequence (CORE_RUNS). params['sequence']."""
    def maker(task: Task) -> Artifact:
        seq = task.params.get("sequence", [])
        body = "CORE_RUNS:\n" + "\n".join(f"  {i}: {sm}" for i, sm in enumerate(seq))
        return Artifact(_slug(task.goal), "core", body, meta={"sequence": seq})
    return Steward("core", warrant or non_empty(), maker)


# ── the MetaSteward (a Steward that runs a sequence of Stewards) ─────────────
def meta_steward(name: str, stewards: list[Steward],
                 warrant: Warrant | None = None) -> Steward:
    """A Steward whose maker runs `stewards` in sequence, threading each admitted
    artifact's body forward as context. Presents as one artifact (kind='workflow');
    its trace records every sub-Steward. Homoiconic: returns a plain Steward, so it
    nests inside another meta_steward."""
    def maker(task: Task) -> Artifact:
        ctx = dict(task.params)
        parts, admitted_kinds = [], []
        for st in stewards:
            r = st.run(Task(goal=f"{task.goal}::{st.kind}", params=ctx))
            if r.admitted and r.artifact is not None:
                parts.append(f"[{r.artifact.kind}:{r.artifact.name}]\n{r.artifact.body}")
                ctx[r.artifact.kind] = r.artifact.body     # feed forward
                admitted_kinds.append(r.artifact.kind)
        return Artifact(name, "workflow", "\n\n".join(parts),
                        meta={"sub": admitted_kinds, "presents_as": "1 LLM",
                              "ran": len(stewards)})
    return Steward("workflow", warrant or non_empty(), maker)
