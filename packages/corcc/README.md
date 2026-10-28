# corcc — the chain-of-reasoning compiler

`corcc` is one of the three chain compilers of [ChainCompiler](https://github.com/sancovp/chaincompiler), a
compiler-compiler for cognition. It compiles **chains of reasoning** (CoRs). A CoR is spoken: one paragraph that performs
ordered moves and ends in a decision. A `PersonaSpec` is those moves in order, each `Move` carrying the cue phrases that
count as evidence it was performed; the last move is the held convergence.

- `forge_persona(spec, db=…)` forges the move chain as an attention-chain language;
- `lint(persona, cor_text)` gates a spoken CoR against that language. Drift out of the syntax is the persona *melting*,
  which is why the lint is called the melt-gauge;
- `package(persona, out_dir=…)` writes the CoR as `<name>/SKILL.md`, with its paragraph skeleton and its inner attention
  chain; a move recovered without its cue phrases is cued by its own name in the skeleton;
- the seed personas: `BANDIT` (`Task → Recall → Decide → Execute → Reward` — given a task, it exploits a proven chain or
  explores by constructing one; the default CoR everywhere), `EINSTEIN` and `FEYNMAN`.

It is made from the [`chaincompiler`](https://pypi.org/project/chaincompiler/) base and composes
[`chaincompiler-accc`](https://pypi.org/project/chaincompiler-accc/) for its inner attention template;
[`sccc`](https://pypi.org/project/sccc/) chains its CoRs with attention chains and skills.

## Install

```bash
pip install corcc
```

It installs the `corcc` command. To work on it, clone the [repository](https://github.com/sancovp/chaincompiler) and run
`./install.sh`, which installs all fifteen packages editable.

## Use

```python
from corcc import BANDIT, forge_persona, package

persona = forge_persona(BANDIT, db="cor.db")   # the BANDIT: Task → Recall → Decide → Execute → Reward
print(package(persona, out_dir="skills"))     # skills/banditchain/SKILL.md
```

## Its design

The repository's [`DESIGN.md`](https://github.com/sancovp/chaincompiler/blob/main/DESIGN.md) §5.

## License

MIT.
