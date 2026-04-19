---
title: "ADR 0020: external skill は gh skill で管理し repo オリジナル skill だけを dotfiles で管理する"
status: accepted
date: 2026-04-20
worked_at: 2026-04-20 00:40 JST
agent_model: GPT-5 Codex
---

# ADR 0020: external skill は gh skill で管理し repo オリジナル skill だけを dotfiles で管理する

## Context

この dotfiles repo は、Claude Code / Codex を含む global 設定の正本として運用している。

一方で skill には、次の 2 種類が混在する。

- この repo で作成・保守する repo オリジナル skill
- GitHub や外部 ecosystem 由来の external skill

これまでは `skill-manager` が external skill の `adopt` を許容しており、
長期利用や再現性が必要なら git-managed copy に取り込む選択肢を残していた。
しかしこの dotfiles repo では、external skill まで vendoring すると provenance と更新責務が曖昧になり、
repo の境界も膨らみやすい。

すでに `gh skill` が標準 backend として使えるため、
external skill は GitHub-native に管理し、repo オリジナル skill だけを dotfiles 配下で git 管理する方が運用境界を保ちやすい。

## Decision

- この dotfiles repo では、配布する repo オリジナル skill を publisher layout の `skills/` で git 管理する。
- external skill はこの repo に vendoring せず、`gh skill` で install / update / remove する。
- 配布する repo オリジナル skill の global 配備も `gh skill install --from-local` を標準とし、chezmoi で `~/.claude/skills/` や `~/.codex/skills/` へ直接配備しない。
- `npx skills` / skills.sh は既存 install の棚卸し、互換運用、段階移行のための legacy backend に限定する。
- この repo の external/original 境界は `AGENTS.md`、AI 別指示ファイル、ADR で定義し、distributable な `skill-manager` 本体には埋め込まない。
- `grok-x-research` のようなこの repo 起源 skill は external skill ではなく repo オリジナル skill として扱う。

## Consequences

- dotfiles repo の責務は「global 設定の正本」と「repo オリジナル skill publisher source の保守」に絞られる。
- external skill の provenance と更新責務は `gh skill` 側に寄せられる。
- repo オリジナル skill も GitHub-native な preview/install/update 導線に乗せやすくなる。
- `skill-manager` の一般論としては `adopt` が残っても、この repo での扱いは repo-local policy で制約する。
- external skill を repo に取り込みたい場合は、まず `AGENTS.md` と ADR を更新する明示的な方針変更が必要になる。
