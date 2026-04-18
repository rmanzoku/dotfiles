---
title: "ADR 0015: skill-manager は gh skill を標準 backend とし段階移行を支援する"
status: accepted
date: 2026-04-03
worked_at: 2026-04-18 15:45 JST
agent_model: GPT-5 Codex
---

# ADR 0015: skill-manager は skills.sh を backend にし agent 差分を前提に扱う

## Context

`skill-manager` は当初、Claude Code 中心で、Codex への同期や parity を強く意識した自前管理スキルとして設計した。
しかし現在は agent の種類が増え、Claude にだけ入れる skill、Codex `.system` と衝突する skill、
外部 ecosystem から `npx skills add` で trial install する skill など、agent ごとの差分を前提に扱う方が自然になっている。

また、skills.sh と `npx skills` CLI が外部 skill の discovery / install / update の共通 backend として実用可能になり、
それに合わせて `skill-manager` も skills.sh 中心の整理に寄せていた。

2026-04-16 には GitHub CLI `v2.90.0` で `gh skill` が public preview として追加された。
これにより、GitHub-native な install / preview / update / publish と provenance 記録を `gh` 本体で扱えるようになった。
一方で既存の `npx skills` / skills.sh ワークフローも既に利用されており、全リポジトリを一括では切り替えられない。
そのため、新規導入は `gh skill` を標準にしつつ、既存資産は段階移行できる補助コマンドを併設する方針が必要になった。

## Decision

- `skill-manager` の標準 backend は `gh skill` とする。
- 新規の discovery / install / update / publish は、原則 `gh skill` を使う。
- `npx skills` / skills.sh は既存 install の棚卸し、互換運用、段階移行のための legacy backend として残す。
- 既存の `skills.sh` install から `gh skill install` への移行は、非破壊の移行コマンド生成を挟んで段階的に行う。
- `skill-manager` は parity manager ではなく、provenance と agent 差分を扱う policy layer とする。
- skill の状態は少なくとも次で把握する。
  - provenance: `skills-cli`, `vendored`, `manual`, `plugin`
  - scope: `global`, `project`
  - installed agents
- Claude と Codex の完全一致は前提にしない。
- `sync codex` は legacy 的に残してもよいが、`mirror` したい skill だけに限定する。
- 長期利用、ローカル修正、再現性が必要な skill は `adopt` して git-managed copy に取り込む。

## Consequences

- 外部 skill の install/update/publish を GitHub-native に寄せられる。
- `npx skills add` と `gh skill install` を新規導入と legacy 移行で使い分ける必要がある。
- `gh skill` により GitHub-native な provenance と publish 手順を扱える。
- 一括移行ではなく、生成した移行コマンドを使う repo 単位の段階移行が前提になる。
- agent ごとの差分を error ではなく inventory data として扱える。
- vendored skill と trial install を区別しやすくなる。
- telemetry は既定で無効化して使う運用を維持する必要がある。
- Claude marketplace plugin と skills.sh skill は別レイヤとして整理し続ける必要がある。
