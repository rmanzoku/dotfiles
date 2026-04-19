---
title: "ADR 0002: repo-docs-diagnose スキルは docs 診断と提案に留める"
status: accepted
date: 2026-03-12
worked_at: 2026-04-20 00:40 JST
agent_model: GPT-5 Codex
---

# ADR 0002: repo-docs-diagnose スキルは docs 診断と提案に留める

## Context

AI エージェント前提のリポジトリでは、README、docs index、architecture docs、service docs、design-system docs、運用文書、agent entrypoint の入口設計が探索効率と参照品質に直結する。

一方で、docs が不足しているリポジトリでは「何を追加・整理すると AI が読みやすくなるか」を提案できると再利用価値が高い。

このスキルの設計にあたり、別の参照リポジトリで docs 導線の benchmark を行い、正規入口を追加した構造と既存構造を比較した。
その結果、architecture / services / skills のような入口発見系シナリオでは一定の改善が見られたが、review / precommit のように feature spec と横断ルール参照が重要な導線では、入口の正規化だけでは改善が不十分だった。

そのため、この dotfiles リポジトリに追加する skill は、対象リポジトリの自動変更まで含めず、診断と提案に留めるのが妥当である。

## Decision

- `skills/repo-docs-diagnose/` を publisher source として追加する。
- この skill は 2 モードを持つ。
  - `diagnose`: read-only で docs 構造を診断する
  - `bootstrap`: 明示要求がある場合だけ docs/entrypoint/運用文書の雛形提案を返す
- script 出力は JSON に統一し、そこから人間向け文面を組み立てる。
- bootstrap keyword が含まれない曖昧な依頼は `diagnose` として扱う。
- bootstrap でも対象 repo のファイルは自動作成しない。
- 固定パスは創作上の唯一解ではなく推奨パスとして扱う。`docs/` 配下に既存文書がある場合は、欠落判定より先に「推奨パスへ正規化する」提案を返す。
- benchmark で試した docs 正規化構造は、このスキルの推奨デフォルトとしては採用しない。
- 特に review / precommit 系の導線については、入口追加だけでなく feature spec と横断ルールへの到達性を別に検証するまで、一般化した推奨に含めない。

## Benchmark Note

この判断に使った benchmark は、抽象的には次の 3 系統を比較した。

- repo onboarding
  - リポジトリの目的、正規 docs、読み順の把握
- skill dispatch / routing
  - spec / implement / UI / review / precommit で正しい docs と skill に到達できるか
- normalized entrypoint discovery
  - architecture / services / skills の最短入口を発見できるか

主な観測は次のとおり。

- 入口発見系では、`AGENTS.md` や architecture/services/skills の index 追加が有効なケースがあった
- skill dispatch 系でも、skill index の明示は一部シナリオで有効だった
- ただし review / precommit 系では、`docs/ai_playbook.md`、`docs/backend_rules.md`、`docs/api_contract.md`、対象 feature spec まで踏ませる導線が必要で、単純な入口正規化だけでは不十分だった
- したがって、benchmark は「docs 導線を診断・提案する価値」は裏付けたが、「特定の推奨構造をそのまま汎用採用する価値」までは裏付けなかった

## Consequences

- README / docs index / architecture / services / design-system / operational docs / entrypoint の欠落を定型ルールで診断できる。
- 既存 docs を活かしながら、推奨パスへ寄せる改善案を返せる。
- docs 初期化が必要な repo でも、提案ベースで安全に着手できる。
- 特定の docs 構造をハードに押し付けず、既存構造を活かした診断ができる。
- skill 自体は再利用しやすくなるが、実際の docs 作成は別依頼または別ターンで実行する必要がある。
