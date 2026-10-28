# chaincompiler-si — the self-interpreter, and the MCP server the ChainCompiler plugin runs

`chaincompiler-si` (import `si`) is the self-interpreter of [ChainCompiler](https://github.com/sancovp/chaincompiler), a
compiler-compiler for cognition. It runs ChainCompiler's chain dialect, which is Python with ChainCompiler's operations
injected as names — `forge_ac`, `forge_cor`, `forge_sc`, `construct_language`, `SkillTree`, `materialize`, `walk`,
`build_exchange`, `tree_to_mcp` and the rest — so an agent can drive the whole stack in one program.

- `interpret(source)` runs a program in that dialect and returns its value;
- `walk` and `reachable` traverse a materialized skill tree by its breadcrumbs, and `read_skill` finds a skill by name
  anywhere in a tree;
- `tree_to_mcp` turns a tree into an MCP server launcher, and `scaffold_repo` stamps a federated node repository from a
  tree;
- `si.server` is the MCP server the ChainCompiler plugin registers, with the tools `si_interpret`, `si_walk`,
  `si_reachable`, `si_read_skill`, `si_tree_to_mcp` and `si_search`, run by the console command `si-server`.

**`si_interpret` executes arbitrary Python with the permissions of the process running the server.** It is an execution
surface: run only programs you trust.

## Install

```bash
pip install chaincompiler-si
```

It brings [`chainaios`](https://pypi.org/project/chainaios/) and the chain compilers at the same release, and
`agent-skilltree` and `fastmcp` from PyPI. To run the server without installing anything into your own Python, run it
through uv, the way the ChainCompiler plugin launches it:

```bash
uvx --from chaincompiler-si si-server
```

To work on it, clone the [repository](https://github.com/sancovp/chaincompiler) and run `./install.sh`, which installs all
fifteen packages editable.

## Use

```python
from si import interpret

print(interpret("1 + 1"))                 # 2
print(interpret("forge_ac") is not None)  # True — ChainCompiler's operations are names in the dialect
```

## Its design

The repository's [`DESIGN.md`](https://github.com/sancovp/chaincompiler/blob/main/DESIGN.md) §14 (this package) and §16
(the plugin that launches its server).

## License

MIT.
