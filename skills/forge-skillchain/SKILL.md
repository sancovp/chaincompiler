---
name: forge-skillchain
description: SCCC — forge a skill-chain language — resolve [ac|cor|skill] steps to packages and roll them up.
---

**Run its Python** from a plugin install with `uv run --no-project --with sccc==0.3.1 --with chaincompiler-accc==0.3.1 --with corcc==0.3.1 python3` — pipe a block in as `python3 - <<'PY'` … `PY` — and from a clone of the public repository where `./install.sh` ran, with the clone's `python3`.

An SC chains forged AC/CoR/skill steps toward a goal. SCCC is made FROM CORCC+ACCC+chaincompiler. Every step must already be a skill dir in `skills_dir` (or your skills), so this makes its two steps first.

```python
import accc, corcc, sccc
from corcc.notation import Move, PersonaSpec
accc.package('debug', '[Symptom] ⇒ [Repro] ⇒ |Localize|', out_dir='skills')          # the [ac:debug] step
spec = PersonaSpec(name='Debugger', moves=(Move('Symptom', ()), Move('Repro', ())))
corcc.package(corcc.forge_persona(spec, db='cc.db'), out_dir='skills')                  # the [cor:Debugger] step
seq = '[ac:debug] ⇒ [cor:Debugger] ⇒ |ShippedFix|'
sccc.forge('ship', [seq], db='cc.db')
sccc.package('ship', seq, out_dir='dist', skills_dir='skills')   # → rollup <name>/SKILL.md
```
