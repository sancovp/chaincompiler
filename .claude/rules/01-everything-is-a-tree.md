# Rule: nothing is a forest — everything is a tree (which contains a forest)

This is the **first law** of this project. Every other rule and every line of code serves it.
ChainCompiler exists to fix one bug the substrate forces on the whole world: **the disconnected
forest.** So the standing constraint is simple and absolute:

> **A bare forest is never allowed. Every forest must be rooted into a tree, so that every region
> is reachable from every other. `Tree = Root × Forest`; if you make a set, you give it a root.**

## What "forest" means here (the bug)

A **forest** is a set of nodes with **no edges between regions** — a flat list where you cannot
traverse from one part to another. The substrate ships forests *by default*:

- `.claude/skills/` auto-loads **one layer per dir** and **`.claude` cannot nest in `.claude`** — so
  the mechanism literally cannot express depth. Flat by construction.
- conversations are a flat list (no tags ⇒ no edges ⇒ no graph);
- agents cannot call agents (no nesting ⇒ no edges ⇒ forced onto an external runtime).

Each is the same defect. And the cost is always the same: **"management" is the tax you pay for an
un-closed loop.** Groups, pipelines, workspaces — that is all *manual edge-drawing by hand* because
the substrate refused to hold the edges. **Close the loop and the management feature disappears:**
there is nothing to manage, you just traverse. *We do not add management; we delete the need for it.*

## The math (why a tree is the fix, exactly — G1, this is the definition)

```
Tree(a)   = a × Forest(a)      -- a node = one payload + a forest of children
Forest(a) = List( Tree(a) )    -- a forest = a list of trees
```

Mutually recursive. "Inside a tree, more trees" is the second line substituted into the first,
forever. A **forest is legal only as the children of a root** — i.e. only *inside* a tree. A *bare*
forest (no root) is the bug; rooting it (`Forest → Root × Forest`) is the entire fix. "Forest or
tree depending how you set it up" is exactly this: point at the root and it is a tree; drop the root
and look at the children and it is a forest. (Self-similar, yes — call it *fractal* as a picture, but
the load-bearing claim is "recursive datatype," not "fractal.")

## How the tree is imposed on the flat substrate (the three levers)

The tree is **virtual** — rendered onto the one-layer substrate by the materializer:

1. **placement** — nested *plain* dirs (a node must be a plain dir first, *then* carry `.claude`); the
   path **is** the coordinate (`0` → `0.1` → `0.1.1`).
2. **the inert-nested-`.claude` boundary** — only the top layer auto-loads; deeper `.claude/skills`
   are inert until cat'd. *This is the load-cutter that makes layers instead of a flat dump.*
3. **cat-breadcrumbs + index summary** — each `SKILL.md` ends with literal `cat <path>` links to its
   children (descend on demand) and an index summary ("reachable below: …") so a hit on a leaf term
   still finds the branch. (See `20-architecture-flows.md` §3.)

You load **one layer and walk**; you never load the pile. That is the whole technology.

## Position = identity = curation authority (the lording rule)

Because each branch's nested `.claude/skills` is **its own root when you cat into it**, *where you
are determines who you are and what you curate.* Descend into a branch and that subtree is your
world — you lord over it. A branch becomes an actual **lord** when it carries a **`CLAUDE.md`** (a
persona) at that dir; until then the parent lord curates it via `search --scope <coord>`.

**Grow lords on warrant, not eagerly.** A branch gets its own persona **when its subtree is big
enough to deserve a dedicated curator** — never one-persona-per-leaf (that is melt in the other
direction). This is the self-expansion principle (every dir is an AIOS) applied *on warrant*.

## The dev directive (what this forbids and requires)

- **Never ship a bare list/forest.** Any set you create — skills, configs, rules, agents, results,
  records — must be **rooted and traversable**: give it a root node, address its members by
  coordinate, make every region reachable. If you cannot traverse from any region to any other, it
  is a forest and it is wrong.
- **A "forest of trees" at the top is allowed *only if it too has a root*** (a federation walked from
  a root registry — see `20-architecture-flows.md` §5). A rooted forest is a tree; an unrooted one is
  the bug.
- **When you audit the system, the question is: "where is there still a bare forest?"** Find it, root
  it.

## Open debts this law exposes (the audit backlog)

- ⚠️ **This very `.claude/skills/` dir is a flat forest** (7 sibling skills, no root, no coords). The
  dev surface violates its own first law. It must be **treeified** (one root, cat-breadcrumbs, coords)
  — the canonical dogfood.
- ⚠️ **`roll_up_algebra` emits a *single-lord* tree** (root → one CoR → its frames), not a
  *forest-of-lords*. To make "each branch curates its subtree" real, the construct must be able to
  emit **lordable sub-domains** (each a branch with its own `CLAUDE.md` + subtree). This is the
  upstream (`accc`/`corcc`/`sccc`) change that makes the recursion structural, not cosmetic.

## Triggers

- Designing or reviewing **any** collection of things — before you leave it, ask "is this rooted and
  traversable, or did I just make another forest?"
- Auditing the system for the bug this project exists to kill.
- Whenever a "management" feature is tempting — that is the smell of an un-closed loop; close the loop
  instead.
