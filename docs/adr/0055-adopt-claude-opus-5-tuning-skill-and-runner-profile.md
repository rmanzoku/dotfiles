---
title: "ADR 0055: Claude Opus 5 を tuning skill・CLI runner profile・orchestration evaluator へ採用する"
status: accepted
date: 2026-07-25
worked_at: 2026-07-25 11:20 JST
agent_model: Claude Fable 5 (claude-fable-5)
---

# ADR 0055: Claude Opus 5 を tuning skill・CLI runner profile・orchestration evaluator へ採用する

## Context

Claude Opus 5(`claude-opus-5`)がリリースされた。Opus 4.8 と同価格のドロップインだが、(a) thinking が既定で有効、(b) thinking disabled は effort `high` 以下限定という 2 つの breaking change があり、さらに挙動バイアスが旧世代から反転している: subagent へ過剰に委譲しやすく(4.8 は過少委譲)、指示なしで自己検証する(4.8 は self-check 指示が有効だった)。

この repo には `opus-4-7-tuning` / `opus-4-8-tuning` / `gpt-5-5-tuning` というモデル別 tuning skill の系譜と、`claude-cli-runner` のモデル別 prompt profile(opus-4-7 / opus-4-8 adapter)がある。Opus 5 向けの adapter がないままだと、4.8 向け補正(委譲奨励・self-check 前提)が Opus 5 実行時に逆効果になる。また `agent-orchestration-evaluator` には「モデル世代固有の挙動補正を role prompt に固定しない」ことを検査する観点がなかった。

## Decision

- 公式ドキュメント(whats-new-opus-5、prompting-claude-opus-5、migration-guide)を正本として `skills/opus-5-tuning` を新設する。構造は `opus-4-8-tuning` を踏襲し、Opus 5 固有の反転項目(検証 scaffolding 削除、委譲 cap、effort 下方 sweep、scope discipline、冗長性の prompt 制御)を典型修正パターンとして定義する。
- `skills/claude-cli-runner` に `opus-5` prompt profile を追加する。`auto` は `claude-opus-5` / `opus-5` 形の明示モデルにのみ適用し、`opus-4-5` 系や bare `opus` alias には適用しない。adapter は literal 実行・requested scope・検証パス/検証 subagent の追加禁止・委譲限定・review coverage 維持を短く肯定形で指示する。既定モデルを runner に持たせない方針(ADR 0053 と同系)は維持する。
- `skills/agent-orchestration-evaluator` に invariant 23 を追加する: モデル世代固有の挙動補正(委譲奨励/抑制、self-check 強制、進捗 scaffold)は resolver / model adapter / runner prompt profile に置き、role prompt や skill 本文に固定しない。SKILL.md は model-agnostic を維持し、Opus 5 の具体名は tuning skill と runner adapter 側だけが持つ。
- `docs/skills-install-manifest.md` に `opus-5-tuning` を追加し、Claude Code / Codex 両方へ `gh skill install --from-local` で配備する。

## Consequences

- Opus 5 実行時は runner の opus-5 adapter が世代補正を担い、role prompt・skill 本文は書き換え不要になる。モデル更新時の変更点が adapter と tuning skill に局所化される。
- 4.8 向け補正の残存(委譲奨励・self-check 指示)は `opus-5-tuning` の監査フローと evaluator の新観点で検出できる。
- Opus 4.8 以前を使い続ける workflow には影響しない(既存 profile・skill は変更なし)。
- モデル提供状況や公式ガイダンスが変わった場合は、公式ドキュメントを再確認して `opus-5-tuning` と本 ADR を更新する。

## Validation

- `scripts/skill-quick-validate` を `opus-5-tuning` / `claude-cli-runner` / `agent-orchestration-evaluator` に実行し合格。
- `run_claude_cli.py` の profile 自動判定を 10 ケースで検証(`claude-opus-4-5` 系の誤検出なしを含む)し合格。
- fake CLI による no-API e2e(`--model claude-opus-5`)で `prompt_profile=opus-5`・adapter 注入・success を確認。
- 検証 artifact は `.context/opus-5-adoption/` に保存(machine-local、git 管理外)。
