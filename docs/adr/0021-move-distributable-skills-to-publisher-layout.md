---
title: "ADR 0021: 配布 skill は publisher layout の skills/ を正本とし gh skill --from-local で配備する"
status: accepted
date: 2026-04-20
worked_at: 2026-04-20 01:05 JST
agent_model: GPT-5 Codex
---

# ADR 0021: 配布 skill は publisher layout の `skills/` を正本とし `gh skill --from-local` で配備する

## Context

この repo では配布用の first-party skill を `dot_claude/skills/` や `dot_codex/skills/` に置いてきた。
しかしこの配置は、chezmoi で直接グローバル配備する layer と、GitHub-native な skill publisher layer を混同しやすい。

実際に `skill-manager` のような配布 skill に repo 固有 policy が混入しやすく、
`grok-x-research` でも Claude と Codex で二重の source of truth が生じていた。

一方で `gh skill install --from-local` が使えるため、repo 内に publisher layout を持てば、
preview/install/update/publish の導線を third-party skill と同じ形へ揃えられる。

## Decision

- 配布する first-party skill の正本は `skills/<name>/` とする。
- 現在配布している `skill-manager`、`repo-docs-diagnose`、`grok-x-research` を `skills/` 配下へ集約する。
- `dot_claude/skills/` と `dot_codex/skills/` の配布コピーは撤去する。
- global 配備の標準経路は `gh skill install --from-local <repo-root> <skill> --agent <agent> --scope user` とする。
- `grok-x-research` の実装本体は `~/.local/bin/grok_x_research` ではなく、skill bundle の `scripts/` に同梱する。
- repo ローカル専用 skill は引き続き `.claude/skills/` に置き、publisher skill と混在させない。
- 新しいマシン向けの復元情報は当面 script 化せず、repo の docs-only install manifest として保持する。
- upstream publisher layout を持たない third-party external skill は、docs-only manifest に `fetch + gh skill install --from-local` 手順を記録して扱う。

## Consequences

- 配布 skill であることが layout だけで明確になり、repo 固有 policy との混線が減る。
- `gh skill preview/install/update/publish` の導線を first-party / third-party で揃えやすくなる。
- `grok-x-research` は Claude/Codex の二重管理を解消し、単一の publisher source に集約できる。
- chezmoi は配布 skill の実体配備ではなく、policy と install decision の正本として整理される。
- 将来 `gh` 側に manifest 機能が入ったときは、docs-only install manifest からの移行を判断できる。
- upstream 非 publisher の third-party skill も、例外手順を docs-only manifest に残すことで再現可能性を保てる。
