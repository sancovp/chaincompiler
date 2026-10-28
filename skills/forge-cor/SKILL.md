---
name: forge-cor
description: CORCC — forge a chain-of-reasoning persona (NESTS an attention chain); lint + package it.
---

**Run its Python** from a plugin install with `uv run --no-project --with corcc==0.3.2 python3` — pipe a block in as `python3 - <<'PY'` … `PY` — and from a clone of the public repository where `./install.sh` ran, with the clone's `python3`.

A CoR is a SPOKEN paragraph that ends in a decision; it nests a forged AC. CORCC is made FROM ACCC.

```python
import corcc
from corcc.notation import Move, PersonaSpec
spec = PersonaSpec(name='Debugger', moves=(Move('Symptom', ()), Move('Repro', ())), blurb='find the cause')
persona = corcc.forge_persona(spec, db='cc.db')
corcc.package(persona, out_dir='skills')   # → <name>/SKILL.md (inner AC nested inside)
```
