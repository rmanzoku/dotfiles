---
title: "ADR 0026: skill-manager は Codex plugin inventory と health check も扱う"
status: accepted
date: 2026-04-20
worked_at: 2026-04-20 10:12 JST
agent_model: GPT-5 Codex
---

# ADR 0026: skill-manager は Codex plugin inventory と health check も扱う

## Context

Codex 0.121.0 では marketplace と plugin cache が実装されており、
実際の skill availability には direct install だけでなく plugin-provided skill も含まれる。

このため `skill-manager` が direct install と Claude marketplace だけを見ていると、
Codex 側で実際に使える機能の棚卸しが不完全になる。

また Codex CLI には現時点で `marketplace list` 相当の inventory コマンドがなく、
実状態を確認するには少なくとも次を読む必要がある。

- `~/.codex/config.toml`
- `~/.codex/plugins/cache/*/*/*/.codex-plugin/plugin.json`
- `~/.codex/.tmp/bundled-marketplaces/*/.agents/plugins/marketplace.json`

## Decision

- `skill-manager` の責務に Codex plugin inventory と health check を含める。
- Codex plugin の control plane は `~/.codex/config.toml` と marketplace metadata とみなす。
- Codex plugin の realized state は `~/.codex/plugins/cache` とみなす。
- plugin が提供する skill は `codex_plugin` source として source-aware inventory に含める。
- Codex plugin は direct install skill と同一視せず、別 source として collision 判定に載せる。

## Consequences

- `list` は Codex plugin の `enabled` / `configured` / `cached` / `available` を返せる。
- `doctor` は Codex plugin config, cache, `skills`, `apps`, `mcpServers` の欠落を検出できる。
- Codex plugin 由来 skill と direct install skill の重名を区別して扱える。
- plugin lifecycle は `gh skill` / `skills.sh` の lifecycle と混線させずに管理できる。
