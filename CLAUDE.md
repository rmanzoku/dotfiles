# リポジトリ管理ルール

- このリポジトリ（dotfiles）は原則として Claude Code が更新する
- dotfile の変更時は必ず `dotfile-update` スキルを使用すること
- 手動編集は `~/.zshenv` 等の chezmoi 管理外ファイルに限る

# スキル管理

- 本リポジトリでは Claude Code のスキル（`dot_claude/skills/`）のみを管理する
- 各 AI ツール間のスキル同期は skill-manager スキルの責務であり、本リポジトリでは扱わない
