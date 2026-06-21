---
name: skilltree
description: The primary technology — impose a navigable TREE on the flat `.claude/skills` substrate, and keep it COHERENT. Use when you see a `[SKILLTREE]` system-notification warning (the tree decohered — recohere it), when a `.claude/skills` is a flat forest you can't navigate, when you need to view/engineer/assign-coords on a skill tree, or when you must navigate a big tree without loading the pile. Triggers: "tree decoherence", "recohere", "skilltree", "treeify skills", "the tree shape", "flat forest", "bare forest", "cat down the tree".
---

# skilltree — the tree is the primary technology

Anthropic's `.claude/skills` is a **flat forest**: it auto-loads **one layer per dir**, `.claude`
**cannot nest in `.claude`**, and the top can't itself be `.claude`. So the substrate cannot express
depth — every skill screams into context at once (melt), and you pay a "management" tax to fake
structure. **skilltree fixes this by imposing a virtual tree on the flat substrate** (rule 01:
*nothing is a forest; everything is a tree, which contains a forest — `Tree = Root × Forest`*).

The tree is rendered with three levers:
1. **placement** — nested *plain* dirs (path = coordinate `0` → `0.1` → `0.1.1`);
2. **the inert-nested-`.claude` boundary** — only the top layer auto-loads; deeper `.claude/skills`
   are inert until you `cat` them (this is the load-cutter that makes layers, not a dump);
3. **`cat`-breadcrumbs + index summary** — each `SKILL.md` ends with literal `cat <path>` links to
   its children + a "reachable below: …" summary (so a search on a leaf term still finds the branch).

You **load one layer and walk**; you never load the pile. *Position = identity:* `cat` into a branch
and that subtree is your world — you lord over it.

## If you got here from a `[SKILLTREE]` notification (recohere — the fix)

The decoherence cron found the on-disk tree drifted from its coherent shape. **Recohere it:**

```
skilltree cohere <root>          # see exactly what drifted (bare forest / stale breadcrumb / coord drift / stray)
skilltree emit   <root>          # re-cohere IN PLACE: reassign coords + rewrite breadcrumbs (non-destructive)
skilltree emit   <root> --root-forest --name <root-name>   # if it's a BARE FOREST: synthesize a root + relocate leaves
skilltree cohere <root>          # confirm: "✓ coherent" → the notice clears on the next check
```

`<root>` is the dir whose tree drifted (the user level is `~/.claude`). **`emit` can relocate/remove
real skill dirs when tree-ifying a forest** — read the `cohere` report first and be sure of `<root>`.

## Engineer or build a tree

- **Discover reality:** `skilltree discover <root>` prints the tree that is actually on disk.
- **From scratch / a manifest:** construct a `SkillTree(TreeNode(...))` (or a `skilltree.json`) and
  `materialize(tree, root, coords=True)` — or `skilltree build <manifest> <root>`.
- **Assign coords / re-emit breadcrumbs:** `emit` (above). Coords come from the tree shape
  (`assign_coords`: root `0`, child *i* = `parent.i`).
- **Surface to the top:** `link_tree` / `build_forest` symlink a tree's (or a forest's) entry points
  up into `~/.claude/skills` so they auto-load; everything deeper stays behind `cat`.

## Navigate a tree (don't load it — walk it)

- You auto-load **only the root layer**. To go deeper, run the `cat` the `## Descend` block gives you.
- **Search, scoped:** `skilltree search <root> "<query>" --scope 0.1` searches only `0.1` + its
  descendants ("where you are = what you see"). The index summaries make branches findable by any
  descendant's terms.

## The decoherence cron (how the notification got there)

`skilltree watch <root> --interval 300` runs in the background: every ~5 min it re-checks the tree
and rewrites the self-managed `00-system-notifications` rule (`~/.claude/rules`) — "nominal" when
coherent, ERROR/WARN + this fix when not. It is **read-only on the tree**; the fix is yours to run.
Single check: `skilltree notify <root>` (or `watch --once`).
