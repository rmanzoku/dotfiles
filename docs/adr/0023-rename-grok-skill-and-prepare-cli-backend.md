---
title: "ADR 0023: Grok skill を `grok` へ改名し将来の CLI backend 置換に備える"
status: accepted
date: 2026-04-20
worked_at: 2026-04-20 02:32 JST
agent_model: GPT-5 Codex
---

# ADR 0023: Grok skill を `grok` へ改名し将来の CLI backend 置換に備える

## Context

`grok-x-research` はすでに X 専用 skill ではなく、汎用の Grok 呼び出し wrapper へ寄っている。
この状態で旧名を残すと、skill の役割より過去の用途を強く想起させる。

また、現時点の backend は xAI Responses API だが、将来 Grok CLI が利用可能になれば、
同じ file-based artifact 契約の裏側を CLI 実装へ差し替えたい。

## Decision

- publisher skill 名と directory 名を `grok` に統一する。
- install manifest と UI metadata は `$grok` を正本として扱う。
- 現在の backend は xAI Responses API のままとする。
- 将来 Grok CLI が実用になった場合は、skill 名や artifact 契約を変えず backend だけを置換する方針とする。

## Consequences

- 利用者は用途ではなく対象そのものの名前で skill を呼べる。
- backend 実装を API から CLI へ差し替えても、orchestrator 側の handoff 変更を最小化できる。
- 過去の `grok-x-research` という名称は歴史的文脈として ADR に残るが、現行の配布正本は `grok` になる。
