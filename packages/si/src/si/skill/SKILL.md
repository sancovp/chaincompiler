---
name: self-interpreter
description: Run ChainCompiler chain-dialect programs and turn skill trees into MCPs. Use to forge languages, build/walk skill trees, or execute a cognition chain.
---

# Self-Interpreter (SI)

The SI runs the **chain dialect** — a Python dialect whose vocabulary is the
ChainCompiler primitives (`forge_ac`, `forge_cor`, `forge_sc`, `construct_language`,
`SkillTree`, `TreeNode`, `materialize`, `walk`, `build_exchange`, `tree_to_mcp`, …).
It defers to native Python for everything else.

## As an MCP

Start it: `python -m si.server`. Tools:

- `si_interpret(source)` — run a chain-dialect program; returns `repr(result)`.
- `si_walk(root_dir, root_name)` / `si_reachable(...)` — traverse a skill tree.
- `si_read_skill(root_dir, skill)` — fetch a skill body by name.
- `si_tree_to_mcp(root_dir, root_name, out)` — turn a tree/master into its own MCP.

## Example program

```python
tree = SkillTree(TreeNode("root", "sc", children=[TreeNode("a", "ac"), TreeNode("b", "cor")]))
materialize(tree, OUT)
result = reachable(OUT, "root")     # the execute arm: walk the tree
```
