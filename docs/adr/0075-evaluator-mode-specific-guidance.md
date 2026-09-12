---
title: "ADR 0075: Evaluator のモード別ガイダンスを条件付き参照へ分離する"
status: "Accepted"
date: "2026-09-13"
worked_at: "2026-09-13 00:49:57 JST"
agent_model: "GPT-5.6 Terra (author); GPT-6 Astra (integration)"
---

# ADR 0075: Evaluator のモード別ガイダンスを条件付き参照へ分離する

## Context

`agent-orchestration-evaluator` は監査、調整、Skill 抽出を扱うが、詳細な監査手順と調整例を常時読み込んでいた。さらに編集しない `audit` に、編集を伴う完了条件が混在していた。現行の owner-local 直接実行と benefit-based delegation の方針、25 個の Invariants、runner mapping は現行利用者方針として保持する必要がある。

## Decision

`SKILL.md` にはモード選択、Core Model、25 個の Invariants、Expected runner mapping、モード別の出力と完了条件を残す。`audit` の詳細手順は `references/audit-checklist.md`、`tune` と `extract-skill` の調整例は `references/tuning-patterns.md` に移す。監査中の具体的な推奨文に例が必要な場合だけ、後者も参照する。

`audit` は findings/evidence/limitations/recommendations/verification plan を返せば完了とし、未修正のソース欠陥を完了阻害にしない。`tune` と `extract-skill` は要求範囲と適用される既存 Invariants のみを受け入れ条件とし、無関係な repository-wide defect の解消を要求しない。抽出は既存の `skill-creator` workflow を使う。

## Consequences

入口の常時読み込み量を減らしつつ、全モードに必要な判断基準と runner mapping を維持する。監査では調査対象を編集せず、証拠 artifact は handoff、利用者指定の audit trail、identity、recovery に必要な場合だけ作成する。利用者が全ファイルへの書込を禁止した場合は応答内に記録する。調整では正規 resolver と依存 Skill の整合・更新順序を保持する。

## Verification

- `scripts/skill-quick-validate skills/agent-orchestration-evaluator`
- `scripts/docs-link-check skills/agent-orchestration-evaluator/SKILL.md skills/agent-orchestration-evaluator/references/audit-checklist.md skills/agent-orchestration-evaluator/references/tuning-patterns.md docs/adr/0075-evaluator-mode-specific-guidance.md`
- `SKILL.md`、追加 reference、ADR の全体 Markdown 確認
