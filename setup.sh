#!/bin/bash
set -eu

info() { printf '\033[1;34m[info]\033[0m %s\n' "$1"; }
warn() { printf '\033[1;33m[warn]\033[0m %s\n' "$1"; }

if ! scripts/chezmoi-drift --check-ignore >/dev/null; then
  warn ".chezmoiignore と source state の不整合があります。編集前に解消してください。"
  warn "  詳細確認: scripts/chezmoi-drift --check-ignore"
  exit 1
fi

# --- ドリフト検出 ---
info "chezmoi 管理下のファイルの差分を確認しています..."

diff_output="$(chezmoi diff 2>/dev/null || true)"

if [ -z "$diff_output" ]; then
  info "差分なし。すべてのファイルが chezmoi ソースと一致しています。"
  exit 0
fi

warn "以下のファイルに chezmoi ソースとの差分があります:"
echo "$diff_output" | grep -E '^(---|\+\+\+) [ab]/' | sed 's|^... [ab]/|  |' | sort -u
echo ""
warn "編集前に差分を解消してください:"
warn "  変更を取り込む: scripts/chezmoi-drift --apply"
warn "  管理状態に戻す: scripts/chezmoi-drift --restore"
