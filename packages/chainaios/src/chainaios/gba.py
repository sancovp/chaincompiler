"""gba.py — the General BanditAgent as a PERSISTENT native-CC AIOS (DESIGN.md §3, §10 stage 1).

A GBA is a directory an agent *goes to and becomes*:

    <root>/
      CLAUDE.md                         the persona + the BanditChain loop (Select→exec|construct)
      .claude/skills/<domain>/SKILL.md   the LIVE SkillTree root (auto-loads; cat down to leaves)
      .claude/skills/.../                the gated AC/CoR/SC bodies, organized as cat-breadcrumbs
      kb/                                its own knowledge base (the reward record)
      .index.db                          the FTS5 search index (DERIVED, rebuildable)
      gba.json                           the tree manifest (so construct can re-materialize)

The minted gated bodies live in a sibling scratch (`.<name>.src/`, outside the indexed root) and are
referenced by `skill_src`, so `build_index` sees the tree and only the tree. The PERSISTENT artifact is
the AIOS dir; nothing is written to `/tmp`. `construct_into` mints a new chain, appends it to the tree,
re-materializes, and re-indexes — the Bandit's *construct* arm made to persist (DESIGN.md §7 spine).
"""
from __future__ import annotations

import json
import shutil
from dataclasses import dataclass, field
from pathlib import Path

from skilltree import SkillTree, TreeNode, materialize, validate, build_index, search as _tree_search

from .bandit import roll_up_algebra, domain_bandit
from chaincompiler import skill_markdown, slugify   # the CC base

# the repo skill that teaches the loop (installed into every GBA so it's loadable)
_BCS_SKILL = Path(__file__).resolve().parents[4] / ".claude" / "skills" / "bandit-chain-system" / "SKILL.md"


@dataclass
class GBA:
    """A persistent General BanditAgent AIOS directory."""
    domain: str
    root: Path
    closed: bool
    report: dict = field(default_factory=dict)

    @property
    def claude_md(self) -> Path: return self.root / "CLAUDE.md"
    @property
    def skills_root(self) -> Path: return self.root / ".claude" / "skills"
    @property
    def rules_dir(self) -> Path: return self.root / ".claude" / "rules"
    @property
    def index_db(self) -> Path: return self.root / ".index.db"
    @property
    def manifest(self) -> Path: return self.root / "gba.json"
    @property
    def kb(self) -> Path: return self.root / "kb"


# ── the CLAUDE.md = ONE role block (the domain invariant = the persona) ──────
def _role_block(domain: str, bandit_name: str) -> str:
    """The main role block: who the agent IS in this domain. The domain invariant.
    Everything else (the loop, the law, the KB protocol) is a rule block (see below),
    appended into the CLAUDE.md by Claude Code from `.claude/rules/`."""
    return "\n".join([
        f"# {bandit_name}",
        "",
        f"You are the **{bandit_name}**, the base agent of this directory: the **ChainSelector for "
        f"`{domain}`**. Given a task in `{domain}` you pick an arm — **select** a proven chain (exploit) "
        f"or **construct** a new one (explore).",
        "",
        "Your loop, your law, and your KB protocol are in your appended rules (`.claude/rules/`); your "
        "chains and the `bandit-chain-system` how-to are your skills (`.claude/skills/`).",
    ])


# ── the rule blocks (equipment): everything that ISN'T the role invariant ────
def _rule_blocks(domain: str, root_node: str) -> dict[str, str]:
    """Rule blocks Claude Code appends to the CLAUDE.md from `.claude/rules/`."""
    return {
        "01-bandit-loop.md": "\n".join([
            "# Rule: your default workflow is the loop flow-skill", "",
            f"Your default workflow is the **`{domain}-loop`** flow skill in your tree — find it "
            f"(`chaincompiler gba search <this-dir> loop`), `cat` it, and walk it "
            "(Task → Recall=Select(search→match) → Decide → Construct|Exec → Reward).",
            "",
            "**Addressing:** every node has a coordinate (`0` → `0.1` → `0.1.1` …). "
            "`gba search <this-dir> \"<q>\" --scope 0.1` searches ONLY `0.1` + its descendants "
            "(*where you are = what you see*); add `--newest` to forward only the latest versions.",
            "**Attention-chain syntax** (for `gba construct`): `[Label] ⇒ [Label] ⇒ |Converge|` — each "
            "`[...]` is a **bare label** (one word/CamelCase, **no colon, no description inside the "
            "brackets**: `[Symptom]` ✓, `[Symptom: latency]` ✗ → parser error). `|...|` is the convergence.",
        ]),
        "02-the-law.md": "\n".join([
            "# Rule: everything is a skill", "",
            "Everything you make is a **skill** (a prompt): a chain (**SC**), an attention frame (**AC**), "
            "or a reasoning frame (**CoR**). Gate it — keep the **form** well-formed (the anti-melt gate) — "
            "fit it into the tree, re-index. **Never judge content; always gate form.**",
        ]),
        "03-kb-reward.md": "\n".join([
            "# Rule: the KB reward record", "",
            "Keep a knowledge base under `kb/`: one note per topic, each headed with a grade "
            "(🏆 ✅ ⚠️ ❌) = the reward. On a new task, surface your best-graded prior chains first "
            "(that is `Recall`). Promote a chain to golden when it earns 🏆 twice; demote ❌ out of Recall.",
        ]),
        "04-self-expansion.md": "\n".join([
            "# Rule: place + expand (never drop a skill flat)", "",
            "Every skill you make is **placed, not dropped**: gate it → place it in the tree with a "
            "coordinate (`chaincompiler gba construct <this-dir> …` does this + re-indexes). **Every dir is "
            "automatically an AIOS** — if the new thing is a domain/role, give it its own AIOS "
            "(`chaincompiler gba new <domain> <dir> -a …`). When you *improve* a skill, bump its `version:` "
            "(keep the old as history); search forwards to the newest (`gba search … --newest`). Full "
            "protocol: the home-level **`adding-a-skill`** skill. This is how the tree self-expands.",
        ]),
    }


def _node_from(d: dict) -> TreeNode:
    return TreeNode(d["name"], d.get("kind", "skill"), description=d.get("description"),
                    skill_src=d.get("skill_src"),
                    children=[_node_from(c) for c in d.get("children", [])])


def _reindex(gba: GBA) -> int:
    """Rebuild the FTS5 index over the WHOLE live tree (materialize spreads child nodes as
    siblings under root, so we rglob root, not just .claude/skills). DERIVED + persisted."""
    if gba.index_db.exists():
        gba.index_db.unlink()
    con = build_index(gba.root, db_path=str(gba.index_db))
    n = con.execute("SELECT count(*) FROM skills").fetchone()[0]
    con.close()
    return n


def _apply_tree(gba: GBA, tree_dict: dict) -> tuple[int, int]:
    """The ONE path for any tree change. `materialize` does `rmtree(root)`, so we preserve the
    sidecars (kb, persona, manifest, the bandit-chain-system skill) across it, then re-index.
    Returns (violations, indexed_skills)."""
    # 1. preserve sidecars that live UNDER root (kb reward-record + .claude/agents seat defs)
    #    across the rmtree. (CLAUDE.md / .claude/rules are regenerated below from the profile.)
    kb_bak = gba.root.parent / f".{gba.root.name}.kbbak"
    if gba.kb.exists():
        if kb_bak.exists():
            shutil.rmtree(kb_bak)
        shutil.copytree(gba.kb, kb_bak)
    agents_bak = gba.root.parent / f".{gba.root.name}.agentsbak"
    agents_dir = gba.root / ".claude" / "agents"
    if agents_dir.exists():
        if agents_bak.exists():
            shutil.rmtree(agents_bak)
        shutil.copytree(agents_dir, agents_bak)

    # 2. materialize the live tree into the AIOS root (nukes + rewrites root).
    #    coords=True ADDRESSES every node (root 0, children 0.1/0.2, …): the coord is baked into the
    #    name/desc, so the index carries it and search can be SCOPED to a subtree — "where you are
    #    determines what you see exposed" (DESIGN.md §6 / the addressing spine).
    materialize(SkillTree(_node_from(tree_dict)), gba.root, coords=True)
    viol = validate(gba.root)
    if agents_bak.exists():                                   # restore seat subagent defs (HBA)
        shutil.copytree(agents_bak, gba.root / ".claude" / "agents", dirs_exist_ok=True)
        shutil.rmtree(agents_bak)

    # 3. restore the sidecars (the manifest carries `domain` + an optional `_profile` — a custom
    #    role block / rule set, e.g. for an HBA — so identity survives every re-materialize)
    gba.manifest.write_text(json.dumps({"domain": gba.domain, **tree_dict}, indent=2))
    prof = tree_dict.get("_profile") or {}
    role = prof.get("role") or _role_block(gba.domain, domain_bandit(gba.domain).name)
    rules = prof.get("rules") or _rule_blocks(gba.domain, tree_dict["name"])
    gba.claude_md.write_text(role)                                          # CLAUDE.md = role block
    gba.rules_dir.mkdir(parents=True, exist_ok=True)                        # equipment: the rule blocks
    for fname, body in rules.items():
        (gba.rules_dir / fname).write_text(body)
    if kb_bak.exists():
        shutil.copytree(kb_bak, gba.kb, dirs_exist_ok=True)
        shutil.rmtree(kb_bak)
    else:
        gba.kb.mkdir(exist_ok=True)
        (gba.kb / "README.md").write_text(
            f"# {gba.domain} KB\n\nReward record. One note per topic, each headed with a grade "
            f"(🏆 ✅ ⚠️ ❌). See ../CLAUDE.md for the loop.\n")
    if _BCS_SKILL.exists():
        dst = gba.skills_root / "bandit-chain-system"
        dst.mkdir(parents=True, exist_ok=True)
        (dst / "SKILL.md").write_text(_BCS_SKILL.read_text())

    # 4. the persisted, rebuildable index
    n = _reindex(gba)
    return len(viol), n


def _persona_role_block(domain: str, persona) -> str:
    """A role block derived from a CUSTOM CoR persona (not the bandit): who you ARE in this
    domain, with the melt-gauge loop (the ordered moves; the last is the held convergence)."""
    moves = " → ".join(m.name for m in persona.moves)
    return "\n".join([
        f"# {persona.name}",
        "",
        f"You are the **{persona.name}**, the base agent of this directory: the compiled "
        f"chain-of-reasoning for `{domain}`. {persona.blurb}.",
        "",
        f"Your reasoning is the melt-gauge **{moves}** — perform the moves in order on every "
        "task (the last move is your held convergence; skipping or scrambling them = the persona "
        "is melting). Your loop, your law, and your KB protocol are in your appended rules "
        "(`.claude/rules/`); your chains and the `bandit-chain-system` how-to are your skills "
        "(`.claude/skills/`).",
    ])


def _node_dict(domain: str, sysd, *, root: bool, persona=None) -> dict:
    """Build a tree manifest node from a rolled-up BanditChainSystem (skill_src = gated bodies).
    `persona` (a custom CoR seat) overrides the default domain bandit for the node's name/blurb."""
    persona = persona or domain_bandit(domain)
    cor = {"name": slugify(persona.name) if root else slugify(f"{domain}-cor"), "kind": "cor",
           "description": persona.blurb, "skill_src": str(sysd.cor.parent),
           "children": [{"name": p.parent.name, "kind": "ac",
                         "description": f"attend ({domain})", "skill_src": str(p.parent)}
                        for p in sysd.ac]}
    if root:
        return {"name": slugify(domain), "kind": "sc",
                "description": f"{domain}: {persona.blurb}", "skill_src": str(sysd.sc.parent),
                "children": [cor]}
    return cor


def _loop_flow(domain: str) -> str:
    """The BanditChain default workflow, as a walkable FLOW-skill (so the agent's skillchain lives IN
    the tree, not only as a rule). Mirrors the COG's flow skill — agent = persona+skills+skillchain+tree."""
    return "\n".join([
        f"This is your **default workflow** for `{domain}` — the BanditChain. Walk it on every task; "
        "it is a flow, not a function.",
        "",
        "1. **Task** — frame what's being asked.",
        "2. **Recall = Select (search → neural-match)** — `chaincompiler gba search <this-dir> \"<query>\"` "
        "(`--scope <coord>` to look only in your region; `--newest` for the latest versions). Read the "
        "hits and intuitively pick the best fit.",
        "3. **Decide** — a fit → **exec** it. Nothing fits → **construct**.",
        "4. **Construct** — `chaincompiler gba construct <this-dir> <name> \"[Focus] ⇒ [Focus] ⇒ |Converge|\"` "
        "(gated + coord-addressed + re-indexed; follow the `adding-a-skill` discipline — place it, AIOS it).",
        "5. **Execute** — run the chosen/built chain.",
        "6. **Reward** — write a graded note to `kb/`. Your KB + tree ARE your policy.",
    ])


# ── make a GBA (the keystone: a persistent AIOS, not /tmp) ───────────────────
def make_gba(domain: str, root: str | Path, *, atoms: list[str], blurb: str = "",
             role_block: str | None = None, rule_blocks: dict | None = None,
             persona=None) -> GBA:
    """Emit a persistent GBA AIOS dir: CLAUDE.md + live SkillTree + persisted index + KB.
    `role_block` / `rule_blocks` override the defaults (e.g. an HBA) and persist as a `_profile`
    in the manifest, so they survive every re-materialize (construct doesn't clobber identity).
    `persona` (a custom `corcc` `PersonaSpec`) seats a real chain-of-reasoning as the GBA's CoR
    instead of the generic domain bandit (the melt-gauge seam, chainaios cc3af4e); when given
    without an explicit `role_block`, the CLAUDE.md role is derived from that persona's moves."""
    root = Path(root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    src = root.parent / f".{root.name}.src"           # gated bodies, OUTSIDE the indexed root
    src.mkdir(parents=True, exist_ok=True)
    if persona is not None and role_block is None:
        role_block = _persona_role_block(domain, persona)

    # CONSTRUCT the closed AC/CoR/SC algebra (gated bodies land in `src`, which persists)
    sysd = roll_up_algebra(domain, atoms, db=str(src / ".cc.db"),
                           skills_dir=str(src / "skills"), out_dir=str(src / "dist"),
                           persona_root=str(src / "personas"), blurb=blurb, persona=persona)
    tree_dict = _node_dict(domain, sysd, root=True, persona=persona)

    # the default workflow, as a flow-skill IN the tree (agent = persona + skills + skillCHAIN + skilltree)
    loop_src = src / "loop"
    loop_src.mkdir(exist_ok=True)
    (loop_src / "SKILL.md").write_text(skill_markdown(
        f"{domain}-loop", f"the {domain} default workflow (BanditChain) — walk it", _loop_flow(domain)))
    tree_dict["children"].append({
        "name": slugify(f"{domain}-loop"), "kind": "sc",
        "description": f"the {domain} default workflow — walk it", "skill_src": str(loop_src)})

    if role_block or rule_blocks:
        tree_dict["_profile"] = {"role": role_block, "rules": rule_blocks}

    gba = GBA(domain=domain, root=root, closed=sysd.closed, report=dict(sysd.report))
    viol, n = _apply_tree(gba, tree_dict)
    gba.report.update({"violations": viol, "indexed_skills": n,
                       "persistent": True, "root": str(root)})
    gba.closed = sysd.closed and viol == 0
    return gba


# ── construct INTO a live GBA (the Bandit's explore arm, persisted) ──────────
def construct_into(gba: GBA, name: str, atoms: list[str], *, blurb: str = "", persona=None):
    """Mint a new AC/CoR/SC chain system, append it to the GBA's tree, re-materialize + re-index.
    The output PERSISTS into the agent's own directory (DESIGN.md §5 step 3–4). Returns the
    BanditChainSystem (so a Challenger can gate its `.report['sequence']`). `persona` seats a
    custom CoR for the constructed subsystem — e.g. a minted character's own reasoning (the
    Aegis `SDNA_Synth` arm: each new character constructed carries its OWN persona, not the bandit)."""
    src = gba.root.parent / f".{gba.root.name}.src"
    sysd = roll_up_algebra(name, atoms, db=str(src / ".cc.db"),
                           skills_dir=str(src / "skills"), out_dir=str(src / "dist"),
                           persona_root=str(src / "personas"), blurb=blurb, persona=persona)
    tree_dict = json.loads(gba.manifest.read_text())
    tree_dict["children"].append(_node_dict(name, sysd, root=False, persona=persona))
    _, n = _apply_tree(gba, tree_dict)
    gba.report["indexed_skills"] = n
    return sysd


def search(gba: GBA, query: str, *, scope_coord: str | None = None, limit: int = 5,
           newest_only: bool = False) -> list[dict]:
    """Select's search half: BM25 over the GBA's live tree (the agent does the neural-match).
    `scope_coord` restricts to a subtree (`0.1` → only `0.1` + descendants) — where you are = what you
    see. `newest_only` forwards only the newest `version` per logical skill — the self-expansion routing."""
    con = build_index(gba.root, db_path=":memory:")
    hits = _tree_search(con, query, scope_coord=scope_coord, limit=limit, newest_only=newest_only)
    con.close()
    return hits


def load_gba(root: str | Path) -> GBA:
    """Re-open an existing GBA from disk (cold) by reading its manifest."""
    root = Path(root).resolve()
    man = json.loads((root / "gba.json").read_text())
    return GBA(domain=man.get("domain", man.get("name", root.name)), root=root, closed=True)
