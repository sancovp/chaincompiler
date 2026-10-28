# chainaios — the agent tier: agents made out of compiled chains

`chainaios` is the agent tier of [ChainCompiler](https://github.com/sancovp/chaincompiler), a compiler-compiler for
cognition. It builds on the three chain compilers and makes agents out of what they compile:

- `construct_language(domain, ac_chain=…, …)` mints a domain's attention chain, its chain of reasoning (the BANDIT unless
  one is given) and a skill chain over both — three `SKILL.md` packages in one call;
- `roll_up_algebra(domain, atoms, …)` mints a whole chain system — attention chains, a chain of reasoning, the skill-chain
  rollup and a persona folder — and organizes it as a SkillTree that validates; it is *closed* when every artifact is a
  skill and the tree validates with zero violations;
- `make_gba(domain, root, atoms=…)` writes a General BanditAgent: a persistent folder an agent goes to and becomes,
  because Claude Code injects a folder's `CLAUDE.md`, rules and skills when an agent reads into it. It holds a
  coordinate-addressed tree of its gated chains, a knowledge base, a search index and the `bandit-chain-system` skill that
  teaches its loop, which this package ships as its own data;
- `make_hba` makes an agent whose loop dispatches to subagents instead of acting inline, and `make_cog` makes a
  Challenger · Generator · Observer flow of three seats;
- `check_gba(root)` reads an agent's folder again on disk and says whether it is still closed.

It installs the `chaincompiler` command: `chaincompiler layers`, `demo`, `persona`, `gba new|construct|search|check|hba`
and `cog new|flow`.

## Install

```bash
pip install chainaios
```

It brings [`chaincompiler`](https://pypi.org/project/chaincompiler/),
[`chaincompiler-accc`](https://pypi.org/project/chaincompiler-accc/), [`corcc`](https://pypi.org/project/corcc/) and
[`sccc`](https://pypi.org/project/sccc/) at the same release, and `agent-skilltree` from PyPI. The extra `legend` adds
[`glyphsteer`](https://pypi.org/project/glyphsteer/), with which `roll_up_algebra` writes each persona's grade legend:
`pip install "chainaios[legend]"`. To work on it, clone the [repository](https://github.com/sancovp/chaincompiler) and run
`./install.sh`, which installs all fifteen packages editable.

## Use

```python
import chainaios
from corcc.notation import EINSTEIN

bundle = chainaios.construct_language(
    "triage",
    ac_chain="[Symptom] ⇒ [Scope] ⇒ |Severity|",
    cor_persona=EINSTEIN,
    db=".cc.db", skills_dir="skills", out_dir="dist",
)
print(bundle.ac, bundle.cor, bundle.sc, sep="\n")
# skills/triage-attention/SKILL.md
# skills/thinklikeeinstein/SKILL.md
# dist/triage/SKILL.md
```

## Its design

The repository's [`DESIGN.md`](https://github.com/sancovp/chaincompiler/blob/main/DESIGN.md) §7 (this tier) and §8 (the
agent shapes: GBA, COG, HBA and the lattice).

## License

MIT.
