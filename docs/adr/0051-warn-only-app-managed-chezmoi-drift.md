---
title: "Warn Only On App-Managed Chezmoi Drift And Make Claude Settings Private"
date: 2026-07-07
agent_model: "Claude Fable 5 (claude-fable-5) / OpenAI Codex GPT-5.5 (dot_* 編集担当)"
status: "accepted"
---

# ADR 0051: app 管理ドリフトは警告のみとし、Claude settings を private 化する

## Context

pre-commit hook（`.claude/hooks/chezmoi-pre-commit-hook`）は `chezmoi diff` が非空だと `git commit` をブロックする。2026-07-07 の commit 作業で、アプリが target を書き換えることに起因するドリフトが commit を繰り返し妨げる構造が確認された。

- `~/.codex/config.toml`: Codex Desktop が `[mcp_servers.node_repl]`、browser-use 環境変数（アプリバージョン固定値を含む）等を実行時に注入する。source へ取り込むとアプリ更新のたびに churn し、`chezmoi apply` で消すとアプリ再起動まで注入設定が失われる。source は template（`private_config.toml.tmpl`）のため `chezmoi re-add` による取り込みは template 変数を破壊し不可。
- `~/.claude/settings.json`: Claude Code アプリが mode 0600 で書き戻すため、source 既定の 0644 と恒常的な mode ドリフトになる。
- `~/.ssh/config`: Colima が `Include ~/.colima/ssh_config` を注入していた。ADR 0009 の設計どおり unmanaged な `~/.ssh/config.local` へ移設したが、Colima は managed 側へ再注入するため、恒久対策として machine-local の `~/.colima/default/colima.yaml` で `sshConfig: false` を設定し、Colima による `~/.ssh/config` 書き換え自体を停止した（Include は config.local 側で維持）。
- `~/.gemini/settings.json`: Gemini CLI が末尾改行なしで再保存する churn を観測（内容差分なし）。再発が続く場合は許容リスト追加を再検討する。

また、アプリ側の変更が正当な場合（Claude plugin 有効化、`gh auth setup-git` の credential helper）は source へ取り込む方向で解消した。

## Decision

1. **hook に app 管理ドリフト許容リストを導入する。** `.claude/hooks/chezmoi-pre-commit-hook` の `APP_MANAGED_DRIFT_ALLOWLIST`（glob 可。現在 `.codex/config.toml` と `.codex/automations/*/automation.toml`）に該当する target のドリフトは警告表示のみとし、commit をブロックしない。それ以外のファイルは従来どおりブロックする。許容リストの追加・削除は本 ADR の更新を伴うこと。automation.toml は Codex Desktop が `target = { type = "project", project_id = "<絶対パス>" }` などの machine-local 実行バインディングを書き込み、prompt 文字列も Desktop のシリアライザ表現で再保存されるため、config.toml と同じ app 管理扱いとする。
2. **Codex Desktop が注入する app 管理セクションは source へ取り込まない。** machine-local runtime state として扱い、source 側の変更を配備する際は `chezmoi apply` の一時的な注入設定喪失（アプリ再起動で再注入）を許容する。
3. **`dot_claude/settings.json` を `dot_claude/private_settings.json` へ昇格する。** target `~/.claude/settings.json` の管理状態 mode を 0600 とし、アプリの書き戻し挙動と一致させて mode ドリフトを解消する。
4. **判断基準の整理**: target 側の外部変更は、(a) ユーザーの選択を反映した正当な状態（plugin 有効化、credential helper 等）なら source へ取り込む、(b) アプリの runtime 注入なら取り込まず許容リストまたは unmanaged local file（ADR 0009 方式）で扱う、(c) machine-local の path/version 固定値を含むものは原則 (b) とする。

## Consequences

- Desktop アプリの更新・起動だけで commit がブロックされる事象がなくなる。許容リスト対象のドリフトも hook が警告表示するため観測性は維持される。
- `.codex/config.toml` のドリフトは静かに滞留し得るが、source 変更を配備する際の `chezmoi apply` 実行時に解消される。取り込み・復元の判断は `scripts/chezmoi-drift` の明示実行に委ねる。
- `modify_` script による部分管理（app 注入セクションを保存しつつ管理キーを強制）は、TOML マージと template の複合で実装・保守コストが高いため今回は採用しない。許容リスト運用で不足が観測されたら再検討する。
- 関連 ADR: 0009（ssh local include）、0050（指示ファイル単一正本化）。
