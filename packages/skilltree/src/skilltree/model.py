"""SkillTree model — a tree of skill dirs wired by LINKS, not nesting.

Every node is a skill dir (`<name>/SKILL.md`) of any type (ac/cor/sc/skill).
Edges are links: each node lives in its OWN `.claude/skills/` root, and a node's
direct children are symlinked into that root. Auto-load reaches a root + its
direct children only — never deeper (a skill dir won't auto-load a nested
`.claude`). To descend, you REDIRECT the active skills root to the child's root.

Because the platform won't traverse this, the tree's integrity is not guaranteed
by the filesystem — it must be validated programmatically (see validate.py).
"""
from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path

KINDS = ("ac", "cor", "sc", "skill")


@dataclass
class TreeNode:
    name: str                       # slug; also the skill dir name
    kind: str = "skill"             # ac | cor | sc | skill
    skill_src: str | None = None    # existing `<name>/SKILL.md` dir to carry as content (else a stub)
    description: str | None = None   # SKILL.md description (so it auto-loads / is searchable)
    children: list["TreeNode"] = field(default_factory=list)

    def walk(self):
        yield self
        for child in self.children:
            yield from child.walk()

    def edges(self):
        for child in self.children:
            yield (self.name, child.name)
            yield from child.edges()


@dataclass
class SkillTree:
    root: TreeNode

    # ---- manifest (source of truth for validation) ----
    def to_manifest(self) -> dict:
        def enc(n: TreeNode) -> dict:
            return {"name": n.name, "kind": n.kind, "skill_src": n.skill_src,
                    "description": n.description, "children": [enc(c) for c in n.children]}
        return {"skilltree": enc(self.root)}

    @staticmethod
    def from_manifest(data: dict) -> "SkillTree":
        def dec(d: dict) -> TreeNode:
            return TreeNode(name=d["name"], kind=d.get("kind", "skill"),
                            skill_src=d.get("skill_src"), description=d.get("description"),
                            children=[dec(c) for c in d.get("children", [])])
        return SkillTree(dec(data["skilltree"]))

    def save(self, path: str | Path) -> Path:
        p = Path(path)
        p.write_text(json.dumps(self.to_manifest(), indent=2), encoding="utf-8")
        return p

    @staticmethod
    def load(path: str | Path) -> "SkillTree":
        return SkillTree.from_manifest(json.loads(Path(path).read_text(encoding="utf-8")))

    def nodes(self) -> list[TreeNode]:
        return list(self.root.walk())

    def edges(self) -> list[tuple[str, str]]:
        return list(self.root.edges())
