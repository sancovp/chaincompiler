# skill2framework — the chapter rung: a finished agent turned into a chapter of a SkillTome

`skill2framework` is the chapter rung of [ChainCompiler](https://github.com/sancovp/chaincompiler), a compiler-compiler for
cognition. It is the deterministic part of turning a finished agent into a chapter of its author's SkillTome. The
`skill2framework` skills the ChainCompiler plugin ships write two posts about the agent — a narrative post and a deep
dive — and this package does everything after them:

- `assemble_chapter(blog1, blog2, chapter_dir=…, framework_name=…)` makes the two posts one self-contained chapter folder,
  its links, calls to action and manifest included;
- `package_plugin(framework_skill, chapter_dir, out_dir=…, name=…)` packages the framework's skill and its chapter as an
  installable plugin, repathing the chapter's links into the bundle and checking that each resolves;
- `fold_into_tome(framework_skill_dir, volume=…, tome_root=…)` folds the framework into the tome, through
  `agent-skilltree`'s `tome.fold`;
- `JourneyCore` and `render_blog1` are the narrative post's model and its renderer, so the post is filled in and never
  written by hand.

## Install

```bash
pip install skill2framework
```

It brings `agent-skilltree` from PyPI. To work on it, clone the [repository](https://github.com/sancovp/chaincompiler)
and run `./install.sh`, which installs all fifteen packages editable.

## Use

```python
from skill2framework import assemble_chapter, fold_into_tome, package_plugin
```

Each call takes the files the one before it wrote; the `skill2framework` skills in the plugin run them in order.

## Its design

The repository's [`DESIGN.md`](https://github.com/sancovp/chaincompiler/blob/main/DESIGN.md) §13.

## License

MIT.
