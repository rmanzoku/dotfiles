# dotfiles

[chezmoi](https://www.chezmoi.io/) で管理する dotfiles。

## セットアップ (新しいマシン)

```bash
# chezmoi をインストール
brew install chezmoi

# dotfiles を適用
chezmoi init --apply rmanzoku

# 必要ならシークレットを設定 (~/.zshenv.local は手動管理)
echo 'export GEMINI_API_KEY="your-key-here"' > ~/.zshenv.local

# Homebrew パッケージを復元
brew bundle --file=$(chezmoi source-path)/Brewfile
```

## 日常の操作

```bash
# dotfile の変更を chezmoi に反映
chezmoi add ~/.zshrc

# 差分を確認
chezmoi diff

# 変更をコミット
chezmoi cd
git add -A && git commit -m "update dotfiles"
git push
```

### chezmoi 管理外の変更を検出 (`chezmoi-drift`)

ツールやアプリが dotfile を直接変更した場合のケア:

```bash
# source と .chezmoiignore の不整合を確認
scripts/chezmoi-drift --check-ignore

# 差分のあるファイルを確認
scripts/chezmoi-drift

# 外部の変更を chezmoi ソースに取り込む
scripts/chezmoi-drift --apply

# chezmoi ソースの状態に戻す
scripts/chezmoi-drift --restore
```

### Worktree での AI 編集

Conductor などのツールが git worktree を立ち上げて dotfiles を編集する際、`setup.sh` が自動実行されます。このスクリプトは chezmoi ソースとの差分を検出し、編集前にドリフトがあれば警告します。

## 主なファイル

### chezmoi で配備するファイル

| 実ファイル | 用途 |
|---------|------|
| `.zshrc` | Zsh 設定 |
| `.zshenv` | Zsh の local override / secret 読み込み |
| `.zprofile` | Zsh ログイン時初期化 (Homebrew, `rbenv`) |
| `.profile` | 汎用プロファイル |
| `.gitconfig` | Git 設定 |
| `.config/git/ignore` | グローバル gitignore |
| `.local/bin/env` | PATH 設定スクリプト |
| `.claude/CLAUDE.md` | Claude Code グローバル設定 |
| `.claude/settings.json` | Claude Code 設定 |
| `.codex/AGENTS.md` | Codex エージェント設定 |
| `.codex/config.toml` | Codex モデル・プロジェクト設定 |
| `.qwen/QWEN.md` | Qwen ユーザー設定 |
| `.qwen/settings.json` | Qwen モデルプロバイダー設定 |
| `Brewfile` | Homebrew パッケージ一覧 |

### repo ローカルで管理するファイル

| パス | 用途 |
|---------|------|
| `.claude/skills/` | このリポジトリ専用の Claude Code スキル |
| `docs/` | 運用ルール、ADR、補助ドキュメント |
| `scripts/` | repo 運用スクリプト |

### chezmoi ソースとの主な対応

| 実ファイル | chezmoi ソース |
|-----------|----------------|
| `.claude/CLAUDE.md` | `dot_claude/CLAUDE.md` |
| `.claude/settings.json` | `dot_claude/settings.json` |
| `.codex/AGENTS.md` | `dot_codex/AGENTS.md` |
| `.codex/config.toml` | `dot_codex/private_config.toml` |
| `.qwen/QWEN.md` | `dot_qwen/QWEN.md` |
| `.qwen/settings.json` | `dot_qwen/settings.json` |

`dot_` はドットファイル化です。`private_` はファイル名変換ではなく、target の group / world 権限を外す属性です。
`.claude/skills/` は repo ローカル運用とし、chezmoi ではホームディレクトリへ配備しません。
詳細は [chezmoi-knowledge/SKILL.md](/Users/rmanzoku/.local/share/chezmoi/.claude/skills/chezmoi-knowledge/SKILL.md) と [semantics.md](/Users/rmanzoku/.local/share/chezmoi/.claude/skills/chezmoi-knowledge/references/semantics.md) を参照してください。

## シークレット管理

API キーなどのシークレットは `~/.zshenv.local` に配置し、chezmoi 管理外としています。
