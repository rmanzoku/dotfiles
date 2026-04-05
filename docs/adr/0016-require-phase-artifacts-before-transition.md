---
title: "ADR 0016: Phase / Step 遷移前に .context artifact を必須化する"
status: accepted
date: 2026-04-05
worked_at: 2026-04-05 21:05 JST
agent_model: GPT-5 Codex
---

# ADR 0016: Phase / Step 遷移前に `.context` artifact を必須化する

## Context

Plan 合意や Skill 定義に明示された Phase / Step が、会話上の合意やモデル内部の判断だけでスキップされる事例があった。
既存ルールでは Plan レビュー前の `.context/` 実ファイル化や、AI 間受け渡しのファイル経由は定義されていたが、
「Phase / Step をまたぐために何が揃っていればよいか」は統一されていなかった。

このため、Plan、Skill、レビュー、実装、検証のいずれでも、
中間成果物が残っていないまま次段階へ進み、再読・再レビュー・別 Agent 引き継ぎ・監査が難しくなる余地があった。

## Decision

- Phase / Step を持つ作業では、各 Phase / Step の完了前に `.context/` 配下へ artifact を保存することを必須にする。
- 次の Phase / Step へ進む条件を、対応する artifact の生成に固定する。
- artifact の初期必須項目は `task`、`phase_or_step`、`created_at` とし、Markdown は Front Matter、JSON は同名キーで保持する。
- artifact の推奨命名は `.context/<task-or-date>/<nn>-<phase-name>.(md|json)` とし、同名更新時は最新更新時刻のファイルだけを有効扱いにする。
- 非 Phase 作業は対象外とするが、artifact gate を明示的にバイパスする単発例外は `.context/single-step/<task>.json` に限定する。
- Phase / Step 遷移の最小原則は repo の `AGENTS.md` を正本とし、Skill 固有の required artifact は `SKILL.md` を正本とする。
- `AGENTS.md` と `SKILL.md` が競合する場合は、`SKILL.md` をその Skill 実行中の具体契約として優先し、`AGENTS.md` は下限ルールとして常に適用する。
- Hook は補助 enforcement に限定し、自然言語の意味理解や「本当に完了したか」の判定は持たせない。
- Claude Code では `dot_claude/settings.json` と repo ローカル `.claude/settings.json`、Codex では repo ローカル `.codex/hooks.json` を使って artifact gate を補助する。
- Codex の `~/.codex/hooks.json` は個人通知などのグローバル用途に限定し、repo enforcement は載せない。

## Consequences

- Plan、Skill、レビュー、実装、検証の各段階で、中間成果物が `.context/` に残り、再読・再レビュー・引き継ぎがしやすくなる。
- Hook は artifact の有無と最小スキーマだけを検査するため、過度な意味解析による誤判定を避けやすい。
- 単発作業の例外を明示ファイルに限定することで、バイパス条件を監査可能にできる。
- 初期導入では「artifact の存在確認」までに留めるため、Phase 完了の意味的妥当性は reviewer と Skill の設計で補完する必要がある。
