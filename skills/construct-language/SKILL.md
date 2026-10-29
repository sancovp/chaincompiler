---
name: construct-language
description: Construct a whole cognition-language for a domain (AC + CoR + SC) in one call (the AIOS top-door).
---

**Run its Python** from a plugin install with `uv run --no-project --with chainaios==0.3.3 python3` — pipe a block in as `python3 - <<'PY'` … `PY` — and from a clone of the public repository where `./install.sh` ran, with the clone's `python3`.

Mint a domain's attention chain, chain-of-reasoning, and a skill chain that chains them — a new domain language pre-powered with AC + CoR. Lives in chainaios (ABOVE the *CC).

```python
import chainaios
bundle = chainaios.construct_language('triage',
    ac_chain='[Symptom] ⇒ [Scope] ⇒ |Severity|',
    db='cc.db', skills_dir='skills', out_dir='dist')
# bundle.ac / bundle.cor / bundle.sc → three SKILL.md packages
```
