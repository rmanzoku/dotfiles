# ADR 0005: Plan レビューは `.context/` の実ファイル経由で渡す

- Status: Accepted
- Date: 2026-03-12
- Worked At: 2026-03-12 23:46 JST
- Agent Model: GPT-5 Codex

## Context

Plan レビュー運用では、repo ルールとして既存の reviewer テンプレートを変えずに使う必要がある。
一方で、review 対象の plan 本文を shell の file descriptor や標準入力経由で reviewer に渡そうとすると、
子プロセスへ fd が安定して引き継がれない、shell quoting が崩れる、plan に backtick が含まれると here-doc 自体が壊れる、
といった要因で review 実行が失敗することがあった。

実際に、`/dev/fd/*` は親 shell では読めても子プロセスからは `Bad file descriptor` となるケースがあり、
`/dev/stdin` や plan 本文の直接埋め込みも、reviewer 側で空入力や quoting 崩れを引き起こしうる。

このリポジトリでは、一過性ファイルの正規置き場を `.context/` とし、`/tmp` と `/private` は使わない共通ルールがある。
また、今回の修正ではユーザーの明示判断により `dot_qwen/QWEN.md` を更新対象から除外する。

## Decision

- Plan レビュー前に、review 対象の plan 本文を作業 worktree 内の `.context/` に一時ファイルとして保存する。
- reviewer には plan 本文ではなく、その実ファイルパスを `<plan_file_path>` として渡す。
- `dot_codex/AGENTS.md` と `dot_claude/CLAUDE.md` の `# Plan 共通ルール` に、この前提手順と禁止事項を追記する。
- `## レビュー実行テンプレート` のコードブロック本文は変更せず、その直前の説明で安全な使い方を補う。
- `/dev/stdin`、`/dev/fd/*`、plan 本文の here-doc 直書きのような fd / inline 依存の受け渡しは採用しない。
- `dot_qwen/QWEN.md` は今回のユーザー明示判断に従って変更しない。この例外判断はこの ADR に残すが、通常の共通ルール同期方針は維持する。

## Consequences

- shell quoting と fd 継承に依存せず、reviewer が安定して plan 本文を読める。
- テンプレート本文を固定したまま、運用上の失敗要因だけを前提手順で吸収できる。
- `.context/` を正規の一時ファイル置き場として使うルールと整合する。
- `dot_qwen/QWEN.md` は今回未更新のため、Plan ルールの完全同期は別途必要になりうる。
