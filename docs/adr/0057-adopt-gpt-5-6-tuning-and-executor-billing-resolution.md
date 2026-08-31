---
title: "ADR 0057: GPT-5.6 tuning skill を新設し、サブスク標準採用と executor/billing 分離解決を導入する"
status: accepted
date: 2026-07-25
worked_at: 2026-07-25 11:55 JST
agent_model: Claude Fable 5 (claude-fable-5)
---

# ADR 0057: GPT-5.6 tuning skill を新設し、サブスク標準採用と executor/billing 分離解決を導入する

> Fable の task-data authorization と credit floor は [ADR 0069](./0069-normalize-ai-cli-runner-data-boundaries.md) により一部更新された。executor/billing 分離と per-run budget contract は維持する。

## Context

GPT-5.6(2026-07-09 リリース、`gpt-5.6-sol` / `gpt-5.6-terra` / `gpt-5.6-luna`)は ADR 0054 で Codex の role 別既定に採用済みだが、対応する tuning skill がなく、`codex-cli-runner` の prompt profile も GPT-5.5 までだった。公式ガイダンスは 5.5 の fresh-baseline と異なり「既存プロンプトを lean に削る」方向(繰り返し排除・無効 example 削除・tool scope 限定)で、autonomy boundary の明示列挙、eval-gated Pro Mode、persisted reasoning、bounded PTC が新要素になる。

また運用実態として、(a) サブスクリプションで賄える実行経路(Claude Code の Opus 5 / Fable 5、Codex の GPT-5.6)が routine の標準になった一方、(b) 特定プロジェクトでは Claude モデルを Copilot CLI(credit 課金)経由で実行する executor 移譲が発生している。従来の evaluator は model と executor を分離して解決する検査観点を持たず、「モデル vendor の CLI が唯一の実行経路」という暗黙前提や、暗黙継承される executor override を検出できなかった。

## Decision

- 公式ドキュメント(latest-model / prompt-guidance の `?model=gpt-5.6`)を正本として `skills/gpt-5-6-tuning` を新設する。中核方針は rewrite ではなく trim(lean prompts)、effort は現行 baseline から 1 段下げテスト、既定簡潔化に伴う brevity 指示の見直し、安全アクション明示の autonomy boundary、eval-gated Pro Mode、persisted reasoning、bounded PTC、variant 配分の resolver 集約とする。
- `skills/codex-cli-runner` に `gpt-5-6` prompt profile を追加する。`auto` は明示 `--model` の 5.6 系(sol / terra / luna / alias)にのみ適用し、5.5 系と相互誤検出しない。wrapper の `--effort` choices は Codex CLI の `model_reasoning_effort` が `none` / `max` を受理するか未検証のため変更せず、必要時は `--extra-codex-arg` の config 経由とする。
- `skills/agent-orchestration-evaluator` に executor / billing source の分離解決を導入する(invariant 24 / 25)。runner 契約・budget guard・usage 報告は model vendor ではなく executor に従う。
- **サブスク標準採用ポリシー**: サブスクリプションで賄える実行経路では現行世代 flagship を routine の標準とする — Claude Code entrypoint は Opus 5(長期自律・ゼロベース監査等の明示要件では Fable 5、既存 role 規約に従う)、Codex entrypoint は GPT-5.6(role 別 variant は ADR 0054)。従量・credit 課金経路(API 予算、Copilot credits、via-Copilot の Fable/Opus)は per-run の明示予算契約を必須とし、silent default / fallback にしない。
- **Per-project executor override**: 特定プロジェクトが Claude モデルを Copilot CLI 経由で実行する場合、そのプロジェクトの resolver / registry で override を宣言し、`copilot-cli-runner` の契約(credit cap、usage 記録、Fable 明示選択による30日保持 acknowledgment、model-neutral な task-data boundary)に従う。グローバル既定からの暗黙継承は認めない。
- evaluator の skill 本文では具体モデル名を non-authoritative 例に留め(invariant 10 維持)、本 ADR を標準採用ポリシーの正本とする。

## Placement

- 世代 doctrine: `skills/gpt-5-6-tuning`(Codex 系)、`skills/opus-5-tuning` / `skills/fable-5-tuning`(Claude 系、ADR 0055 / 0056)
- 世代 adapter: `codex-cli-runner`(gpt-5-6)、`claude-cli-runner`(opus-5)、`copilot-cli-runner`(opus-5 / fable-5)
- executor / billing 検査観点: `skills/agent-orchestration-evaluator`
- Codex / Claude Code / Copilot の具体既定モデル: `dot_codex/` / `dot_claude/` / `dot_copilot/`(Codex 管理域、ADR 0054)— 本 ADR では変更しない

## Consequences

- GPT-5.6 実行時は runner の gpt-5-6 adapter が lean / autonomy boundary 補正を担い、role prompt の書き換えなしで世代更新できる。
- サブスク標準と従量経路の境界が evaluator で検査可能になり、Copilot credits や API 予算の無自覚な消費、premium tier への silent fallback を防げる。
- Claude モデルの Copilot 移譲はプロジェクト単位の宣言的 override として扱われ、runner 契約の取り違え(claude-cli-runner の契約を Copilot 実行に適用する等)を防げる。
- Codex CLI が effort の `none` / `max` を正式サポートしたと確認できた場合は、wrapper choices の拡張を別途検討する。

## Validation

- `scripts/skill-quick-validate` を gpt-5-6-tuning / codex-cli-runner / agent-orchestration-evaluator に実行し合格。
- codex wrapper の profile 判定 12 ケース(sol / terra / luna / alias、5.5 との相互誤検出なし、gpt-5.4 非対象)合格。
- fake CLI による no-API e2e(`--model gpt-5.6-sol`)で `prompt_profile=gpt-5-6`・adapter 注入・success を確認。
- 検証 artifact は `.context/gpt-5-6-adoption/` に保存(machine-local、git 管理外)。
