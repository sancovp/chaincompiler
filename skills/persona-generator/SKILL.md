---
name: persona-generator
description: A named persona from a ROLE-intro block + a chain sequence; XML by default, or markdown mode.
---

**Run its Python** from a plugin install with `uv run --no-project --with "agent-prompt-engineering>=0.2.0" python3` — pipe a block in as `python3 - <<'PY'` … `PY` — and from a clone of the public repository where `./install.sh` ran, with the clone's `python3`.

Subclass of the big generator: a system-prompt name + a ROLE-intro block wrapping the chains.

```python
from prompt_engineering import persona_generator
gen = persona_generator('Ada the Debugger',
    [('ac', {'foci': ['Symptom','Repro'], 'held': 'Localize'})],
    role='a senior debugger',
    fields={'mission': 'find the root cause', 'law': 'reproduce before theorizing'},
    mode='xml')        # default: <role name=…><mission>…</mission> … </role>
gen()
```

`mode='markdown'` → a `# {name}` heading + a `You are …` role line, then the chains.
