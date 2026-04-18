---
title: "ADR 0018: repo 専用の chezmoi knowledge skill を追加する"
status: accepted
date: 2026-04-18
worked_at: 2026-04-18 20:20 JST
agent_model: GPT-5 Codex
---

# ADR 0018: repo 専用の chezmoi knowledge skill を追加する

## Context

このリポジトリでは chezmoi 管理の source state と repo ローカルファイルが混在しており、
`dot_`、`private_`、`symlink_`、`.chezmoiignore`、hidden source directory の解釈を誤ると、
誤った編集や誤説明につながりやすい。

既存の `dotfile-update` は編集ワークフローの skill として有効だが、
それ自体は「なぜその判断になるか」という repo 固有の chezmoi 知識を主目的にはしていない。

また、外部の chezmoi skill には参考になる論点がある一方で、
この repo の運用に合わない前提や手順駆動の内容も含まれる。

## Decision

- repo ローカルに `chezmoi-knowledge` skill を追加する。
- この skill は操作コマンド集ではなく、AI が chezmoi の意味解釈を誤らないための knowledge skill として設計する。
- 正本は `chezmoi-knowledge` skill の reference とし、SKILL.md では誤解しやすい判断点を要約して trigger しやすくする。
- 実際の編集・apply・drift 確認は引き続き `dotfile-update` の責務とする。
- `dotfile-update` から `chezmoi-knowledge` への導線を追加し、意味解釈と操作フローを分離する。

## Consequences

- chezmoi の source/target 誤認や `.chezmoiignore` の誤説明を減らしやすくなる。
- repo ローカル `.claude/skills/` のような非配備ファイルを誤って managed target と説明しにくくなる。
- workflow skill と knowledge skill の責務が分かれ、更新判断がしやすくなる。
- chezmoi の詳細知識は `chezmoi-knowledge` skill の reference を正本として保ち、SKILL.md 側の重複を抑える必要がある。
