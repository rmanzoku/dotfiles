# ADR 0006: Gemini CLI の baseline 設定を dotfiles で管理する

- Status: Accepted
- Date: 2026-03-13
- Worked At: 2026-03-13 14:00 JST
- Agent Model: GPT-5 Codex

## Context

この dotfiles リポジトリでは、Claude、Codex、Qwen についてはグローバル指示ファイルとクライアント設定ファイルを source state として管理している。
一方、`gemini-cli` はすでに実機へ導入済みでログインも完了しているが、`~/.gemini/settings.json` は手動管理のままで、`GEMINI.md` も未整備だった。

Gemini には `save_memory` と `GEMINI.md` による永続コンテキスト機能があるが、このリポジトリの共通方針では、worktree / セッションをまたいで再利用すべき指示は Memory ではなく git 管理ファイルへ置く。
そのため、Gemini でも他 AI と同じく、グローバル instruction と baseline settings は dotfiles 管理へ移し、machine-specific state は非管理に分ける必要がある。

また、Gemini CLI は workspace 配下の `GEMINI.md` / `AGENTS.md` を親ディレクトリ方向も含めて探索し、project context として自動で連結する。
このリポジトリでは chezmoi source state として `dot_gemini/` や `dot_codex/` を保持しているため、除外しないと source 用ファイルまで Gemini の project context に混入し、指示が重複する。

## Decision

- `dot_gemini/GEMINI.md` を追加し、Gemini 向けのグローバル共通ルールと Plan 共通ルールを管理する。
- `dot_gemini/settings.json` を追加し、Gemini CLI 0.33.0 向けの baseline settings を管理する。
- 運用ルールとして、グローバル指示は `~/.gemini/GEMINI.md` に置き、repo / project 固有指示は原則 repo 直下の `AGENTS.md` に集約する。
- baseline settings には次を含める。
  - `general.defaultApprovalMode = auto_edit`
  - `context.fileName = ["AGENTS.md", "GEMINI.md"]`
  - `mcpServers.pencil`
  - `security.folderTrust.enabled = true`
  - 既存実機状態の維持に必要な `security.auth.selectedType = oauth-personal`
  - `ui.theme = Default Light`
- `~/.gemini/` 配下の machine-specific state は原則 `.chezmoiignore` で非管理にする。
  - 例: `oauth_creds.json`, `mcp-oauth-tokens-v2.json`, `trustedFolders.json`, `history/`, `tmp/`, `projects.json`
- repo ルートに `.geminiignore` を置き、chezmoi source 用の `dot_gemini/` と `dot_codex/` を Gemini の project context から除外する。
- Gemini 固有の skills / extensions / hooks / commands は今回は managed 化せず、baseline config 導入までに留める。
- `.claude/skills/dotfile-update/SKILL.md` の AI 間対応表に Gemini を追加し、Gemini state を原則 ignore とする運用を明文化する。

## Consequences

- Gemini でも横断運用ルールと baseline settings を再現可能な形で配備できる。
- 認証トークンや trust 記録など、マシン依存の state を誤ってコミットしにくくなる。
- `AGENTS.md` を Gemini の正規の repo 指示ファイルとして扱うことで、既存 repo の agent instructions をそのまま再利用でき、repo ごとに `GEMINI.md` を増やさずに済む。
- `.geminiignore` により、chezmoi source 用ディレクトリが Gemini の project context に混入せず、グローバル `~/.gemini/GEMINI.md` と repo 直下の正規 instruction だけを読み込ませやすくなる。
- Gemini の拡張機能群は今回は非管理のため、将来的に skills / extensions を本格管理する場合は別 ADR で境界を再定義する必要がある。
