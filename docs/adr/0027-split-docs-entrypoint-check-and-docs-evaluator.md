---
title: "ADR 0027: docs entrypoint check と docs evaluator を分離する"
status: accepted
date: 2026-04-26
worked_at: 2026-04-26 00:00 JST
agent_model: GPT-5 Codex
---

# ADR 0027: docs entrypoint check と docs evaluator を分離する

## Context

既存の `repo-docs-diagnose` は、README、docs index、architecture / service / design-system / operational docs、agent entrypoint の有無と導線を軽量に確認し、明示的な初期化依頼では docs skeleton を提案する skill として作られた。

一方で、リポジトリのドキュメント品質には、入口の有無だけでは判断できない観点がある。

- すべてのテキストドキュメントが棚卸しされているか
- README、AGENTS、CLAUDE.md、skills、docs index などから必要な文書へ辿れるか
- AI が読む前提で必要十分な粒度になっているか
- ADR や workbench などの履歴・一時文書が正本扱いされていないか
- TODO / Deferred Work / gap が散在せず管理されているか
- 廃止済み docs や skills が active navigation に残っていないか
- ドキュメント間に矛盾がないか
- 一時文書の内容が正本へ反映済みか、未反映 gap が管理されているか

これらは `code-evaluator` と同じく、実装や削除を行う skill ではなく、artifact-backed な評価レポートとして扱う方が適している。

また、`diagnose` という語は「軽量な入口確認」と「広域 docs 監査」の境界を曖昧にしやすい。

## Decision

- `repo-docs-diagnose` を廃止し、役割を `docs-entrypoint-check` にリネームする。
- `docs-entrypoint-check` は README / docs index / agent entrypoint / docs skeleton の軽量 check と bootstrap 提案に限定する。
- `docs-evaluator` を新設し、リポジトリのドキュメントシステム全体を評価する report-only skill とする。
- `docs-evaluator` は `code-evaluator` と同じ立ち位置に置き、`.context/docs-evaluator/<task>/` に inventory、reachability、source-of-truth、raw findings、checks、report を保存する。
- `docs-evaluator` は対象 repo の docs を編集・削除・正本反映・commit しない。
- 配布 manifest は `docs-entrypoint-check` と `docs-evaluator` を first-party publisher skills として復元対象にする。

## Consequences

- 軽量な docs 入口確認は `docs-entrypoint-check` を使う。
- 全テキストドキュメントの棚卸し、到達性、正本性、矛盾、廃止物、TODO / Deferred Work、未反映 gap の評価は `docs-evaluator` を使う。
- docs の修正作業は `docs-evaluator` の report を根拠に、別ターンまたは通常の編集作業として実施する。
- 既存の `repo-docs-diagnose` という skill 名は新規 install 対象から外れる。
