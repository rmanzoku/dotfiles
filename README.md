# dotfiles

[chezmoi](https://www.chezmoi.io/) で管理する dotfiles。

## セットアップ (新しいマシン)

```bash
# chezmoi をインストール
brew install chezmoi

# dotfiles を適用
chezmoi init --apply rmanzoku

# シークレットを設定 (~/.zshenv は手動管理)
echo 'export GEMINI_API_KEY="your-key-here"' > ~/.zshenv

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
# 差分のあるファイルを確認
chezmoi-drift

# 外部の変更を chezmoi ソースに取り込む
chezmoi-drift --apply

# chezmoi ソースの状態に戻す
chezmoi-drift --restore
```

### Worktree での AI 編集

Conductor などのツールが git worktree を立ち上げて dotfiles を編集する際、`setup.sh` が自動実行されます。このスクリプトは chezmoi ソースとの差分を検出し、編集前にドリフトがあれば警告します。

## 管理対象ファイル

| ファイル | 用途 |
|---------|------|
| `.zshrc` | Zsh 設定 |
| `.zprofile` | Zsh プロファイル (Homebrew) |
| `.profile` | 汎用プロファイル |
| `.gitconfig` | Git 設定 |
| `.config/git/ignore` | グローバル gitignore |
| `.local/bin/env` | PATH 設定スクリプト |
| `.local/bin/chezmoi-drift` | ドリフト検出スクリプト |
| `.claude/CLAUDE.md` | Claude Code グローバル設定 |
| `.claude/settings.json` | Claude Code 設定 |
| `.claude/skills/` | Claude Code カスタムスキル |
| `Brewfile` | Homebrew パッケージ一覧 |

## シークレット管理

API キーなどのシークレットは `~/.zshenv` に配置し、chezmoi 管理外としています。
