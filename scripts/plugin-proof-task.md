This folder is empty, and the chaincompiler plugin is installed. Do exactly these two things, then stop and report.

1. Call the chaincompiler plugin's self-interpreter tool `si_interpret` with the source `1 + 1`, and report what it
   returned.
2. Use the `forge-attention-chain` skill. Run its Python exactly the way the skill says a plugin install runs it, to
   package an attention chain named `debug`, whose chain is `[Symptom] ⇒ [Repro] ⇒ |Localize|`, into the folder
   `skills/` here. Then report the path of the SKILL.md it wrote.

Install nothing with pip, and write no SKILL.md yourself.
