"""The Steward — the Custodian genus, lowest rung (non-graph realization).

A **Custodian** is "a loop-runner gated by a warrant" (CCC DESIGN.md §2.1). It has two
sibling realizations: the **Cybernet** (game-being animated by an LLM through the graph,
gated by `required_pattern`) and the **Steward** (headless automation/worker, gated by a
proto-SOMA placement gate). This module builds the **Steward** — the simpler sibling — in
ChainCompiler, off the graph. (Next: the same thing implemented INTO CCC as Cybernets.)

A Steward runs the **O/F/I/A/P** cognition loop and produces **the one type** (a skill-dir
artifact). The **A-stage IS the LOCK** — the warrant-freeze that admits (crystallizes) or
rejects the produced artifact. That lock is the whole point: a Custodian that does not pass
its warrant produces nothing admissible.

Hierarchy (built bottom-up): Steward → specialist Stewards (Core/SM/Chain/Compiler) →
MetaSteward (a Steward whose maker calls a sequence of Stewards — reads as one, runs many).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable


# ── the one type ─────────────────────────────────────────────────────────────
@dataclass
class Artifact:
    """The one type a Steward produces — a skill-dir spec (name + body + meta).
    `kind` records which part it is (core/sm/chain/compiler/…)."""
    name: str
    kind: str
    body: str = ""
    meta: dict = field(default_factory=dict)


@dataclass
class Task:
    """What to make. `goal` is the intent; `params` parameterizes the maker."""
    goal: str
    params: dict = field(default_factory=dict)


# ── the warrant (the gate; a rung on the proto-SOMA → SOMA ladder) ───────────
@dataclass
class Verdict:
    ok: bool
    reason: str = ""
    detail: dict = field(default_factory=dict)


@dataclass
class Warrant:
    """A gate over an artifact. `tier` places it on the fidelity ladder so the merge
    axis is explicit: 'proto_soma' (regex/shape) → 'grammar' (rulecatcher) → 'soma'."""
    name: str
    check: Callable[[Artifact], Verdict]
    tier: str = "proto_soma"

    def __call__(self, artifact: Artifact) -> Verdict:
        return self.check(artifact)


# ── the result + trace ───────────────────────────────────────────────────────
@dataclass
class StewardResult:
    task: Task
    artifact: Artifact | None
    verdict: Verdict
    admitted: bool
    kill_criterion: str
    trace: list[str] = field(default_factory=list)


# ── the Steward (the O/F/I/A/P loop, gated at A) ────────────────────────────
class Steward:
    """A loop-runner gated by a warrant that produces one kind of artifact.

    `maker(task) -> Artifact` is the I-stage producer (deterministic template, or an
    injected LLM hook — the Steward is headless either way). `warrant` is the A-lock.
    `kill(artifact) -> str` (optional) is the P-stage falsifiable claim.
    """

    def __init__(self, kind: str, warrant: Warrant,
                 maker: Callable[[Task], Artifact],
                 kill: Callable[[Artifact], str] | None = None):
        self.kind = kind
        self.warrant = warrant
        self.maker = maker
        self._kill = kill or (lambda a: f"{a.kind}:{a.name} fails its warrant {self.warrant.name!r}")

    def run(self, task: Task) -> StewardResult:
        trace = [f"O observe: {task.goal!r}", f"F frame: kind={self.kind}"]
        artifact = self.maker(task)                              # I integrate (produce)
        artifact.kind = artifact.kind or self.kind
        trace.append(f"I integrate: produced {artifact.kind}:{artifact.name}")
        verdict = self.warrant(artifact)                         # A authenticity = THE LOCK
        admitted = verdict.ok
        trace.append(f"A lock[{self.warrant.tier}]: "
                     f"{'ADMIT' if admitted else 'REJECT'} — {verdict.reason or 'ok'}")
        kc = self._kill(artifact)                                # P predict (kill-criterion)
        trace.append(f"P predict: {kc}")
        return StewardResult(task, artifact if admitted else None, verdict, admitted, kc, trace)


def crystallize(artifact: Artifact, out_dir) -> "object":
    """Externalize an admitted artifact as a `<name>/SKILL.md` (the A-lock made durable).
    Uses chaincompiler's shared skill-packager; the artifact IS the skill body."""
    from chaincompiler.skillpack import write_skill
    return write_skill(artifact.name, artifact.meta.get("description", f"a {artifact.kind}"),
                       artifact.body, out_dir=out_dir,
                       extra={"kind": artifact.kind, **artifact.meta.get("extra", {})})
