---
name: forge-skillchain
description: SCCC — forge a skill-chain language — resolve [ac|cor|skill] steps to packages and roll them up.
---

**Run its Python** from a plugin install with `uv run --no-project --with sccc==0.3.0 python3` — pipe a block in as `python3 - <<'PY'` … `PY` — and from a clone of the public repository where `./install.sh` ran, with the clone's `python3`.

An SC chains forged AC/CoR/skill steps toward a goal. SCCC is made FROM CORCC+ACCC+chaincompiler.

```python
import sccc
seq = '[ac:debug] ⇒ [cor:Debugger] ⇒ |ShippedFix|'
sccc.forge('ship', [seq], db='cc.db')
sccc.package('ship', seq, out_dir='dist', skills_dir='skills')   # → rollup <name>/SKILL.md
```
