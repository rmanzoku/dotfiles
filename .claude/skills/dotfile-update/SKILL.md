---
name: dotfile-update
description: >
  chezmoi 管理の dotfiles リポジトリで dotfile を追加・変更・削除するためのワークフロースキル。
  `dot_*` ファイル、`.chezmoiignore`、`Brewfile`、共通ルールファイル
  （`dot_claude/CLAUDE.md`、`dot_codex/AGENTS.md`、`dot_qwen/QWEN.md`）の
  編集を依頼された場合に必ず使用すること。
  「zshrc を変更して」「gitconfig に設定を追加して」「Brewfile にパッケージを追加して」
  「共通ルールを更新して」のような依頼はすべてこのスキルの対象。
  CLAUDE.md でこのスキルの使用が強制されているため、dotfile 関連の変更では必ずトリガーすること。
---

# dotfile-update

chezmoi で管理された dotfiles リポジトリの更新ワークフロー。
このリポジトリでは dotfile の変更は必ずこのスキルのワークフローに従う。

## ワークフロー

### 1. ソースファイルの編集

chezmoi のソースファイル（`dot_*`）を直接編集する。
ホームディレクトリの実ファイルではなく、リポジトリ内のソースを編集すること。

対応表:
- `~/.zshrc` → `dot_zshrc`
- `~/.gitconfig` → `dot_gitconfig`
- `~/.config/...` → `dot_config/...`
- `~/.claude/CLAUDE.md` → `dot_claude/CLAUDE.md`
- `~/.codex/AGENTS.md` → `dot_codex/AGENTS.md`
- `~/.qwen/QWEN.md` → `dot_qwen/QWEN.md`

chezmoi の命名規則:
- `dot_` → `.`（ドットファイル）
- `executable_` → 実行権限付きファイル
- `.tmpl` → chezmoi テンプレート（`{{ .chezmoi.homeDir }}` 等が使える）

### 2. 共通ルールの同期

`dot_claude/CLAUDE.md`、`dot_codex/AGENTS.md`、`dot_qwen/QWEN.md` は共通ルールセクションを共有している。
いずれかの共通ルール部分を変更した場合、残りの 2 ファイルにも同じ変更を反映すること。

共通ルールセクションの識別: `# 共通ルール` 見出し配下の箇条書き。

Claude Code 固有ルール（`# Claude Code 固有ルール` 以降）は `dot_claude/CLAUDE.md` のみに存在し、
同期対象外。

### 3. chezmoi apply の実行

編集が完了したら、変更を実機に反映する:

1. `chezmoi diff` で差分を確認し、ユーザーに提示する
2. ユーザーの確認を得てから `chezmoi apply` を実行する（確認なしに自動実行しない）
3. chezmoi が未インストールの場合は `brew install chezmoi` を案内して停止する

### 4. ドリフト確認

apply 後に差分がないことを確認する:

```bash
scripts/chezmoi-drift
```

「差分はありません」と出力されれば完了。

### 5. `.chezmoiignore` の管理

新しいファイルやディレクトリを追加する際、以下に該当するものは `.chezmoiignore` に追記する:
- キャッシュ・ログ・セッション等のトランジェントデータ
- マシン固有の状態ファイル
- リポジトリ専用ファイル（`setup.sh`、`scripts/` 等、既に登録済み）

## 注意事項

- `Brewfile` の更新後は `brew bundle` の実行は不要（パッケージインストールはユーザーが別途行う）
- シークレット（API キー等）は `~/.zshenv` に配置し、chezmoi 管理外とする。リポジトリにコミットしない
- pre-commit hook（`.claude/hooks/chezmoi-pre-commit-hook`）がコミット前にドリフトを自動検出する。ドリフトがあるとコミットがブロックされるため、必ず apply まで完了させること
