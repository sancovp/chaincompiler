---
name: big-generator
description: Roll the per-chain-type generators (AC/CoR/SC) into ONE callable that renders a chain sequence.
---

**Run its Python** from a plugin install with `uv run --no-project --with "agent-prompt-engineering>=0.2.0" python3` — pipe a block in as `python3 - <<'PY'` … `PY` — and from a clone of the public repository where `./install.sh` ran, with the clone's `python3`.

Give a template-sequence of chains (`(kind, spec)`, kind ∈ {ac, cor, sc}); get ONE callable that renders them into one prompt (a MetaStack of the chain blocks).

```python
from prompt_engineering import big_generator
gen = big_generator([
    ('ac',  {'foci': ['Symptom','Repro'], 'held': 'Localize'}),
    ('cor', {'name': 'Debugger', 'foci': ['Symptom','Repro'], 'held': 'RootCause', 'decision': 'the fix'}),
])
gen()   # → the composed prompt
```
