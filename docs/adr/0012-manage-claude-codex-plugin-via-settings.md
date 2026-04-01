---
title: "ADR 0012: Claude Code の Codex plugin は settings で marketplace と enabled 状態を管理する"
status: accepted
date: 2026-04-01
worked_at: 2026-04-01 14:35 JST
agent_model: GPT-5 Codex
---

# ADR 0012: Claude Code の Codex plugin は settings で marketplace と enabled 状態を管理する

## Context

Claude Code で `openai/codex-plugin-cc` を常用できるようにしたい。
この plugin は marketplace 経由で導入し、README でも `claude plugin marketplace add openai/codex-plugin-cc` と
`claude plugin install codex@openai-codex` を案内している。

一方、この dotfiles リポジトリでは `~/.claude/plugins/` を transient data として `.chezmoiignore` で除外している。
そのため install cache や marketplace metadata を source state に含めると、マシン固有状態まで git 管理してしまう。

## Decision

- 永続化するのは `~/.claude/settings.json` に相当する source である `dot_claude/settings.json` のみとする。
- `extraKnownMarketplaces` に `openai-codex` を追加し、source は GitHub repo `openai/codex-plugin-cc` とする。
- `enabledPlugins` に `codex@openai-codex` を追加し、Claude Code のグローバル設定として有効化する。
- `~/.claude/plugins/` 配下の install cache、marketplace checkout、installed metadata は transient data のままとし、chezmoi では管理しない。
- 実機で plugin 本体が未導入の場合は、settings 反映後に `claude plugin install codex@openai-codex` を個別実行して cache を生成する。

## Consequences

- marketplace 登録と enabled 状態は dotfiles で再現できる。
- install cache を git 管理しないため、マシン固有の plugin 実体や更新時刻を持ち込まずに済む。
- 新しい環境では `chezmoi apply` 後に plugin install が 1 回必要になる。
