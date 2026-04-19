---
title: "ADR 0019: Claude と Codex で共有する Grok X research skill を追加する"
status: accepted
date: 2026-04-18
worked_at: 2026-04-20 00:40 JST
agent_model: GPT-5 Codex
---

# ADR 0019: Claude と Codex で共有する Grok X research skill を追加する

## Context

`grok-x-research` は、Claude Code または Codex をオーケストレーターとしつつ、
X 上の調査や投稿角度の抽出だけを Grok に委任するために作成した。

repo ローカル skill としては動作確認できたが、継続利用のたびにこのリポジトリ文脈へ依存させるより、
Claude / Codex のグローバル skill として `~/.claude/skills/` と `~/.codex/skills/` へ常設した方が再利用しやすい。

一方で、実通信ロジックを agent ごとに複製すると保守コストが増える。
`skill-manager` の方針に合わせ、agent 差分は入口 skill に閉じ込め、実装本体は共有コマンドへ寄せる方が扱いやすい。

## Decision

- `grok-x-research` を publisher layout の `skills/grok-x-research/` として追加し、Claude / Codex 共通の source of truth とする。
- 実通信ロジックは skill bundle の `skills/grok-x-research/scripts/executable_grok_x_research` に置く。
- request / response の受け渡しは引き続き `.context/` 配下の JSON artifact を正本とする。
- skill は trigger と運用境界に専念し、bundled script を呼ぶ。
- skill の主体は Grok model への API 委任であり、`x_search` はその実行中に使う証拠収集ツールとして扱う。
- まずは Claude と Codex に `gh skill install --from-local` で配備する shared skill とし、他 AI への同期は行わない。
- 将来複数 agent 間で同一 I/O 契約を共有したくなった場合に限り、MCP 化や他 AI への同期を再検討する。

## Consequences

- Claude と Codex からはどの worktree でも同じ skill 名で Grok 委任を使える。
- xAI API 利用に必要な `XAI_API_KEY` があれば、repo ローカル skill へ依存せず実行できる。
- skill 利用者は「X を検索する helper」ではなく「Grok に調査を委任する skill」として一貫して扱える。
- 実装本体の更新は publisher skill bundle の 1 箇所で済む。
- 他 AI から同じ skill 名で呼べる保証はまだなく、必要になった時点で同期方針を再判断する。
