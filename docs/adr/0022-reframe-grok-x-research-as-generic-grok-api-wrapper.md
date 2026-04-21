---
title: "ADR 0022: grok-x-research を汎用 Grok API ラッパーとして再定義する"
status: superseded
date: 2026-04-20
worked_at: 2026-04-20 02:32 JST
agent_model: GPT-5 Codex
---

# ADR 0022: grok-x-research を汎用 Grok API ラッパーとして再定義する

Superseded by [ADR 0023](./0023-rename-grok-skill-and-prepare-cli-backend.md).

## Context

`grok-x-research` は当初、X 調査専用の orchestration skill として設計した。
ただし実体は xAI Responses API を叩く script であり、X 固有の入出力契約や補助ロジックを skill 側に持ち込みすぎると、
単純に Grok を呼びたい用途でも毎回過剰な artifact 形を要求する。

publisher skill として継続配布するなら、skill の責務は「再読可能な file-based handoff を保った薄い API ラッパー」に寄せた方が再利用しやすい。

## Decision

- `grok-x-research` の skill ID と配置は維持する。
- skill の役割は X 調査専用 orchestration ではなく、xAI Responses API を呼ぶ汎用 Grok ラッパーへ変更する。
- request artifact は `task` と `request` を正本とし、`request` の中身は xAI Responses API の payload をほぼそのまま受け取る。
- bundled script は payload の最小検証、既定 model の補完、API 呼び出し、response artifact 保存だけを担当する。
- X 特化の schema 強制、source 抽出前提、投稿下書き前提は skill 本体から外す。

## Consequences

- Orchestrator は X 調査以外でも同じ skill を再利用できる。
- X 検索や Web 検索を使いたい場合は、request artifact 内の `tools` として明示する方式に変わる。
- response artifact は raw API response を保持するため、後段での独自解析や再処理がしやすくなる。
- skill 名は過去互換のため残るが、意味は「Grok API wrapper」に寄るので、利用時は名前より `SKILL.md` の契約を正本として扱う。
