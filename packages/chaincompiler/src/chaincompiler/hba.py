"""hba.py — the HierarchicalBanditAgent: a GBA whose Select/Construct arms DELEGATE to subagents
(DESIGN.md §3, §10 stage 3). Scaffold approach: chaincompiler EMITS the structure (subagent defs +
the dispatch protocol); a real Claude Code agent does the delegation at runtime via the Agent tool.

Why hierarchy: filling a frame *excellently* needs more domain ACs than fit one window without the
geometry flattening ("melt"). So the **construct-agent** loads that context in ITS OWN window and
returns only the finished skill — the HBA never melts. The HBA is otherwise a GBA (its own tree/kb),
so its identity (role + dispatch rule) is carried as a `_profile` and survives the construct-agent's
runtime persists into the tree.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .gba import GBA, make_gba, _rule_blocks
from .skillpack import slugify


@dataclass
class HBA:
    """A HierarchicalBanditAgent AIOS (a GBA + seat subagent defs)."""
    domain: str
    root: Path
    gba: GBA

    @property
    def claude_md(self) -> Path: return self.root / "CLAUDE.md"
    @property
    def agents_dir(self) -> Path: return self.root / ".claude" / "agents"
    @property
    def rules_dir(self) -> Path: return self.root / ".claude" / "rules"


def _hba_role(domain: str) -> str:
    return "\n".join([
        f"# {domain.capitalize()}HBA",
        "",
        f"You are the **{domain.capitalize()}HBA** — the Hierarchical BanditAgent for `{domain}`. You do "
        f"**not** select or construct inline; you **dispatch to subagents and execute** what they return. "
        f"Your seat subagents are in `.claude/agents/`; your protocol, law, and KB rules are appended from "
        f"`.claude/rules/`; your tree + golden chains are your skills (`.claude/skills/`).",
    ])


def _hba_dispatch_rule(domain: str) -> str:
    return "\n".join([
        "# Rule: the HBA dispatch loop   [HBA → SelectAgent → (ConstructAgent) → HBA execs]", "",
        "1. **Task** — frame what's being asked.",
        "2. **Dispatch SELECT** — call the `select-agent` subagent (the Agent/Task tool) with the task. "
        "It returns `EXEC <skill>` (a golden fit) or `CONSTRUCT <name>: <attention-chain>` (a gap).",
        "3. **If CONSTRUCT** — call the `construct-agent` subagent. It loads the full `" + domain + "` "
        "context in **its own window** (anti-melt) and returns only the finished skill.",
        "4. **Execute** — load the chosen/returned skill and do the work. **Only the HBA executes.**",
        "5. **Reward** — record the graded outcome in `kb/`.",
        "",
        "Why subagents: filling a frame excellently needs more domain ACs than fit one window without "
        "**melt** (a flattened geometry in the ICL). Isolate that work in the `construct-agent`.",
    ])


def _select_agent_def(domain: str, root_node: str) -> str:
    return "\n".join([
        "---",
        "name: select-agent",
        f"description: The Select seat of the {domain} HBA. Searches the tree, neural-matches, and returns "
        f"a DECISION (EXEC <skill> | CONSTRUCT <name>:<chain>). Does NOT execute.",
        "tools: Bash, Read, Grep, Glob",
        "---",
        "",
        f"You are the **Select seat** for `{domain}`. Given a task:",
        "",
        f"1. Search the HBA's tree: `chaincompiler gba search <hba-dir> \"<task>\"`, then `cat` the hits "
        f"(start at `.claude/skills/{root_node}/SKILL.md`).",
        "2. **Neural-match**: judge whether any hit *truly* fits the task — not just keyword overlap.",
        "3. Return ONE line: `EXEC <skill-name>` if a golden chain fits, else "
        "`CONSTRUCT <name>: <attention-chain>` describing the gap to fill.",
        "",
        "Return only the decision. You do not execute and you do not construct.",
    ])


def _construct_agent_def(domain: str) -> str:
    return "\n".join([
        "---",
        "name: construct-agent",
        f"description: The Construct seat of the {domain} HBA. Loads the full {domain} context in its own "
        f"window (anti-melt), rolls up + CLOSES an excellent AC/CoR/SC, returns only the finished skill.",
        "tools: Bash, Read, Write, Grep, Glob",
        "---",
        "",
        f"You are the **Construct seat** for `{domain}`. You work in your **own context** so the HBA never melts.",
        "",
        "1. Load the `bandit-chain-system` skill and read widely across the domain's existing ACs — this "
        "deep context is *why you are isolated*.",
        "2. Roll up + CLOSE a new chain for the gap: "
        "`chaincompiler gba construct <hba-dir> <name> \"<attention-chain>\"` "
        "(it persists into the HBA's tree + re-indexes).",
        "3. Return ONLY the finished skill name + path. Keep your large working context to yourself.",
    ])


def make_hba(domain: str, root: str | Path, *, atoms: list[str]) -> HBA:
    """Emit an HBA AIOS: a GBA base + the select/construct seat subagent defs + the dispatch protocol."""
    root = Path(root).resolve()
    root_node = slugify(domain)

    # HBA identity: the dispatch rule REPLACES the inline bandit-loop; law + KB rules are kept.
    base = _rule_blocks(domain, root_node)
    rules = {"01-hba-dispatch.md": _hba_dispatch_rule(domain),
             "02-the-law.md": base["02-the-law.md"],
             "03-kb-reward.md": base["03-kb-reward.md"]}

    g = make_gba(domain, root, atoms=atoms,
                 role_block=_hba_role(domain), rule_blocks=rules)

    # the seat subagent defs (survive re-materialize: _apply_tree only touches CLAUDE.md/.claude/rules)
    agents = root / ".claude" / "agents"
    agents.mkdir(parents=True, exist_ok=True)
    (agents / "select-agent.md").write_text(_select_agent_def(domain, root_node))
    (agents / "construct-agent.md").write_text(_construct_agent_def(domain))

    return HBA(domain=domain, root=root, gba=g)
