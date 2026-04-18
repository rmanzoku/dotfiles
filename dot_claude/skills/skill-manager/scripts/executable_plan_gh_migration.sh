#!/usr/bin/env bash
set -euo pipefail

SCRIPT_PATH="${BASH_SOURCE[0]}"
SCRIPT_DIR="${SCRIPT_PATH%/*}"
if [[ "${SCRIPT_DIR}" == "${SCRIPT_PATH}" ]]; then
  SCRIPT_DIR="."
fi
SCRIPT_DIR="$(cd "${SCRIPT_DIR}" && pwd)"
LIB_SCRIPT="${SCRIPT_DIR}/lib/gh_migration_plan.py"

GIT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || true)"

if ! command -v python3 >/dev/null 2>&1; then
  printf '%s\n' '{"generated_at":"","gh_version":"","project_root":null,"candidates":[],"manual_follow_up":[],"errors":[{"code":"NO_PYTHON3","path":"","reason":"python3 not found in PATH"}]}'
  exit 0
fi

exec python3 "${LIB_SCRIPT}" \
  --git-root="${GIT_ROOT}" \
  "$@"
