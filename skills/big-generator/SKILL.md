---
name: big-generator
description: Roll the per-chain-type generators (AC/CoR/SC) into ONE callable that renders a chain sequence.
---

Give a template-sequence of chains (`(kind, spec)`, kind ∈ {ac, cor, sc}); get ONE callable that renders them into one prompt (a MetaStack of the chain blocks).

```python
from prompt_engineering import big_generator
gen = big_generator([
    ('ac',  {'foci': ['Symptom','Repro'], 'held': 'Localize'}),
    ('cor', {'name': 'Debugger', 'foci': ['Symptom','Repro'], 'held': 'RootCause', 'decision': 'the fix'}),
])
gen()   # → the composed prompt
```
