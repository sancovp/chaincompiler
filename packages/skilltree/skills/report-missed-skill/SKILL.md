---
name: report-missed-skill
description: Use when you needed a skill that does not exist, or the user says you missed a skill ("you missed X — report it"). Files a structured missed-skill report so the gap can be fixed. Triggers on "report missed skill", "missing skill", "no skill for this", "you missed".
---

# report-missed-skill

The Skill OS grows from its own gaps. When a skill that *should* exist doesn't,
**file a report** — don't just work around it silently.

## When to use

- **Agent-initiated:** you're doing a task and there's no skill for it. File a report describing the gap, then proceed with your best effort.
- **User-initiated:** the user says *"you missed X — use report-missed-skill and then use it."* File a report for X describing what happened, then continue.

## How

Run:

```bash
skilltree report-missed \
  --needed   "<the skill / capability that was needed>" \
  --happened "<what you did instead, or what went wrong>" \
  --suggests "<proposed skill name + one-line purpose>"
```

For "expected a skill to fire but it didn't":

```bash
skilltree mark-problem --skill "<skill>" --expected "<what you expected>" --happened "<what happened>"
```

Reports accumulate in `~/.claude/skill-reports.json`. An improver agent later reads
the open queue (`skilltree reports`), creates or improves the skills, and resolves them.
This is ring 3 of the Skill OS — the system improving itself from use.
