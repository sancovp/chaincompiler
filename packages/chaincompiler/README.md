# chaincompiler — the base the chain compilers are made from

`chaincompiler` is the base package of [ChainCompiler](https://github.com/sancovp/chaincompiler), a compiler-compiler
for cognition. A language model thinks in whatever notation it is given, so the useful machine is not one notation but a
factory for them: ChainCompiler mints a notation from examples, gates text against it so a model cannot malform it, and
compiles it into a skill (`<name>/SKILL.md`) that any agent loads. This package is the part of that factory every
notation shares:

- `forge(kind, name, examples, db=…)` learns a grammar from example chains into a named scope, `<kind>:<name>` — a
  *forged language* — and returns it as a `Language`;
- `gate_language(language, candidate)` lints a candidate chain against that grammar and returns its violations and the
  fixes it suggests, so a model's output is checked against the language it was taught;
- `package_skill(name, body, out_dir=…, description=…)` writes a compiled body as `<name>/SKILL.md`;
- `build_prime(...)` renders the block that teaches a model the grammar and shows it one compiled example, so the model
  writes in shape and the gate catches drift;
- `compile_chain` runs a chain through [`honeyc`](https://pypi.org/project/honeyc/) into its lenses.

The three chain compilers — [`chaincompiler-accc`](https://pypi.org/project/chaincompiler-accc/) (attention chains),
[`corcc`](https://pypi.org/project/corcc/) (chains of reasoning) and [`sccc`](https://pypi.org/project/sccc/) (skill
chains) — are each made from this base by adding only their kind, their parser and their renderer. Every check it makes
is about syntax and structure; it never judges whether a thought is good.

## Install

```bash
pip install chaincompiler
```

It brings [`honeyc`](https://pypi.org/project/honeyc/) and [`rulecatcher`](https://pypi.org/project/rulecatcher/) at the
same release, and `agent-prompt-engineering` and `agent-skilltree` from PyPI. The extra `persona` adds
[`glyphsteer`](https://pypi.org/project/glyphsteer/), which `chaincompiler.persona` (the glyph-persona front end) imports:
`pip install "chaincompiler[persona]"`. The `chaincompiler` command is installed by
[`chainaios`](https://pypi.org/project/chainaios/), the agent tier, not by this package.

To work on it, clone the [repository](https://github.com/sancovp/chaincompiler) and run `./install.sh`, which installs
all fifteen packages editable.

## Use

```python
from chaincompiler import forge, gate_language

lang = forge("ac", "triage", ["[Symptom] ⇒ [Scope] ⇒ |Severity|", "[Repro] ⇒ [Localize] ⇒ |Cause|"], db="cc.db")
violations, suggestions = gate_language(lang, "[Symptom] ⇒ [Scope] ⇒ |Severity|")
print(lang.scope, violations)        # ac:triage []
```

## Its design

The repository's [`DESIGN.md`](https://github.com/sancovp/chaincompiler/blob/main/DESIGN.md) §1 (the one type and the
loop every constructor runs) and §4 (this package).

## License

MIT.
