#!/usr/bin/env python3
"""
skillchain — compose Claude Code skills into a validated, packaged chain.

A skillchain is an ordered list of steps. Two step kinds:
  • skill  — invoke a named skill (validated to exist on disk)
  • cor    — an Attention-Chain / Chain-of-Reasoning bridge between skills
             (an explicit reasoning step that routes one skill's output into the next)

The compiler:
  1. indexes every skill on disk (~/.claude/skills + ~/.claude/plugins),
  2. validates every referenced skill EXISTS (errors listing any missing),
  3. wires the CoR bridges between steps,
  4. exports a skill PACKAGE (<out>/<name>/SKILL.md + chain.json) that, when
     invoked, executes the chain in order.

Usage:
  skillchain.py list
  skillchain.py validate <spec.json|spec.chain>
  skillchain.py compile  <spec.json|spec.chain> [--out DIR] [--install]

Spec formats — see README.md. JSON is canonical; `.chain` is a light text DSL:
    name: research_to_paper
    description: research a question then write it up
    > deep-research : <the question>            # '>' = skill step  (skill : args)
    = research                                  # '=' = capture last result as a var
    ~ Given {research}, extract the 3 strongest claims and the gaps, then write an outline brief.   # '~' = CoR bridge
    > academic-paper : write the paper from the outline brief
"""
import argparse, json, os, re, sys, pathlib, datetime

HOME = pathlib.Path.home()
SKILL_ROOTS = [HOME / ".claude" / "skills", HOME / ".claude" / "plugins"]


# ----------------------------------------------------------------------------- skill index
def _read(path):
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def _frontmatter(path):
    txt = _read(path)
    name = None
    desc = None
    m = re.search(r"^\s*name:\s*(.+?)\s*$", txt, re.MULTILINE)
    if m:
        name = m.group(1).strip().strip("\"'")
    m = re.search(r"^\s*description:\s*(.+?)\s*$", txt, re.MULTILINE)
    if m:
        desc = m.group(1).strip().strip("\"'")
    return name, desc


def index_skills(roots=SKILL_ROOTS):
    """Return {alias -> {'path':Path,'name':str,'desc':str}}. A skill is reachable
    by its frontmatter name, its directory name, and (after a ':') the colon-suffix."""
    idx = {}
    for root in roots:
        if not root.exists():
            continue
        for sk in root.rglob("SKILL.md"):
            name, desc = _frontmatter(sk)
            dirname = sk.parent.name
            canonical = name or dirname
            rec = {"path": sk, "name": canonical, "desc": desc or ""}
            for alias in {name, dirname, (name or "").split(":")[-1], dirname.split(":")[-1]}:
                if alias:
                    idx.setdefault(alias, rec)
    return idx


def resolve(ref, idx):
    """Resolve a skill reference against the index. Try exact, then colon-suffix."""
    if ref in idx:
        return idx[ref]
    if ":" in ref and ref.split(":")[-1] in idx:
        return idx[ref.split(":")[-1]]
    return None


# ----------------------------------------------------------------------------- spec parsing
def parse_spec(path):
    p = pathlib.Path(path)
    text = _read(p)
    if p.suffix == ".json" or text.lstrip().startswith("{"):
        return json.loads(text)
    return parse_chain_dsl(text)


def parse_chain_dsl(text):
    spec = {"name": None, "description": "", "steps": []}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.lower().startswith("name:"):
            spec["name"] = line.split(":", 1)[1].strip()
        elif line.lower().startswith("description:"):
            spec["description"] = line.split(":", 1)[1].strip()
        elif line.startswith(">"):  # skill step:  > skill : args
            body = line[1:].strip()
            if ":" in body:
                skill, args = body.split(":", 1)
                spec["steps"].append({"skill": skill.strip(), "args": args.strip()})
            else:
                spec["steps"].append({"skill": body.strip(), "args": ""})
        elif line.startswith("="):  # capture last result:  = varname
            var = line[1:].strip()
            if spec["steps"]:
                spec["steps"][-1]["capture"] = var
        elif line.startswith("~"):  # CoR bridge
            spec["steps"].append({"cor": line[1:].strip()})
    return spec


# ----------------------------------------------------------------------------- validate
def validate(spec, idx):
    """Return (ok, report). report lists every step with resolved path or MISSING."""
    rows, missing = [], []
    if not spec.get("name"):
        missing.append("(spec has no 'name')")
    for i, step in enumerate(spec.get("steps", []), 1):
        if "skill" in step:
            rec = resolve(step["skill"], idx)
            if rec:
                rows.append((i, "skill", step["skill"], "ok", str(rec["path"])))
            else:
                rows.append((i, "skill", step["skill"], "MISSING", ""))
                missing.append(step["skill"])
        elif "cor" in step:
            rows.append((i, "cor", (step["cor"][:48] + "…") if len(step["cor"]) > 48 else step["cor"], "ok", ""))
        else:
            rows.append((i, "?", str(step), "BAD-STEP", ""))
            missing.append(f"step {i} (unknown kind)")
    return (len(missing) == 0), rows, missing


# ----------------------------------------------------------------------------- compile
def compile_package(spec, idx, out_dir):
    name = spec["name"]
    desc = spec.get("description", "") or f"Compiled skillchain: {name}"
    steps = spec.get("steps", [])
    deps = sorted({resolve(s["skill"], idx)["name"] for s in steps if "skill" in s})

    body = []
    body.append(f"# {name} — compiled skillchain\n")
    body.append(
        f"> Compiled by `skillchain.py` on {datetime.date.today().isoformat()}. "
        f"Orchestrates {len(steps)} step(s) composing {len(deps)} skill(s).\n"
        f"> **Dependencies (validated present at compile time):** "
        + (", ".join(f"`{d}`" for d in deps) if deps else "none")
        + "\n"
    )
    body.append(
        "**Execute the steps below in order.** Carry each step's result forward; where a step "
        "references `{var}`, substitute the captured value from the named earlier step.\n"
    )
    sidx = 0
    for step in steps:
        sidx += 1
        if "skill" in step:
            rec = resolve(step["skill"], idx)
            args = step.get("args", "").strip()
            cap = step.get("capture")
            body.append(f"## Step {sidx} — invoke skill `{rec['name']}`")
            if rec.get("desc"):
                body.append(f"*{rec['desc']}*\n")
            body.append(
                f"Invoke the **{rec['name']}** skill"
                + (f" with input: {args}" if args else " (no extra input)")
                + (f"\n\n→ Capture its result as `{cap}`." if cap else "")
                + "\n"
            )
        elif "cor" in step:
            body.append(f"## Step {sidx} — reasoning bridge (CoR / AttentionChain)")
            body.append(
                "Reason explicitly, step by step:\n\n"
                f"> {step['cor']}\n\n"
                "State the conclusion, then carry it forward as the input to the next step.\n"
            )
    body.append("## Done")
    body.append("Return the final step's output as the result of this chain.\n")

    skill_md = f"---\nname: {name}\ndescription: {desc}\n---\n\n" + "\n".join(body)

    pkg = pathlib.Path(out_dir) / name
    pkg.mkdir(parents=True, exist_ok=True)
    (pkg / "SKILL.md").write_text(skill_md, encoding="utf-8")
    (pkg / "chain.json").write_text(json.dumps(spec, indent=2), encoding="utf-8")
    return pkg, deps


# ----------------------------------------------------------------------------- cli
def _print_rows(rows):
    for i, kind, what, status, path in rows:
        mark = "✓" if status == "ok" else "✗"
        line = f"  {mark} [{i}] {kind:5} {what}"
        if status != "ok":
            line += f"   <{status}>"
        elif path:
            line += f"   → {path}"
        print(line)


def main():
    ap = argparse.ArgumentParser(prog="skillchain", description="compose skills into a validated, packaged chain")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list", help="list indexed skills")
    v = sub.add_parser("validate", help="check a chain spec's skills all exist")
    v.add_argument("spec")
    c = sub.add_parser("compile", help="validate + emit a skill package")
    c.add_argument("spec")
    c.add_argument("--out", default="dist", help="output dir (default: ./dist)")
    c.add_argument("--install", action="store_true", help="emit into ~/.claude/skills instead of --out")
    a = ap.parse_args()

    idx = index_skills()

    if a.cmd == "list":
        names = sorted({rec["name"] for rec in idx.values()})
        print(f"{len(names)} skills indexed under {', '.join(str(r) for r in SKILL_ROOTS if r.exists())}:")
        for n in names:
            print(f"  - {n}")
        return 0

    spec = parse_spec(a.spec)
    ok, rows, missing = validate(spec, idx)
    print(f"chain: {spec.get('name')!r}  ({len(spec.get('steps', []))} steps)")
    _print_rows(rows)

    if a.cmd == "validate":
        if ok:
            print("✓ valid — all skills resolve.")
            return 0
        print(f"✗ INVALID — {len(missing)} problem(s): {', '.join(missing)}")
        return 1

    # compile
    if not ok:
        print(f"✗ refusing to compile — {len(missing)} missing/bad: {', '.join(missing)}")
        return 1
    out = (HOME / ".claude" / "skills") if a.install else pathlib.Path(a.out)
    pkg, deps = compile_package(spec, idx, out)
    print(f"✓ compiled → {pkg}/SKILL.md  (+ chain.json)")
    print(f"  deps: {', '.join(deps) if deps else 'none'}")
    if a.install:
        print("  installed into ~/.claude/skills — invokable as a skill after reload.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
