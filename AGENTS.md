# リポジトリ管理ルール

- このリポジトリ（dotfiles）の管理責任は Codex が持つ
- `dot_*` 配下のファイルは chezmoi により環境へ配置される成果物として扱う
- `dot_*` 配下の変更時は必ず `dotfile-update` スキルを使用すること
- 手動編集は `~/.zshenv` 等の chezmoi 管理外ファイルに限る

# スキル管理

- 本リポジトリでは Claude Code 用のスキル（`dot_claude/skills/`）も管理対象に含む
- 各 AI ツール間のスキル同期は skill-manager スキルの責務であり、本リポジトリでは扱わない
