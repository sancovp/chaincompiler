#!/usr/bin/env bash
# Install every ChainCompiler package in this monorepo, editable.
# Everything (including `rulecatcher`, the gate) is vendored here — one clone,
# one command, no external setup.
set -euo pipefail
cd "$(dirname "$0")"

# External deps (installed WITH deps, since the monorepo packages below go in --no-deps):
#   - pydantic-stack-core : THE foundation (RenderablePiece + MetaStack — every prompt is a MetaStack of blocks)
#   - agent-prompt-engineering (APE) : the prompt engine the whole stack imports DOWN onto (>=0.2.0, on pydantic-stack-core)
#   - agent-skilltree : coordinate-addressed skill placement (PyPI name; import name stays `skilltree`).
#     >=0.4.0: portable trees (breadcrumbs relative to each node's folder; `relink --localize` at install);
#     the `skill2framework` package's fold_into_tome delegates to skilltree.tome.fold
#   - numpy : glyphsteer's dense regime imports it at package import time
#   - lark + pyyaml : honeyc's parser and its YAML lens · click : every package's CLI · fastmcp : the si MCP server
#     (every non-optional dependency the packages declare; the optional extras — glyphsteer[dense|serve|st],
#     honeyc[dev] — are installed only when wanted)
#   - setuptools>=77 : the build backend every package's build file requires (77 is the first that reads
#     `license = "MIT"`); the packages below build without isolation, so this environment's own setuptools builds
#     them, and a fresh environment carries none, or an older one
python3 -m pip install "setuptools>=77" "pydantic-stack-core>=0.1.4" "agent-prompt-engineering>=0.2.0" "agent-skilltree>=0.4.0" numpy lark pyyaml click "fastmcp>=4.1,<5"

# The monorepo packages, editable. Layering (imports point DOWN, enforced by .importlinter):
#   chainaios > sccc > corcc > accc > chaincompiler > prompt_engineering(APE).
# rulecatcher first (the gate; the *CC import it). chainaios = the Bandit AIOS app (owns the `chaincompiler` CLI).
# glyphsteer included: chainaios' roll_up_algebra writes the persona legend from it (silent no-legend fallback without it).
# Folders, not distribution names: four distributions are named apart from their folder and import name, since their
# bare names belong to other projects on PyPI — chaincompiler-accc · chaincompiler-archetype · chaincompiler-si ·
# skillchain-compiler (DESIGN §18).
PKGS=(rulecatcher honeyc skillchain-compiler chaincompiler accc corcc sccc chainaios si archetype skill2framework
      glyphsteer personacc personapack goldenreq)
ARGS=()
for p in "${PKGS[@]}"; do ARGS+=(-e "packages/$p"); done

python3 -m pip install --no-build-isolation --no-deps "${ARGS[@]}"
echo "✓ installed ${#PKGS[@]} packages editable (rulecatcher + chainaios included) + APE/pydantic-stack-core/agent-skilltree"
