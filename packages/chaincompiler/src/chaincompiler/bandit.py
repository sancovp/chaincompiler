"""bandit.py — the bandit's headline capability.

The default persona (`corcc.BANDIT`, the ChainSelector) does ONE big move: given a
domain, **roll up the AC→CoR→SC algebra and CLOSE it** into a self-contained
*bandit chain system* — a domain-specific persona (an AIOS dir) whose CoR is the
bandit, carrying instructions to (a) build its own KB and (b) walk that KB with
GlyphSteer chains to improve itself.

Then `hierarchicalize` applies the SAME move over everything the bandit is *made
of* (accc · corcc · sccc · glyphsteer · skilltree · si · honeyc ·
rulecatcher) — the homoicon: the bandit views its own composition as a domain and
mints a closed chain system for each part, organized into one granular self-view.

    roll_up_algebra(domain, atoms, ...) -> BanditChainSystem     (closed: bool)
    hierarchicalize(workdir, ...)        -> SelfView             (a tree of systems)

Lazy-loaded from the package root (`chaincompiler.roll_up_algebra`) to avoid the
import cycle (this imports accc/corcc/sccc, which import the engine).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import accc
import corcc
import sccc
from corcc.notation import BANDIT, Move, PersonaSpec

from .skillpack import slugify, write_skill


# ── the domain-specialized bandit (the selector, given a domain flavor) ──────
def domain_bandit(domain: str, blurb: str = "") -> PersonaSpec:
    """The BANDIT (ChainSelector) specialized to a domain. Same explore/exploit
    moves (Task→Recall→Decide→Execute→Reward); the domain rides in the name, the
    blurb, and an added Task cue. A *flavor* is a single proven chain; this is the
    selector itself, pointed at one domain — so it still chooses select-vs-construct."""
    b = blurb or (f"in the {domain} domain: frame the task, recall a proven {domain} "
                  f"chain, choose exploit (select a golden chain) vs explore "
                  f"(construct a new one), execute it, record the reward")
    moves = list(BANDIT.moves)
    moves[0] = Move("Task", BANDIT.moves[0].cues + (f"the {domain} task", f"in {domain}"))
    return PersonaSpec(name=f"{domain.capitalize()}Bandit", moves=tuple(moves), blurb=b)


# ── the two self-improvement instruction blocks the persona carries ──────────
def kb_instructions(domain: str) -> str:
    """How this persona builds its OWN knowledge base (the first self-instruction)."""
    return "\n".join([
        f"## Build your own KB ({domain})",
        "",
        "You maintain a knowledge base under `kb/`. It is yours — grow it as you work:",
        "",
        f"1. **Record** — every time you run a {domain} chain, write what happened to a",
        f"   `kb/<topic>.md` note: the task, the chain you chose (select vs construct),",
        "   the reward, and what you'd do differently. One note per topic; append, don't overwrite.",
        "2. **Tag** — head each note with a `glyphs:` line (a GlyphSteer legend facet, e.g.",
        "   `🏆`/`✅`/`⚠️`/`❌`) recording how well the chain worked. The grade is the reward signal.",
        "3. **Index** — the KB is a corpus; treat each note as a chunk. The legend in",
        "   `legend.json` is the controlled glyph vocabulary you annotate with.",
    ])


def glyphsteer_improve_instructions(domain: str) -> str:
    """How this persona walks its KB with GlyphSteer chains to improve ITSELF."""
    return "\n".join([
        f"## Improve yourself via GlyphSteer chains ({domain})",
        "",
        "Your KB is not static — you read it back through GlyphSteer to get better:",
        "",
        "1. **Annotate** the KB with the legend (`glyphsteer.annotate_chunk`) so each note",
        "   carries its grade facet lexically (the ASCII tag) and densely (the emoji direction).",
        "2. **Steer** retrieval: when a new task arrives, `glyphsteer.search(con, task, facet=🏆)`",
        "   surfaces your *best-graded* prior chains first — that is the `Recall` move made real.",
        "   The markers steer the match and are stripped before you read (the HIDE invariant).",
        "3. **Promote** — when a constructed chain earns 🏆 twice, fold it into a golden chain",
        "   (a new AC/CoR/SC via `roll_up_algebra`). Demote ❌ chains out of `Recall`.",
        "4. **Loop** — this is your reward update: the KB + the legend ARE your bandit policy,",
        "   improved by reading yourself. Re-run after every batch of tasks.",
    ])


@dataclass
class BanditChainSystem:
    """A rolled-up, CLOSED chain system for one domain — the bandit's output type.
    Every field is (a path to) the one type, a skill dir, except `closed`/`report`."""
    domain: str
    ac: list[Path]
    cor: Path
    sc: Path
    persona_dir: Path
    tree_root: Path
    closed: bool
    report: dict = field(default_factory=dict)


def _write_persona_aios(domain: str, persona: PersonaSpec, ac: list[Path], cor: Path,
                        sc: Path, root: Path) -> Path:
    """Write the domain-specific persona as an AIOS dir: CLAUDE.md (the persona) +
    legend.json (the glyph vocab) + kb/ (its own knowledge base) + a skills/ pointer.
    A persona IS a CLAUDE.md inside a dir — not a single SKILL.md."""
    pdir = root / slugify(f"{domain}-bandit-persona")
    pdir.mkdir(parents=True, exist_ok=True)
    (pdir / "kb").mkdir(exist_ok=True)

    # the GlyphSteer legend this persona annotates its KB with (built-in GRADE vocab)
    try:
        from glyphsteer import GRADE
        from glyphsteer.legend import save_legend
        save_legend(GRADE, pdir / "legend.json")
        legend_line = "Legend: `legend.json` (GlyphSteer GRADE vocabulary: 🏆 ✅ ⚠️ ❌)."
    except Exception:  # glyphsteer not installed — the persona still stands
        legend_line = "Legend: install `glyphsteer` to enable the grade vocabulary."

    moves = " → ".join(m.name for m in persona.moves)
    claude_md = "\n".join([
        f"# {persona.name} — a bandit chain system for `{domain}`",
        "",
        f"You are the **{persona.name}**: the ChainSelector ({moves}), specialized to the "
        f"`{domain}` domain. {persona.blurb}.",
        "",
        "## Your closed algebra (the chains you were rolled up from)",
        "",
        "These three skill dirs are your minted, closed AC→CoR→SC algebra:",
        "",
        *[f"- **AC** (how to think): `{p.parent.name}`" for p in ac],
        f"- **CoR** (the bandit, spoken): `{cor.parent.name}`",
        f"- **SC** (the rollup): `{sc.parent.name}`",
        "",
        legend_line,
        "",
        kb_instructions(domain),
        "",
        glyphsteer_improve_instructions(domain),
        "",
        "## The loop",
        "",
        "`Task → Recall (search your KB, 🏆-faceted) → Decide (select golden vs construct new) "
        "→ Execute → Reward (grade it, write the KB note)` — then improve yourself by reading the KB back.",
    ])
    (pdir / "CLAUDE.md").write_text(claude_md)
    (pdir / "kb" / "README.md").write_text(
        f"# {domain} KB\n\nThis persona's knowledge base. One note per topic, each headed "
        f"with a `glyphs:` grade line. See `../CLAUDE.md` for the protocol.\n")
    return pdir


def roll_up_algebra(domain: str, atoms: list[str], *, db: str, skills_dir: str,
                    out_dir: str, blurb: str = "", persona_root: str | None = None,
                    sequence: str | None = None) -> BanditChainSystem:
    """Mint a domain's AC(s) + CoR(bandit) + SC, build its persona AIOS, and CLOSE it.

    `atoms` = one or more attention-chain strings (the inner templates). The CoR is
    the domain-specialized BANDIT (not a flavor — the selector itself). Closure =
    every minted artifact is the one type AND the organizing SkillTree validates.
    """
    from skilltree import SkillTree, TreeNode, materialize, validate

    skills_dir = str(skills_dir)
    # 1. AC(s) — accc forges + packages each atom into a skill dir
    ac_paths: list[Path] = []
    for i, atom in enumerate(atoms):
        name = f"{domain}-attention" if len(atoms) == 1 else f"{domain}-attention-{i+1}"
        accc.forge(name, [atom], db=db)
        ac_paths.append(Path(accc.package(name, atom, out_dir=skills_dir)))

    # 2. CoR — the domain-specialized bandit, forged + packaged
    persona = domain_bandit(domain, blurb)
    forged = corcc.forge_persona(persona, db=db)
    cor = Path(corcc.package(forged, out_dir=skills_dir))

    # 3. SC — roll the AC(s) + the bandit CoR up into one sequence (the closure op)
    seq = sequence or (
        " ⇒ ".join(f"[ac:{p.parent.name}]" for p in ac_paths)
        + f" ⇒ [cor:{cor.parent.name}] ⇒ |{domain.capitalize()}|")
    sccc.forge(domain, [seq], db=db)
    sc = Path(sccc.package(domain, seq, out_dir=out_dir, skills_dir=skills_dir))

    # 4. the domain-specific persona AIOS (CLAUDE.md + legend + KB + glyphsteer self-improve)
    persona_dir = _write_persona_aios(
        domain, persona, ac_paths, cor, sc, Path(persona_root or out_dir))

    # 5. CLOSE — organize into a SkillTree and validate (the algebra closes ⇔ no violations)
    tree = SkillTree(TreeNode(slugify(domain), "sc", description=f"{domain}: {persona.blurb}",
        children=[TreeNode(slugify(persona.name), "cor", description=persona.blurb, children=[
            TreeNode(slugify(p.parent.name), "ac", description=f"attend ({domain})") for p in ac_paths
        ])]))
    tree_root = Path(out_dir) / f"{slugify(domain)}-tree"
    materialize(tree, tree_root)
    violations = validate(tree_root)
    minted_ok = all(p.exists() and p.name == "SKILL.md" for p in [*ac_paths, cor, sc])
    closed = minted_ok and len(violations) == 0

    return BanditChainSystem(
        domain=domain, ac=ac_paths, cor=cor, sc=sc, persona_dir=persona_dir,
        tree_root=tree_root, closed=closed,
        report={"sequence": seq, "minted_ok": minted_ok, "violations": len(violations),
                "moves": [m.name for m in persona.moves]})


# ── the bandit's own composition (what it is MADE OF) ───────────────────────
# Each entry: name -> (what that part IS, [its REAL operations as attention chains]).
# The atoms decompose each component into its actual public moves, so the self-view
# is genuinely granular: root → component → that component's operations.
COMPONENTS: dict[str, tuple[str, list[str]]] = {
    "accc":        ("attention chains — how to think; inner, silent templates", [
                    "[Examples] ⇒ [Grammar] ⇒ |Forge|",
                    "[AC] ⇒ [Grammar] ⇒ |Gate|",
                    "[Language] ⇒ [Foci] ⇒ |Package|"]),
    "corcc":       ("chains of reasoning — spoken, end in a decision", [
                    "[PersonaSpec] ⇒ [InnerAC] ⇒ |ForgePersona|",
                    "[CoRText] ⇒ [Moves] ⇒ |Lint|",
                    "[Persona] ⇒ [Chain] ⇒ |Package|"]),
    "sccc":        ("skill chains — sequence AC+CoR+skills into the closed composite", [
                    "[Sequence] ⇒ [StepRefs] ⇒ |Parse|",
                    "[Steps] ⇒ [Packages] ⇒ |Resolve|",
                    "[Sequence] ⇒ [Rollup] ⇒ |Package|"]),
    "glyphsteer":  ("dual-regime retrieval steering — glyph facets, hidden on return", [
                    "[Chunk] ⇒ [Glyph] ⇒ |Annotate|",
                    "[Chunks] ⇒ [FTS5] ⇒ |Index|",
                    "[Query] ⇒ [Facet] ⇒ |Search|",
                    "[Indexed] ⇒ [Clean] ⇒ |Hide|"]),
    "skilltree":   ("progressive-disclosure tree of skill dirs (cat-breadcrumbs)", [
                    "[Tree] ⇒ [Dirs] ⇒ |Materialize|",
                    "[Root] ⇒ [Breadcrumbs] ⇒ |Validate|",
                    "[Corpus] ⇒ [BM25] ⇒ |Search|"]),
    "si":          ("self-interpreter — walk + execute the tree", [
                    "[Root] ⇒ [Reachable] ⇒ |Walk|",
                    "[Name] ⇒ [SkillMd] ⇒ |Read|",
                    "[Source] ⇒ [Env] ⇒ |Interpret|"]),
    "honeyc":      ("the compiler — a dense-rune chain rendered many ways", [
                    "[Rune] ⇒ [AST] ⇒ |Parse|",
                    "[AST] ⇒ [Statements] ⇒ |Normalize|",
                    "[Statements] ⇒ [Lens] ⇒ |Render|"]),
    "rulecatcher": ("the gate — learn a grammar, lint to ok/orthogonal/syntax_break", [
                    "[Examples] ⇒ [Rules] ⇒ |Learn|",
                    "[Text] ⇒ [Rules] ⇒ |Lint|",
                    "[Violations] ⇒ [Verdict] ⇒ |Classify|"]),
}


@dataclass
class SelfView:
    """The bandit's granular view of itself: a closed chain system per component,
    organized into one master SkillTree."""
    systems: list[BanditChainSystem]
    tree_root: Path
    closed: bool
    report: dict = field(default_factory=dict)


def hierarchicalize(*, workdir: str | Path, components: dict | None = None) -> SelfView:
    """Apply `roll_up_algebra` over everything the bandit is composed of — a closed
    chain system per part — and assemble them into ONE master SkillTree: the bandit's
    more-granular view of itself (the homoicon, the self-application)."""
    from skilltree import SkillTree, TreeNode, materialize, validate

    components = components or COMPONENTS
    work = Path(workdir); work.mkdir(parents=True, exist_ok=True)
    db = str(work / "self.db")
    skills = work / "skills"; skills.mkdir(exist_ok=True)
    dist = work / "dist"; dist.mkdir(exist_ok=True)
    personas = work / "personas"; personas.mkdir(exist_ok=True)

    systems: list[BanditChainSystem] = []
    for name, (blurb, atoms) in components.items():
        systems.append(roll_up_algebra(
            name, atoms, db=db, skills_dir=str(skills), out_dir=str(dist),
            blurb=blurb, persona_root=str(personas)))

    # the master self-view: root "bandit-self" over each component's rolled-up system
    master = SkillTree(TreeNode("bandit-self", "sc",
        description="the bandit's granular view of its own composition", children=[
            TreeNode(slugify(s.domain), "cor", description=components[s.domain][0],
                     children=[TreeNode(slugify(p.parent.name), "ac",
                                        description=f"attend ({s.domain})") for p in s.ac])
            for s in systems]))
    tree_root = work / "bandit-self-tree"
    materialize(master, tree_root)
    violations = validate(tree_root)
    closed = all(s.closed for s in systems) and len(violations) == 0

    return SelfView(systems=systems, tree_root=tree_root, closed=closed,
                    report={"components": list(components), "violations": len(violations),
                            "all_closed": all(s.closed for s in systems)})
