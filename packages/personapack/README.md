# personapack — a library of ready personas to seat as agents

`personapack` is a library of ready personas for the agents [ChainCompiler](https://github.com/sancovp/chaincompiler)
builds. Each entry is a whole persona — a `PersonaBundle` from [`personacc`](https://pypi.org/project/personacc/):
description blocks, attention chains and at least one chain of reasoning that uses them — carried with

- its invocation terms (the names it answers to),
- its provenance,
- its domain,
- and an activation grade, `seed` < `proven-in-forge` < `tested-with-receipt`, with the receipt behind the grade.

`seat(name)` returns the keyword arguments `chainaios.make_gba` takes, so one call seats a persona as an agent. The
library holds ten: the three seed personas, four proven in the AEGIS forge (Aegis, SdnaSynth, HormoziAegis,
FrameBudgetGuardian) and three tested with a live model (Bodhisattva, SamayaReviewer, ParamitaReader). The forge script
and the receipts behind the two upper grades are not in the repository yet, so a reader cannot check them.

## Install

```bash
pip install personapack chainaios
```

`personapack` brings [`personacc`](https://pypi.org/project/personacc/) and [`corcc`](https://pypi.org/project/corcc/) at
the same release; [`chainaios`](https://pypi.org/project/chainaios/) is what seats a persona as an agent. To work on it,
clone the [repository](https://github.com/sancovp/chaincompiler) and run `./install.sh`, which installs all fifteen
packages editable.

## Use

```python
import personapack
from chainaios import make_gba

print(personapack.get("samayareviewer").activation_grade)       # tested-with-receipt
gba = make_gba("review", "./reviewer", **personapack.seat("samayareviewer"))   # its chains, persona and role
print(gba.closed)                                                # True
```

## Its design

The repository's [`DESIGN.md`](https://github.com/sancovp/chaincompiler/blob/main/DESIGN.md) §6.

## License

MIT.
