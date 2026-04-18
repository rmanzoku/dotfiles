---
name: grok-x-research
description: Delegate X-focused research, discourse analysis, post-angle discovery, and draft-post generation to Grok through file-based artifacts and the xAI API. Use when Claude Code should stay as the orchestrator but needs a dedicated Grok pass over recent X context, specific handles, date windows, or pre-post risk checks. This skill is for research delegation only and does not post to X.
---

# grok-x-research

Claude Code をオーケストレーターとして保ちつつ、X 調査だけを Grok に委任する。
request / response は `.context/` 配下の JSON artifact を正本にする。

## Workflow

1. [references/schema.md](./references/schema.md) を読み、`.context/<task>/grok-request.json` を作成する。
2. `~/.local/bin/grok_x_research --request <request-path> --response <response-path>` を実行する。
3. response artifact の `risks` と `sources` を確認し、Claude 側で最終判断に統合する。
4. 投稿実行や最終承認は Claude 側で行い、この skill には持たせない。

## Rules

- 質問、対象読者、出力言語を request に明示する。
- 狭い調査では `x_search` の handle / date 制約を使う。
- 投稿案に使う可能性があるときは source URL を必須にする。
- `XAI_API_KEY` が必要。X Premium+ だけでは API 実行できない。
- 形を確認するときは先に `--dry-run` を使う。
- 高リスクな主張は別途検証し、source が弱い場合は request を狭めて再実行する。

## Boundaries

- この skill は X への直接投稿を行わない。
- X ネイティブ文脈が不要な一般 Web 調査には使わない。
- 実装ロジックは shared executable に置き、Claude 側には複製しない。
