---
name: make-prompt
description: Compose a prompt as a MetaStack of RenderablePiece blocks (deterministic data → prompt).
---

Build a prompt from blocks — the foundation move (every prompt IS a MetaStack of RenderablePieces).

```python
from prompt_engineering import Role, BulletList, render_prompt
render_prompt(
    Role(role='a senior code reviewer', mission='find correctness bugs'),
    BulletList(title='Rules', items=['Cite file:line.', 'Never invent an API.']),
)
```

Blocks: Text, Heading, Section, Role, BulletList, KeyValue, Fenced, Template, Group. Declarative form: `{"type": "Role", "role": "..."}` via `block_from_dict`. Same blocks → same prompt.
