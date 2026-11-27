---
title: "ADR 0086: Codex の既定モデルを GPT-6.2 にし、Fast を既定にする"
status: accepted
date: 2026-11-18
worked_at: 2026-11-18 JST
agent_model: "Claude Opus 5.5 (claude-opus-5-5)"
---

# Context

2026-11-18 の Codex model catalog（`~/.codex/models_cache.json`）に `gpt-6.2-sol` と `gpt-6.2-astra` が追加された。利用者から、Astra と Sol の既定を 6.2 に変え、Fast モードを既定で有効にするよう指示があった。

ADR 0076 では、Codex parent の既定を `gpt-6.1-sol` / `medium`、`tech` / `biz` を `gpt-6-astra` / `high` とし、`service_tier` は `default` だった。

# Decision

1. Codex parent の既定を `gpt-6.2-sol` にする。effort は `medium` のまま変えない。
2. agent 定義の Sol と Astra を 6.2 に置き換える。`cleaner` / `personal` は `gpt-6.2-sol`、`tech` / `biz` は `gpt-6.2-astra` とし、effort は変えない。
3. `service_tier` を `"fast"` にして、Fast を既定で有効にする。

# Evidence

- catalog では、両モデルとも Fast が service tier id `priority` として提供されている（2x speed、increased usage）。
- openai/codex の `ServiceTier::from_request_value` は `"fast"` と `"priority"` をどちらも Fast として受け付ける。TUI で切り替えたときに config へ保存される値は `"fast"` なので、それに合わせた。
- Codex は `service_tier` の値を設定の読み込み時に検証しない。不正な値を書いても起動時のエラーにならないため、値はソースで確認した。

# Consequences

- Fast は usage の消費が増える。費用効率の方針（作業を Codex に任せる）と相反しうるため、消費が問題になったら `service_tier` を `"default"` に戻す。
- `codex-runner` の prompt profile 判定（`gpt-6` の正規表現）は 6.2 も GPT-6 として扱うので、runner の変更は不要。skill 本文のモデル名の列挙だけを更新した。
- ADR 0076 のモデル配分のうち、Sol と Astra の世代だけを置き換える。役割ごとの配分の考え方は変えない。
