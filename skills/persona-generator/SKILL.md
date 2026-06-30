---
name: persona-generator
description: A named persona from a ROLE-intro block + a chain sequence; XML by default, or markdown mode.
---

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
