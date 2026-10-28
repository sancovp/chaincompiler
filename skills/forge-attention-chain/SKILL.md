---
name: forge-attention-chain
description: ACCC — forge an attention-chain language, gate candidates against it, package it as a SKILL.md.
---

**Run its Python** from a plugin install with `uv run --no-project --with chaincompiler-accc==0.3.2 python3` — pipe a block in as `python3 - <<'PY'` … `PY` — and from a clone of the public repository where `./install.sh` ran, with the clone's `python3`.

An attention chain is an INNER 'how to think' template. ACCC is made FROM chaincompiler's forge.

```python
import accc
lang = accc.forge('debug', ['[Symptom] ⇒ [Repro] ⇒ |Localize|'], db='cc.db')
accc.gate(lang, '[Goal] ⇒ [Repro] ⇒ |Localize|')   # lint a candidate against the language
accc.package('debug', '[Symptom] ⇒ [Repro] ⇒ |Localize|', out_dir='skills')  # → <name>/SKILL.md
```
