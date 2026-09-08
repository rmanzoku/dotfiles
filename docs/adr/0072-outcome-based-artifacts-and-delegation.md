---
title: "ADR 0072: artifact と委譲を成果と境界に基づいて選ぶ"
status: accepted
date: 2026-09-08
worked_at: "2026-09-08 JST"
agent_model: "gpt-5.6-terra"
reviewer_model: "gpt-6-astra"
---

# ADR 0072: artifact と委譲を成果と境界に基づいて選ぶ

## Context

グローバル指示と `dotfile-update` は、Phase / Step の名称だけで artifact を必須とし、
orchestration evaluator は親による concrete task execution を一律に禁じていた。これらは、
既存契約内で一つの owner に閉じる通常の修正にも、不要な中間記録と委譲を要求していた。

## Decision

artifact は owner / context 間の handoff、外部または不可逆操作、未解決の永続判断、証拠再利用または
PR に必要な identity、利用者指定 audit に必要な場合だけ作る。Phase / Step の名称は artifact の根拠にしない。
artifact を作る場合の既存初期メタデータである `task`、`phase_or_step`、`created_at` は維持する。

委譲は並列化、context 隔離、専門性、必要な独立性で判断する。既存契約内で同じ owner に閉じる具体作業は、
親が直接実行できる。Phase 名、role 名、同じ model/provider への解決だけで委譲を強制しない。

この dotfiles repository では durable rationale を `docs/adr/` に置くが、グローバル指示は各 repository の
正規 ADR 配置を参照し、特定の path を強制しない。

command 正規表現または plan text を根拠に artifact を強制していた phase artifact hook と、その Claude / Codex
hook 登録を削除する。新しい validator は作らない。

## Consequences

共通ルール、Codex 固有 validator の説明、`dotfile-update`、`agent-orchestration-evaluator` を同じ判断軸に揃える。
artifact を使う既存の Skill または repository 契約は、その具体的な必要性を保持できる。
