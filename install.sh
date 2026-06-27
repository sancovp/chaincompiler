#!/usr/bin/env bash
# Install every ChainCompiler package in this monorepo, editable.
# Everything (including `rulecatcher`, the gate) is vendored here — one clone,
# one command, no external setup.
set -euo pipefail
cd "$(dirname "$0")"

# skilltree is published standalone as `agent-skilltree` (the PyPI name `skilltree`
# is taken by an unrelated package); import name stays `skilltree`.
python3 -m pip install "agent-skilltree>=0.2.0"

# rulecatcher first (the gate; the *CC packages import it).
PKGS=(rulecatcher honeyc skillchain-compiler chaincompiler accc corcc sccc si archetype)
ARGS=()
for p in "${PKGS[@]}"; do ARGS+=(-e "packages/$p"); done

python3 -m pip install --no-build-isolation --no-deps "${ARGS[@]}"
echo "✓ installed ${#PKGS[@]} packages editable (rulecatcher included) + agent-skilltree"
