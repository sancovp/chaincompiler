"""cog.py — a COG is a FLOW through three role-AIOS directories (DESIGN.md §4, §10).

COG = Challenger · Observer · Generator. It is **not** a function with a return value — it is a flow
you *walk*. Each seat is a DIRECTORY (an AIOS / GBA) you GO TO to learn the role, perform the action,
and leave the artifacts in (or in the shared `workspace/`). The flow itself is a **skillchain** — a
prompt, a skill in the COG's tree — that the agent reads and travels:

    cd C/  (Challenger) → mint the AC/CoR the work needs → place them in G's tree
    cd G/  (Generator)  → use those skills to produce, into ./workspace, until the deliverable
    loop C→G until done
    cd O/  (Observer)   → observe; next cycle C starts from O's observations

It is **all prompts**. The Python here only GUARANTEES SHAPE at build time — it gates syntax, places
names/coordinates, validates the tree, makes it searchable. There is no runtime engine: you travel the
dirs and it works via skills + the cat system. (That is why there is no `run_cog`: the agent IS the run.)
"""
from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from pathlib import Path

from skilltree import SkillTree, TreeNode, materialize, validate

from .gba import GBA, make_gba
from .skillpack import skill_markdown, slugify

SEATS = ("C", "O", "G")

# the topology lattice (DESIGN §10 stage 4): each of C/O/G is a GBA or an HBA → 2³ patterns.
PATTERNS: dict[str, set[str]] = {
    "flat":    set(),                 # all GBA
    "G-hba":   {"G"},
    "C-hba":   {"C"},
    "O-hba":   {"O"},
    "CG-hba":  {"C", "G"},
    "CO-hba":  {"C", "O"},
    "OG-hba":  {"O", "G"},
    "all-hba": {"C", "O", "G"},
}


@dataclass
class COG:
    """A COG AIOS: a domain dir whose default workflow is the C→G→O flow, over three role-AIOS seats."""
    domain: str
    root: Path
    C: GBA            # Challenger seat (an AIOS you go to)
    O: GBA            # Observer seat
    G: GBA            # Generator seat
    closed: bool = True

    @property
    def claude_md(self) -> Path: return self.root / "CLAUDE.md"
    @property
    def skills_root(self) -> Path: return self.root / ".claude" / "skills"
    @property
    def rules_dir(self) -> Path: return self.root / ".claude" / "rules"
    @property
    def workspace(self) -> Path: return self.root / "workspace"
    @property
    def flow(self) -> Path | None:
        """The default-workflow skillchain skill (coord-addressed in the COG's tree)."""
        return next(iter(sorted(self.skills_root.glob("*-cog/SKILL.md"))), None)


# ── the COG role (CLAUDE.md) — who you are when you enter the COG dir ────────
def _cog_role(domain: str) -> str:
    return "\n".join([
        f"# {domain.capitalize()}COG",
        "",
        f"You are the **{domain} COG** — a flow through three role-AIOS directories you GO TO:",
        "- **C** — Challenger — `./C/` (go there; become it; mint the AC/CoR the work needs)",
        "- **G** — Generator — `./G/` (go there; become it; use those skills to produce)",
        "- **O** — Observer  — `./O/` (go there; become it; observe; feed the next C)",
        "",
        "Each seat is its own AIOS (its own CLAUDE.md, rules, tree, kb). Artifacts stay in the seat dir "
        "or in the shared `./workspace/`. Your **default workflow is the `*-cog` flow skill** — `cat` it "
        "from `.claude/skills/` and walk it. It is all prompts; you travel the dirs and it works via skills.",
    ])


def _cog_rules(domain: str) -> dict[str, str]:
    return {"01-cog-flow.md": "\n".join([
        "# Rule: the COG is a flow you walk (not a function)", "",
        "Your default workflow is the `*-cog` flow skill in `.claude/skills/`. Walk it: go to `./C`, "
        "become the Challenger, mint the AC/CoR the task needs and PLACE them in `./G`'s tree "
        "(`chaincompiler gba construct ./G …` — gated + coord'd); go to `./G`, become the Generator, USE "
        "those to produce into `./workspace`; loop C→G until the deliverable; go to `./O`, observe — next "
        "cycle's C starts from O's observations. The Python guarantees the shapes; the running is you.",
    ])}


# ── the default-workflow FLOW — a skillchain (a prompt you travel) ──────────
def _cog_flow(domain: str) -> str:
    return "\n".join([
        f"This is the **default workflow for the `{domain}` domain** — a flow, not a function. You don't "
        "call anything; you TRAVEL the three role-directories and perform each role. Everything is a skill; "
        "find them via the cat system + `chaincompiler gba search`.",
        "",
        "## Walk it",
        "",
        "1. **C — Challenger.** `cat ./C/CLAUDE.md` and become it. Frame the task; ask the questions this "
        "work needs. MINT the attention/reasoning frames the Generator will need and PLACE them in G's tree:",
        "   `chaincompiler gba construct ./G <name> \"[Focus] ⇒ [Focus] ⇒ |Converge|\"` (gated + coord-addressed).",
        "2. **G — Generator.** `cat ./G/CLAUDE.md` and become it. USE the frames C just placed to produce, "
        "until the deliverable/state is reached. Put the deliverable in `./workspace/`.",
        "3. **Loop C→G** until finished.",
        "4. **O — Observer.** `cat ./O/CLAUDE.md` and become it. Observe the run; write observations to "
        "`./O/kb/`. Next cycle, C starts from O's observations (its config already adjusted).",
        "",
        "The Python only guaranteed the shapes (syntax gated, names/coords placed, tree validated, "
        "searchable). The running is you — travel the dirs.",
    ])


def _make_seat(seat_domain: str, seat_root: Path, atoms: list[str], hba: bool) -> GBA:
    """A seat is a GBA, or an HBA (whose underlying GBA view the COG holds; the HBA scaffold —
    .claude/agents + the dispatch rule — lives on disk at the seat root for runtime delegation)."""
    if hba:
        from .hba import make_hba
        return make_hba(seat_domain, seat_root, atoms=atoms).gba
    return make_gba(seat_domain, seat_root, atoms=atoms)


def make_cog(domain: str, root: str | Path, *, atoms: list[str],
             seats: set[str] | None = None) -> COG:
    """Emit a COG AIOS: the C→G→O **flow skill** (shape-guaranteed in the tree) + three role-AIOS seats
    (`C/`, `G/`, `O/`) + a shared `workspace/`. No runtime engine — the COG is a flow the agent walks.
    `seats` = which of {'C','O','G'} are HBAs (delegating seats); the rest are GBAs (the variant lattice)."""
    root = Path(root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    hba_seats = set(seats or ())

    # 1. the default-workflow FLOW, written as a skill and SHAPE-GUARANTEED in the COG's tree
    #    (coord-addressed + validated). materialize rmtree's root, so this runs FIRST (root is empty),
    #    then the seat subdirs are added after and survive.
    src = root.parent / f".{root.name}.cogsrc"
    src.mkdir(parents=True, exist_ok=True)
    (src / "SKILL.md").write_text(
        skill_markdown(f"{domain}-cog", f"the {domain} COG — walk the C→G→O flow", _cog_flow(domain)))
    tree = SkillTree(TreeNode(slugify(f"{domain}-cog"), "sc",
                              description=f"the {domain} COG default workflow", skill_src=str(src)))
    materialize(tree, root, coords=True)
    viol = validate(root)                                  # shape guarantee: the flow resolves in the tree
    shutil.rmtree(src, ignore_errors=True)

    # 2. the COG role (CLAUDE.md) + rules + manifest
    root.joinpath("CLAUDE.md").write_text(_cog_role(domain))
    rules = root / ".claude" / "rules"
    rules.mkdir(parents=True, exist_ok=True)
    for fn, body in _cog_rules(domain).items():
        (rules / fn).write_text(body)
    root.joinpath("cog.json").write_text(json.dumps({"domain": domain, "hba_seats": sorted(hba_seats)}))

    # 3. the three role-AIOS dirs (each a GBA or HBA), added AFTER materialize so they persist
    G = _make_seat(f"{domain}-generate", root / "G", atoms, "G" in hba_seats)
    C = _make_seat(f"{domain}-challenge", root / "C", ["[Task] ⇒ [Question] ⇒ |Frame|"], "C" in hba_seats)
    O = _make_seat(f"{domain}-observe", root / "O", ["[Run] ⇒ [Result] ⇒ |Observe|"], "O" in hba_seats)

    # 4. the shared workspace (where the deliverable accumulates across C→G cycles)
    (root / "workspace").mkdir(exist_ok=True)

    return COG(domain=domain, root=root, C=C, O=O, G=G, closed=(len(viol) == 0))


def load_cog(root: str | Path) -> COG:
    """Re-open an existing COG from disk (cold)."""
    from .gba import load_gba
    root = Path(root).resolve()
    domain = json.loads((root / "cog.json").read_text()).get("domain", root.name)
    return COG(domain=domain, root=root, C=load_gba(root / "C"), O=load_gba(root / "O"),
               G=load_gba(root / "G"))
