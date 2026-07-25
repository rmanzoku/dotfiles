---
title: "ADR 0056: Claude Fable 5 tuning skill を新設し Copilot CLI runner に世代 adapter を導入する"
status: accepted
date: 2026-07-25
worked_at: 2026-07-25 11:32 JST
agent_model: Claude Fable 5 (claude-fable-5)
---

# ADR 0056: Claude Fable 5 tuning skill を新設し Copilot CLI runner に世代 adapter を導入する

## Context

ADR 0055 で Claude Opus 5 を tuning skill と claude-cli-runner の prompt profile へ採用したが、Claude Fable 5(`claude-fable-5`、Mythos 5 同仕様)には対応する tuning skill がなかった。Fable 5 は Opus 5 と補正方向が逆の項目を持つ: 委譲は奨励(async 推奨)、自己検証は明示的に harness 化、手順は de-prescribe。thinking は常時 ON で設定自体が 400 になり、30 日 data retention が必須で、価格は Opus tier より上のため明示採用のみが前提になる。

また Opus / Fable は claude-cli-runner だけでなく copilot-cli-runner 経由でも実行される(ADR 0054: Copilot の独立深層 review が Opus、長期自律・ゼロベース監査が明示指定の Fable)。copilot-cli-runner の prompt profile は汎用 Copilot adapter の 1 軸のみで、モデル世代補正を注入する場所がなく、evaluator invariant 23(世代補正は runner prompt profile に置く)を Copilot 経路で満たせなかった。

## Decision

- 公式ドキュメント(introducing-claude-fable-5-and-claude-mythos-5、prompting-claude-fable-5、migration-guide)を正本として `skills/fable-5-tuning` を新設する。構造は opus-5-tuning を踏襲し、「Opus 5 との反転で事故りやすい点」比較表(委譲・検証・手順粒度・thinking)を持たせる。
- 既定のアップグレード先は引き続き Opus 系とし、fable-5-tuning は Fable 5 を明示選択した workflow だけを対象にする。採用前提(明示選択・retention・予算 cap)の文書化を完了条件に含める。
- `skills/copilot-cli-runner` の prompt profile を `auto / copilot / opus-5 / fable-5 / none` に拡張する。世代 adapter は Copilot adapter(共通契約)への合成とし、`auto` は明示 `--model` からのみ世代を検出、bare alias(`opus` / `fable`)は検出しない。
- 世代 adapter の doctrine は opus-5-tuning / fable-5-tuning を正本とし、runner には補正内容の要約だけを持たせる。Fable の実行契約(明示要求・retention 境界・hard AI-credit cap・暗黙 fallback 禁止、ADR 0054)は変更しない。Fable の長 turn 特性を踏まえ、timeout と credit cap の同時設計を caller checklist に追記する。
- opus-5-tuning / fable-5-tuning の両方に「実行経路は claude-cli-runner に限らない」ことを明記し、世代補正の置き場所を runner prompt profile に統一する(evaluator invariant 23 と整合)。
- `docs/skills-install-manifest.md` に fable-5-tuning を追加し、Claude Code / Codex 両方へ `gh skill install --from-local` で配備する。

## Consequences

- Copilot 経由の Opus 5 / Fable 5 実行でも、caller が `--model` を渡すだけで世代補正が launch prompt に載る。Copilot の既定モデル(dot_copilot 管理、Codex 域)は変更していないため、既定変更は別途 ADR 0054 の更新として扱う。
- 委譲・検証の補正方向が世代で逆になるリスクは、両 tuning skill の比較表と evaluator の invariant 23 検査で抑止する。
- Fable 5 の採用は引き続き明示選択のみで、暗黙 fallback や既定化は起きない。
- モデル提供状況・料金・retention 条件が変わった場合は、公式ドキュメントを再確認して両 tuning skill と本 ADR を更新する。

## Validation

- `scripts/skill-quick-validate` を fable-5-tuning / opus-5-tuning / copilot-cli-runner に実行し合格。
- copilot wrapper の profile 判定 14 ケース(dotted `claude-opus-4.8` / `claude-opus-4.5` の誤検出なし、bare alias 非検出、明示 profile 優先)合格。
- fake CLI no-API e2e で `claude-fable-5` → fable-5 profile、`claude-opus-5` → opus-5 profile の adapter 合成と success を確認。
- 検証 artifact は `.context/fable-5-adoption/` に保存(machine-local、git 管理外)。
