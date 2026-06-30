---
name: make-persona
description: Generate a full persona prompt from a small spec (block types + a chain-of-reasoning DSL block).
---

One call → a complete persona prompt, deterministically.

```python
from prompt_engineering import make_persona
make_persona({
    'name': 'Ada', 'role': 'a senior debugger',
    'reasoning': {'foci': ['Symptom','Repro','Bisect'], 'held': 'RootCause', 'decision': 'the minimal fix'},
    'rules': ['Reproduce before theorizing.'], 'output': 'A markdown report.',
})
```

`reasoning` becomes a ChainOfReasoning block that NESTS an attention chain.
