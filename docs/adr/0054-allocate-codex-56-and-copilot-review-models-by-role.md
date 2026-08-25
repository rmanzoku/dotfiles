---
title: "ADR 0054: Codex 5.6 と Copilot review model を role 別に割り当てる"
status: accepted
date: 2026-07-19
worked_at: 2026-07-19 10:35 JST
agent_model: OpenAI Codex GPT-5.6 Sol
---

# ADR 0054: Codex 5.6 と Copilot review model を role 別に割り当てる

> Fable の task-data authorization と credit floor は [ADR 0069](./0069-normalize-ai-cli-runner-data-boundaries.md) により一部更新された。30日保持、明示選択、hard cap、暗黙 fallback 禁止は維持する。

## Context

Codex の live default は `gpt-5.6-sol` / `high` へ更新されていた一方、chezmoi source は `gpt-5.5` / `medium` のままで、再適用時に旧世代へ戻る drift があった。Copilot CLI の live default は `claude-fable-5` / `high` だが、Fable は長期自律作業向けの性質、別のデータ保持条件、通常の Opus 4.8 より大きい credit 消費を持つため、日常の既定にすると用途・機密性・予算の境界が曖昧になる。

モデル名を各 repository の実装ルールへ広く埋め込むと更新点が増える。モデル差ではなく role で委譲する既存方針を維持し、個人の cross-repository default と custom agent は chezmoi、Copilot の一回ごとの選択は runner caller と run artifact で管理する。

## Decision

- Codex の parent orchestrator の既定を `gpt-5.6-sol` / `medium` とする。要求解釈、分割、委譲、結果統合、最終判断を担わせ、常時 `high` にはしない。
- 高リスクな設計、セキュリティ、データ整合性、公開 contract、release、難しい事業判断は `tech` / `biz` custom agent を経由し、`gpt-5.6-sol` / `high` を使う。
- `personal` は `gpt-5.6-terra` / `medium` とする。
- 問題と scope が確定した owner-local の通常実装は `worker` で `gpt-5.6-terra` / `medium` を使う。仕様、公開 contract、security、data integrity の曖昧さは parent orchestrator へ戻す。
- 境界、入力、成功条件が確定した機械的な実装・変換・定型処理は `mechanical` と automation で `gpt-5.6-luna` / `low` を使う。曖昧さが現れた場合は推測せず parent へ戻す。
- Claude Code にも同じ user-level role を置き、`worker` は `sonnet`、`mechanical` は `haiku` を使う。provider 固有の model alias は各 agent file で管理し、role contract は Codex と揃える。
- Copilot CLI の global default は独立した深い review に使う `claude-opus-4.8` / `high` とする。
- `claude-fable-5` / `high` は caller が明示指定した場合だけ使う。明示指定は provider の30日保持条件の acknowledgment を兼ね、task-relevant な private repository code と internal documents に追加確認を要求しない。hard AI-credit cap を設定し、requested model・effort・credits・elapsed time・artifact を run ごとに記録する。
- Fable と Opus の間で自動 fallback しない。失敗時は原因を記録し、model・budget・scope のどれを変更するか明示して再実行する。
- Screenshot QA の `gpt-5.5` required lane と `claude-opus-4.6` optional lane は、exact-model attestation と代表 visual corpus の benchmark が終わるまで変更しない。

## Placement

- Codex default と custom agent: `dot_codex/`
- Claude Code custom agent: `dot_claude/agents/`
- `tech`、`biz`、`personal` は ADR 0039 に従う git-ignored / 1Password-backed file とする。
- Generic `worker` / `mechanical` は両 provider とも tracked chezmoi source とし、1Password へ保存しない。
- Copilot default: `dot_copilot/private_settings.json`
- Fable の実行境界と credit contract: `skills/copilot-cli-runner/SKILL.md`
- repository 固有の executable consumer: その repository の registry または caller。global default を暗黙に継承させない。

## Consequences

- Codex orchestrator は Sol/medium、通常実装は Terra/medium、明確な反復作業は Luna/low となり、判断品質を親で維持しつつ Sol/high の常用を避けられる。
- Fable の長期自律性と task-relevant な private repository context を利用できる。caller の明示選択は30日保持条件の acknowledgment を兼ね、credit 消費は hard cap で制御する。
- Codex custom `worker` は built-in `worker` より優先されるが、Terra/medium の通常実装 role なので自動委譲時にも Luna へ誤配送しない。Luna は明示的な `mechanical` に限定される。
- Private agent の model override は、1Password の `Secrets Manifest` を更新しない限り他マシンへ復元されない。Generic agent は git と chezmoi だけで復元できる。
- モデル提供状況または料金・保持条件が変わった場合は、CLI の model listing と公式文書を再確認して本 ADR を更新する。

## Validation

- Codex custom agent TOML と Claude Code agent Markdown front matter を parse し、必須 field と role ごとの model を確認する。
- Private agent を変更した場合だけ `opmaterialize add` 後の manifest status を確認する。
- Copilot settings JSON を parse し、`copilot --help` または model listing で model id を確認する。
- `scripts/skill-quick-validate skills/copilot-cli-runner` と runner の no-API validation を実行する。
- `scripts/chezmoi-drift --check-ignore`、`chezmoi diff`、Markdown / repository validation を実行する。
