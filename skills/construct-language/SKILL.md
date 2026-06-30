---
name: construct-language
description: Construct a whole cognition-language for a domain (AC + CoR + SC) in one call (the AIOS top-door).
---

Mint a domain's attention chain, chain-of-reasoning, and a skill chain that chains them — a new domain language pre-powered with AC + CoR. Lives in chainaios (ABOVE the *CC).

```python
import chainaios
bundle = chainaios.construct_language('triage',
    ac_chain='[Symptom] ⇒ [Scope] ⇒ |Severity|',
    db='cc.db', skills_dir='skills', out_dir='dist')
# bundle.ac / bundle.cor / bundle.sc → three SKILL.md packages
```
