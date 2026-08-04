---
title: "ADR 0063: 委譲契約は agent 定義へ移し、グローバル指示から role 名を排除する"
status: accepted
date: 2026-08-04
worked_at: 2026-08-04 15:10 JST
agent_model: Claude Fable 5
---

# ADR 0063: 委譲契約は agent 定義へ移し、グローバル指示から role 名を排除する

## Context

ADR-0062 でサービス名の境界ルールを抽象化した後も、Codex 固有節の Subagents 節(7 bullets)には `tech` / `biz` / `personal` の役割名を挙げた個別規定が残っていた。ユーザーレビューで「subagent と別モデル runner の契約は構造化された場所に保持し、AGENTS.md は『適切な呼び出しをする』程度に留めたい」と指摘された。runner 側は既に構造化済み(workspace の model_registry.yaml / model_resolver.md、各 runner skill)で、subagent 側だけがグローバル指示に個別契約を露出していた。

## Decision

1. **委譲の一般契約だけを共通ルールに置く**(role 名なし・5 bullets): 委譲推奨 / 入力契約(「委譲先の定義(description)が求める入力契約に従う」+ 暗黙継承しない前提 + 利用不能時の扱い)/ secret 非共有(personal 限定から全委譲先へ一般化。親への閲覧許可 ≠ 委譲先への共有許可)/ 限定判断と親の最終責任 / 匿名比較
2. **役割固有の契約は agent 定義の description と本文へ移す**: tech の入力契約(事業前提・規模・フェーズ・体制・不可逆リスク・ADR 有無・evaluator 指定)は tech の description へ、rubric 正本参照は tech 本文へ。personal の要約絞り込み(raw 予定本文・参加者一覧を渡さない)は personal の description へ。biz/tech の使い分け例は各 description が既に定義するため削除
3. **Codex 固有の Subagents 節は全廃**。Codex 固有ルールは Config / Trust と Automations のみになる
4. **機械執行**: instruction-gc に 5b 検査を追加 — common-rules / AGENTS.md.tmpl に role 名(バッククォート付き `tech` 等)が出現したら fail。あわせて md/toml の description 比較(warn)も追加(実施時に tech / biz / personal の description が md/toml で乖離していたことを検出・統一済み)
5. 検証: 縮小版 AGENTS.md + 実 agent 一覧(新 description)を読む白紙実行者(Opus)に S3 同一シナリオを実行させ、[critical] 達成が維持されることを確認する

## Consequences

- 配備 61 行→53 行 / 4,464 字。グローバル指示は role 非依存になり、agent の追加・改廃で AGENTS.md を編集する必要がなくなる(契約は定義とともに生まれ、定義とともに消える)
- 委譲契約の正本は各 agent 定義(1Password 管理)。description は毎セッションの agent 一覧に載るため、可視性は AGENTS.md 記載と同等
- 「description の入力契約に従う」という接着ルール 1 本が、定義側契約に拘束力を与える
