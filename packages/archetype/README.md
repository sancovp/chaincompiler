# chaincompiler-archetype — an archetype compiled as a state machine

`chaincompiler-archetype` (import `archetype`) is the archetype compiler of
[ChainCompiler](https://github.com/sancovp/chaincompiler), a compiler-compiler for cognition. It compiles an archetype as
a state machine rather than a name, because what an archetype does is change: it has

- a **Persona** (the mask it wears),
- a **Shadow** (the persona's denied inverse),
- a **Self** (the process that holds both),
- an **Odyssey** (a succession of journeys, one for each other archetype it meets, ending in a journey after the
  return),
- and a **Becoming** (the archetype it turns into next).

From one seed it infers the aspects it was not given, builds the Odyssey, validates the constraints C1–C6, and emits the
result as readable text, triples, Prolog, Cypher, JSON or a `SKILL.md` an agent loads.

## Install

```bash
pip install chaincompiler-archetype
```

It installs the `archetype` command and brings the [`chaincompiler`](https://pypi.org/project/chaincompiler/) base at the
same release. To work on it, clone the [repository](https://github.com/sancovp/chaincompiler) and run `./install.sh`,
which installs all fifteen packages editable.

## Use

```python
from archetype import compile_archetype, emit, is_valid

hero = compile_archetype("Hero")          # the missing aspects inferred, the Odyssey built
print(is_valid(hero))                     # True
print(emit(hero, "readable"))             # "# Hero — a recursive individuation circuit" …
```

Its specification, cited in its code as `ARCHETYPE-COMPILER.md`, is not yet in the repository.

## Its design

The repository's [`DESIGN.md`](https://github.com/sancovp/chaincompiler/blob/main/DESIGN.md) §12.

## License

MIT.
