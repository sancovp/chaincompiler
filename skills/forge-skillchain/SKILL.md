---
name: forge-skillchain
description: SCCC — forge a skill-chain language: resolve [ac|cor|skill] steps to packages and roll them up.
---

An SC chains forged AC/CoR/skill steps toward a goal. SCCC is made FROM CORCC+ACCC+chaincompiler.

```python
import sccc
seq = '[ac:debug] ⇒ [cor:Debugger] ⇒ |ShippedFix|'
sccc.forge('ship', [seq], db='cc.db')
sccc.package('ship', seq, out_dir='dist', skills_dir='skills')   # → rollup <name>/SKILL.md
```
