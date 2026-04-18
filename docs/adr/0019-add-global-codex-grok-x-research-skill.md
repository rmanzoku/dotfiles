---
title: "ADR 0019: Claude と Codex で共有する Grok X research skill を追加する"
status: accepted
date: 2026-04-18
worked_at: 2026-04-18 14:33 JST
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

- `grok-x-research` を chezmoi 管理の `dot_claude/skills/grok-x-research/` と `dot_codex/skills/grok-x-research/` として追加する。
- 実通信ロジックは `dot_local/bin/executable_grok_x_research` に置き、配備後は `~/.local/bin/grok_x_research` を共有エントリポイントとする。
- request / response の受け渡しは引き続き `.context/` 配下の JSON artifact を正本とする。
- agent ごとの skill は trigger と運用境界に専念し、shared executable を呼ぶ。
- まずは Claude と Codex の shared skill とし、他 AI への同期は行わない。
- 将来複数 agent 間で同一 I/O 契約を共有したくなった場合に限り、MCP 化や他 AI への同期を再検討する。

## Consequences

- Claude と Codex からはどの worktree でも同じ skill 名で Grok 委任を使える。
- xAI API 利用に必要な `XAI_API_KEY` があれば、repo ローカル skill へ依存せず実行できる。
- 実装本体の更新は `~/.local/bin/grok_x_research` 相当の 1 箇所で済む。
- 他 AI から同じ skill 名で呼べる保証はまだなく、必要になった時点で同期方針を再判断する。
