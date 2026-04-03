---
title: "ADR 0015: skill-manager は skills.sh を backend にし agent 差分を前提に扱う"
status: accepted
date: 2026-04-03
worked_at: 2026-04-03 11:45 JST
agent_model: GPT-5 Codex
---

# ADR 0015: skill-manager は skills.sh を backend にし agent 差分を前提に扱う

## Context

`skill-manager` は当初、Claude Code 中心で、Codex への同期や parity を強く意識した自前管理スキルとして設計した。
しかし現在は agent の種類が増え、Claude にだけ入れる skill、Codex `.system` と衝突する skill、
外部 ecosystem から `npx skills add` で trial install する skill など、agent ごとの差分を前提に扱う方が自然になっている。

また、skills.sh と `npx skills` CLI が外部 skill の discovery / install / update の共通 backend として実用可能になった。
この段階で remote skill の registry と installer を自前で持ち続けるより、外部 backend に寄せて、
ローカルでは inventory、policy、adoption を扱う方が保守しやすい。

## Decision

- `skill-manager` の primary backend は `skills.sh` CLI とする。
- 外部 skill の discovery / install / remove / update は原則 `SKILLS_TELEMETRY_DISABLED=1 npx --yes skills ...` を使う。
- `skill-manager` は parity manager ではなく、provenance と agent 差分を扱う policy layer とする。
- skill の状態は少なくとも次で把握する。
  - provenance: `skills-cli`, `vendored`, `manual`, `plugin`
  - scope: `global`, `project`
  - installed agents
- Claude と Codex の完全一致は前提にしない。
- `sync codex` は legacy 的に残してもよいが、`mirror` したい skill だけに限定する。
- 長期利用、ローカル修正、再現性が必要な skill は `adopt` して git-managed copy に取り込む。

## Consequences

- 外部 skill の install/update ロジックを自前実装し続ける負担が減る。
- agent ごとの差分を error ではなく inventory data として扱える。
- vendored skill と trial install を区別しやすくなる。
- telemetry は既定で無効化して使う運用を維持する必要がある。
- Claude marketplace plugin と skills.sh skill は別レイヤとして整理し続ける必要がある。
