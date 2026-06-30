---
name: forge-attention-chain
description: ACCC — forge an attention-chain language, gate candidates against it, package it as a SKILL.md.
---

An attention chain is an INNER 'how to think' template. ACCC is made FROM chaincompiler's forge.

```python
import accc
lang = accc.forge('debug', ['[Symptom] ⇒ [Repro] ⇒ |Localize|'], db='cc.db')
accc.gate(lang, '[Goal] ⇒ [Repro] ⇒ |Localize|')   # lint a candidate against the language
accc.package('debug', '[Symptom] ⇒ [Repro] ⇒ |Localize|', out_dir='skills')  # → <name>/SKILL.md
```
