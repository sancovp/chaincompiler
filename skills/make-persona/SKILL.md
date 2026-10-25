---
name: make-persona
description: Generate a full persona prompt from a small spec (block types + a chain-of-reasoning DSL block).
---

**Run its Python** from a plugin install with `uv run --no-project --with "agent-prompt-engineering>=0.2.0" python3` — pipe a block in as `python3 - <<'PY'` … `PY` — and from a clone of the public repository where `./install.sh` ran, with the clone's `python3`.

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
