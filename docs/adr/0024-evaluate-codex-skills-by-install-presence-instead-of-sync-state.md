---
title: "ADR 0024: skill-manager は Codex skill を sync state ではなく install presence で評価する"
status: accepted
date: 2026-04-20
worked_at: 2026-04-20 09:08 JST
agent_model: GPT-5 Codex
---

# ADR 0024: skill-manager は Codex skill を sync state ではなく install presence で評価する

## Context

`skill-manager` はもともと、Claude 側の skill を Codex に symlink mirror する運用を強く前提にしていた。
そのため Codex 側の状態判定も、`.skill-manager-sync.json` と symlink の整合を基準にしていた。

しかし現在の方針では、external skill / first-party skill ともに `gh skill` を標準 backend として扱う。
`gh skill install` は Codex 側へ valid な skill directory を直接配置できるため、
symlink mirror だけを正常系とみなすと、実際には正常な install が `broken` と誤判定される。

この repo でも `empirical-prompt-tuning`、`grok`、`repo-docs-diagnose` が
Codex に正常配置されているのに、legacy sync 前提の判定のため `broken` 扱いになっていた。

## Decision

- `skill-manager` は Codex skill の状態を `sync` ではなく install presence で判定する。
- Codex 側の状態は次の 4 種とする。
  - `installed`: valid な `SKILL.md` を持つ dir または symlink が存在する
  - `system-preferred`: Codex `.system` skill が同名で優先される
  - `missing`: install が存在しない
  - `broken`: 壊れた symlink、`SKILL.md` 不在、legacy metadata と path の不整合など実体が不正
- `list` JSON は `sync_state` / `codex_synced` / `codex_system` をやめ、`codex_status` を返す。
- `doctor` は `codex_sync` ではなく `codex_presence` を診断し、valid な直置き install を正常扱いする。
- `.skill-manager-sync.json` は Codex 配置の truth source ではなく、legacy mirror metadata として扱う。

## Consequences

- `gh skill install` で入った Codex skill を誤って `broken` 扱いしなくなる。
- Codex 側の health は「mirror されているか」ではなく「使える install があるか」で判断できる。
- legacy mirror metadata が残っていても、valid install の存在を fail にはしない。
- 一方で stale manifest や壊れた symlink は引き続き `broken` として検出できる。
- project scope の `.agents/skills` でも、symlink だけでなく direct install を正常系として扱える。
