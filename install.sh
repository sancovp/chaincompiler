#!/usr/bin/env bash
# Install every ChainCompiler package in this monorepo, editable.
#
# NOTE: `rulecatcher` is an EXTERNAL dependency (its own repo). Install it first:
#   pip install --no-build-isolation -e /path/to/rulecatcher
# then run this script.
set -euo pipefail
cd "$(dirname "$0")"

PKGS=(chaincompiler honeyc skillchain-compiler accc corcc sccc skilltree si)
ARGS=()
for p in "${PKGS[@]}"; do ARGS+=(-e "packages/$p"); done

python3 -m pip install --no-build-isolation --no-deps "${ARGS[@]}"
echo "✓ installed ${#PKGS[@]} packages editable (rulecatcher must be installed separately)"
