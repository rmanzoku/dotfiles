---
title: "ADR 0028: docs-evaluator に docs 実行迷子要因の評価軸を追加する"
status: accepted
date: 2026-04-26
worked_at: 2026-04-26 00:00 JST
agent_model: GPT-5 Codex
---

# ADR 0028: docs-evaluator に docs 実行迷子要因の評価軸を追加する

## Context

`docs-evaluator` は `code-evaluator` と同じ report-only / artifact-backed evaluator として、リポジトリの docs system を広域評価するために追加した。

初期設計では inventory、reachability、source-of-truth boundaries、AI readability、contradictions、TODO / Deferred Work、deprecated docs、temporary-to-canonical gaps を扱っていた。

ただし AI agent が docs を読んで実行するときの失敗は、単純な未到達や矛盾だけでなく、次のような「判断の分岐」で発生しやすい。

- 複数の entrypoint がそれぞれ最初に読む文書を主張している
- 複数 docs が同一 topic の正本を主張している
- MUST / SHOULD / MAY や 必須 / 推奨 / 任意 の強度が docs 間で揺れている
- 共通ルールと AI 別ルールの置き場所が混ざっている
- Skill が repo rule を継承するのか、具体手順を上書きするのか不明
- Markdown metadata が front matter と本文に分散している
- 外部参照、manifest、spec、contract、実装参照先が docs から辿れない
- 古い docs を stale と判断するための deprecation / replacement / manifest / git history signal が不足している

これらは prose style や SEO の問題ではなく、AI agent の実行結果を変える docs system 上のリスクである。

## Decision

- `docs-evaluator` の評価観点に entrypoint conflict、canonical claim conflict、instruction strength drift、agent-specific guidance separation、skill contract precedence、metadata / front matter hygiene を追加する。
- 補助観点として anchor/reference quality、terminology consistency、qualitative reading burden を扱う。
- reference integrity と freshness governance を追加し、外部参照・依存関係・spec/contract への traceability を docs 上の評価対象にする。
- これらは `contradiction` や `reachability` の単なる下位項目にせず、必要に応じて独立した issue category と report section で扱う。
- `docs-evaluator` は引き続き report-only とし、文体校正、SEO 指標、コード例実行、secrets / PII scan、自動修正、PR 作成、文書削除は扱わない。
- code が docs の contract を実装しているかの検証は `code-evaluator` 側に残し、`docs-evaluator` は参照先が docs から明確に辿れるかだけを評価する。
- reading cost、terminology consistency、metadata hygiene は過度に定量化せず、repo-declared rule や AI 実行リスクに関係する場合だけ finding 化する。

## Consequences

- `docs-evaluator` は docs が「存在するか」だけでなく、AI agent がどの指示を優先すべきか迷う構造を評価できる。
- `docs-evaluator` の report は、entrypoint、正本、指示強度、AI 別ルール、Skill 契約、metadata の整理作業に使える。
- 外部参照や spec/contract traceability の欠落を docs 問題として扱えるが、実装 correctness の評価には踏み込まない。
- 実際の docs 修正は、評価 report を根拠に別作業として実施する。
