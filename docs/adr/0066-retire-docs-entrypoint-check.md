---
title: "ADR 0066: docs-entrypoint-check を退役する"
status: "Accepted"
date: "2026-08-10"
worked_at: "2026-08-10 JST"
agent_model: "Claude Fable 5 (Claude Code)"
supersedes: "ADR 0027"
---

# ADR 0066: docs-entrypoint-check を退役する

## Context

docs-entrypoint-check は ADR-0027 で docs-evaluator から分割された軽量チェック skill(README / docs index / agent 入口の確認と bootstrap 雛形生成)。cleaner run 1 がその references に根拠不明の前提行を検出し(S-F13 / B-3)、意図確認をユーザーへ escalate したところ、skill 自体の有用性への疑義が返った。

調査結果:

- **使用痕跡ゼロ**: dotfiles・workspace 両 repo の `.context/` に run artifact が 1 件も無い(docs-evaluator は 13 run 分が残っているのと対照的)
- **skill 丸ごとがモデル既定挙動の教示**: 入口の確認も雛形生成も、現行世代のエージェントが AGENTS.md / README から指示なしでこなす作業であり、ADR-0061 クラス 2 が行単位ではなく skill 単位で該当する
- 汎用テンプレートより対象 repo の慣習に合わせた生成のほうが質が高く、雛形の固定価値も薄い
- docs-evaluator と相互 routing 文を持つ近接ペアで、発火 probe の監視対象だった

ユーザー判断(2026-08-10): 退役。

## Decision

- `skills/docs-entrypoint-check` を repo から削除し、両 agent の installed 実体を除去、manifest から install 行を削除する
- docs-evaluator の routing 参照(冒頭・mode 推論・mode decision order step 2)を清掃し、「軽量な入口チェックは skill 不要、直接対応する」と明記する
- `docs-entrypoint-check` を instruction-gc の STALE_TERMS へ追加する(ratchet。再浮上参照は fail)
- ADR-0027 の分割決定を本 ADR で supersede する。docs-evaluator 側の深い監査は従来どおり
- 失うもの: repo 横断の固定チェックリストとしての一貫性。使用実績が無いため許容と判断した

## Validation

- `scripts/instruction-gc` green(manifest parity・STALE_TERMS・露出予算 baseline 更新込み)
- 発火 probe: 旧トリガー発話「README や docs の入口が最低限揃っているか軽くチェックして」が none に落ち、docs-evaluator の broad audit 発話・instruction-cleaner の掃除発話に回帰が無いこと
