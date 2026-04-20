#!/usr/bin/env bash
set -euo pipefail

SCRIPT_PATH="${BASH_SOURCE[0]}"
SCRIPT_DIR="${SCRIPT_PATH%/*}"
if [[ "${SCRIPT_DIR}" == "${SCRIPT_PATH}" ]]; then
  SCRIPT_DIR="."
fi
SCRIPT_DIR="$(cd "${SCRIPT_DIR}" && pwd)"
LIB_SCRIPT="${SCRIPT_DIR}/lib/list_data.py"

FULL_MODE=false
for arg in "$@"; do
  case "$arg" in
    --full) FULL_MODE=true ;;
  esac
done

GIT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || true)"

if ! command -v python3 >/dev/null 2>&1; then
  printf '%s\n' '{"marketplace_plugins":[],"global_skills":[],"project_skills":[],"codex_marketplaces":[],"codex_plugins":[],"codex_system_skills":[],"skills":[],"collisions":[],"project_root":null,"skill_sources":null,"errors":[{"code":"NO_PYTHON3","path":"","reason":"python3 not found in PATH"}]}'
  exit 0
fi

exec python3 "${LIB_SCRIPT}" \
  --full="${FULL_MODE}" \
  --git-root="${GIT_ROOT}"
