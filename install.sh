#!/usr/bin/env bash
# Install every ChainCompiler package in this monorepo, editable.
# Everything (including `rulecatcher`, the gate) is vendored here — one clone,
# one command, no external setup.
set -euo pipefail
cd "$(dirname "$0")"

# External deps (installed WITH deps, since the monorepo packages below go in --no-deps):
#   - pydantic-stack-core : THE foundation (RenderablePiece + MetaStack — every prompt is a MetaStack of blocks)
#   - agent-prompt-engineering (APE) : the prompt engine the whole stack imports DOWN onto (>=0.2.0, on pydantic-stack-core)
#   - agent-skilltree : coordinate-addressed skill placement (PyPI name; import name stays `skilltree`)
python3 -m pip install "pydantic-stack-core>=0.1.4" "agent-prompt-engineering>=0.2.0" "agent-skilltree>=0.2.0"

# The monorepo packages, editable. Layering (imports point DOWN, enforced by .importlinter):
#   chainaios > sccc > corcc > accc > chaincompiler > prompt_engineering(APE).
# rulecatcher first (the gate; the *CC import it). chainaios = the Bandit AIOS app (owns the `chaincompiler` CLI).
PKGS=(rulecatcher honeyc skillchain-compiler chaincompiler accc corcc sccc chainaios si archetype)
ARGS=()
for p in "${PKGS[@]}"; do ARGS+=(-e "packages/$p"); done

python3 -m pip install --no-build-isolation --no-deps "${ARGS[@]}"
echo "✓ installed ${#PKGS[@]} packages editable (rulecatcher + chainaios included) + APE/pydantic-stack-core/agent-skilltree"
