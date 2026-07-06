---
title: "Single-Source Global Agent Instruction Rules Via Chezmoi Templates"
date: 2026-07-07
agent_model: "Claude Fable 5 (claude-fable-5) / OpenAI Codex GPT-5.5 (dot_* 編集担当)"
status: "accepted"
---

# ADR 0050: グローバル AI 指示ファイルの共通ルールを chezmoi template で単一正本化する

## Context

docs-evaluator によるリポジトリ評価（`.context/docs-evaluator/20260707-chezmoi-dotfiles/report.md`、セッション artifact）で、グローバル配備される AI 指示ファイルについて以下が確認された。

- `dot_codex/AGENTS.md`・`dot_gemini/GEMINI.md`・`dot_qwen/QWEN.md` が「共通ルール」を手動複製しており、確認済みドリフトが 4 点存在した（rg-first ルールが Codex 版に欠落、Phase / Step artifact ルールが Gemini / Qwen 版に欠落、Plan 共通ルールが Qwen 版に欠落、Qwen 版 ADR ルールの「作業リポジトリの」修飾語欠落）。どの差分が意図的かを示すマーカーはなかった。
- 管理外の `~/CLAUDE.md`（2026-03-12 付）・`~/AGENTS.md`（2026-06-10 付）・`~/README.md` が home に手動残置され、`~/CLAUDE.md` は全プロジェクトの Claude セッションに読み込まれていた。`.chezmoiignore` はこれらのファイル名を「Repo-only files (not deployed to home)」と宣言している。
- `tech` レビュー観測点の長大 bullet が、ADR 0048 での code-evaluator rubric・tech agent 定義への織り込み後も `dot_codex/AGENTS.md` に残り、同一ドクトリンが 3 箇所に存在していた。
- Freee / Google の fallback 禁止ポリシーが `README.md` のみに存在し、agent が読む AGENTS 系から到達できなかった。
- ADR 番号 0042 が 2 ファイルで重複していた（2026-06-27 付の grok ADR が後発の誤採番）。

## Decision

1. **共通ルールの単一正本化**: `.chezmoitemplates/common-rules.md` を新設し、`# 共通ルール` と `# Plan 共通ルール` の正本とする。`dot_codex/AGENTS.md.tmpl`・`dot_gemini/GEMINI.md.tmpl`・`dot_qwen/QWEN.md.tmpl` は `includeTemplate "common-rules.md"` で取り込み、AI 固有セクションだけを各ファイルに持つ。「継続的な指示の保存先」は `localDir` / `globalFile` パラメータで AI 別に差し替える。`dot_claude/CLAUDE.md` は従来どおり配備後の `~/.codex/AGENTS.md` を import する。
2. **ドリフト解消は superset 方式**: 欠落 4 点はドリフトによる漏れと判断し、全エージェントが共通ブロック全文（rg-first、Phase / Step artifact ルール、Plan 共通ルール込み）を受け取る。根拠: home 残置コピーの日付から、Gemini / Qwen 版は古いスナップショット同期のまま放置されたと推定した。
3. **tech 観測点の正本一本化**: tech agent 定義は非公開のため、公開正本は code-evaluator スキルの `references/evaluation-rubric.md`（Future-context fit）とし、`dot_codex/AGENTS.md.tmpl` の該当 bullet は参照に置換して再掲しない。
4. **fallback 禁止ポリシーの移設**: Freee / Google の fallback 禁止（別 principal / company / profile への自動切替禁止）を共通ルールの bullet として追加し、`README.md` は正本へのポインタに置換する。
5. **管理外 home ファイルの削除**: `~/CLAUDE.md`・`~/AGENTS.md`・`~/README.md` を削除する（ユーザー承認済み）。グローバル指示は `~/.claude/`・`~/.codex/` 以下の chezmoi 配備ファイルだけを読ませる。
6. **ADR 0042 重複解消**: 後発誤採番の grok ADR を `0049-reset-grok-cli-runner-to-grok-build.md` へリネームする（外部参照 0 件を確認済み）。
7. **関連文書の追随**: `dotfile-update` スキルの共通ルール同期手順を template 正本方式へ書き換え、`README.md`・`AGENTS.md`・`docs/README.md` の source 対応参照を `.tmpl` 名へ更新する。あわせて `dotfile-update` に残っていた「シークレットは `~/.zshenv.local` に配置」という正本ルール矛盾記述を 1Password 方式へ修正する。

## Consequences

- 共通ルールの変更は `.chezmoitemplates/common-rules.md` の 1 箇所編集になり、AI 間ドリフトは原理的に発生しなくなる。意図的な AI 差分は各 `.tmpl` の固有セクションに限定され、差分の意図が構造で表現される。
- Gemini / Qwen は Phase / Step artifact ルールと Plan 共通ルールを新たに受け取る（挙動変更）。
- `dot_*` 側の実装は Codex が担当した（`dot_*` 編集禁止ルールは維持。委譲記録: `.context/20260707-instruction-single-source/codex-run/`、セッション artifact）。
- render 検証で 3 target とも意図した差分のみであることを確認済み。`chezmoi apply` はユーザー確認後に実施する。
- ADR 番号は 0049 まで使用済みとなり、本 ADR が 0050 を使用する。
