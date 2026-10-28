# sccc — the skill-chain compiler

`sccc` is the highest of the three chain compilers of [ChainCompiler](https://github.com/sancovp/chaincompiler), a
compiler-compiler for cognition. It compiles **skill chains**: `[ac:x] ⇒ [cor:y] ⇒ [skill:z] ⇒ |Result|`, a sequence of
attention chains, chains of reasoning and ordinary skills, rolled up into one `SKILL.md`.

- `forge(name, sequences, db=…)` forges the sequence grammar (scope `sc:<name>`), and `lint(language, sequence)` gates a
  sequence against it;
- `parse_sequence(sequence)` reads a sequence into its steps and its held result;
- `package(name, sequence, out_dir=…, skills_dir=…)` resolves every step to a skill folder on disk — the skills folder
  it is given first, then `~/.claude/skills` and `~/.claude/plugins` — and refuses to package while any step is missing,
  so a rollup never names a skill that is not there.

The rollup itself is written by [`skillchain-compiler`](https://pypi.org/project/skillchain-compiler/). It is made from the
[`chaincompiler`](https://pypi.org/project/chaincompiler/) base, above
[`chaincompiler-accc`](https://pypi.org/project/chaincompiler-accc/) and [`corcc`](https://pypi.org/project/corcc/).

## Install

```bash
pip install sccc
```

It installs the `sccc` command. To work on it, clone the [repository](https://github.com/sancovp/chaincompiler) and run
`./install.sh`, which installs all fifteen packages editable.

## Use

```python
from sccc import parse_sequence

steps, held = parse_sequence("[ac:triage] ⇒ [cor:bandit] ⇒ [skill:report] ⇒ |Result|")
print([(s.kind, s.ref) for s in steps], held)   # [('ac', 'triage'), ('cor', 'bandit'), ('skill', 'report')] Result
```

## Its design

The repository's [`DESIGN.md`](https://github.com/sancovp/chaincompiler/blob/main/DESIGN.md) §5.

## License

MIT.
