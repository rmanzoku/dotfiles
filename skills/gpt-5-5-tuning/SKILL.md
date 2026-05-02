---
name: gpt-5-5-tuning
description: "Audit and rewrite repository docs, skills, prompts, and agent harness scaffolding so they fit GPT-5.5 behavior and API guidance: fresh prompt baselines, outcome-first task framing, medium reasoning effort by default, eval-gated high/xhigh effort, intentional text.verbosity, tool guidance in tool descriptions, phase preservation, explicit image_detail, structured outputs, and prompt-cache-friendly layout. Use when the user wants to migrate or readiness-check prompts, AGENTS.md / CLAUDE.md / skill files, agent rules, or eval harnesses for GPT-5.5. Do not use for broad OpenAI SDK migrations or application feature rewrites beyond prompt, model, and orchestration guidance."
---

# GPT-5.5 Tuning

リポジトリのドキュメント・スキル・プロンプト・エージェント運用ルールを GPT-5.5 の挙動に合わせて整備するためのスキル。

本スキルは **人間やエージェントが読む運用文書・プロンプト側** の整備に特化する。SDK 移行、API クライアント実装、プロダクト機能の作り替えは、OpenAI 公式 docs を確認したうえで別タスクとして扱う。

## 起動する場面

次のいずれかに該当するときに起動する。

- ユーザーが「GPT-5.5 向けに整備したい」「GPT-5.5 readiness」「GPT-5.5 prompt tuning」「GPT-5.5 ベストプラクティス」と発話した。
- 既存の `AGENTS.md` / `CLAUDE.md` / `SKILL.md` / `docs/**` / `prompts/**` / `rules/**` が、GPT-5.4 以前や非 reasoning model の前提に寄っていないか棚卸しを依頼された。
- 旧来のプロンプティング指示（過剰な step-by-step 強制、`think step by step` 依存、固定 `high` / `xhigh`、曖昧な tool use 指示、prompt 内 schema 長文、日付注入など）の見直し依頼を受けた。
- GPT-5.5 への移行で `reasoning.effort`、`text.verbosity`、tool descriptions、`phase`、image detail、structured outputs、prompt caching の扱いを整理したい。

## 起動しない場面

- OpenAI SDK、Responses API 呼び出し、tool handler、認証、provider adapter を広く書き換える場合。
- 単発の OpenAI API 質問に答えるだけで、文書やプロンプトの改修を伴わない場合。
- モデル選定や最新 API 仕様の確認のみが目的の場合。この場合は `openai-docs` を優先する。

## 参照する公式ソース

作業中、迷ったら OpenAI 公式 docs を直接確認する。日付・パラメータ・推奨値は変わり得るため、古い記憶で断定しない。

- Using GPT-5.5: <https://developers.openai.com/api/docs/guides/latest-model?model=gpt-5.5>
- GPT-5.5 Prompt Guidance: <https://developers.openai.com/api/docs/guides/prompt-guidance?model=gpt-5.5>
- Models: <https://developers.openai.com/api/docs/models>
- Reasoning models: <https://developers.openai.com/api/docs/guides/reasoning>
- Structured outputs: <https://developers.openai.com/api/docs/guides/structured-outputs>
- Images and vision: <https://developers.openai.com/api/docs/guides/images-vision>
- Prompt caching: <https://developers.openai.com/api/docs/guides/prompt-caching>
- Phase parameter: <https://developers.openai.com/api/docs/guides/conversation-state#phase-parameter>

## GPT-5.5 で押さえる 10 項目

これは「文書を読みながら違反を見つける」ためのチェックリストでもある。

1. **drop-in 移行ではなく fresh baseline**
   旧プロンプトをそのまま引き継がない。product contract を保つ最小プロンプトから始め、代表例で `reasoning.effort`、`text.verbosity`、tool descriptions、output format を調整する。
2. **outcome-first prompts**
   期待成果、success criteria、許容される side effects、evidence rules、output shape を明示する。手順を細かく固定するのは、その経路自体が product 要件のときだけにする。
3. **`reasoning.effort` は `medium` 起点**
   GPT-5.5 の推奨起点は `medium`。latency-sensitive でも planning / search / tool use が必要なら `none` より先に `low` を評価する。`high` / `xhigh` は eval で品質向上が確認できた場合に使う。
4. **高 effort は万能ではない**
   矛盾した指示、弱い停止条件、無制限 tool access があるまま effort を上げると、過剰探索や品質低下を招く。まずプロンプトの矛盾、completion rule、tool boundary を直す。
5. **`text.verbosity` は最終回答長のレバー**
   reasoning quality と回答長を混同しない。簡潔さは `text.verbosity: low`、語数、節数、表幅、JSON-only などで指定する。顧客向けの温かさや説明量が必要な場合は明示する。
6. **literal and thorough な instruction following**
   GPT-5.5 は曖昧・矛盾した指示を雑に選び取らず、整合を取ろうとして reasoning token を消費する。instruction priority、override scope、stopping rule を明示する。
7. **tool guidance は tool description へ寄せる**
   tool 固有の「何をするか」「いつ使うか」「必須入力」「side effects」「retry safety」「よくある error mode」は tool description に書く。system prompt には全 tool 共通の運用方針だけを置く。
8. **long-running / tool-heavy workflow は状態管理を明示**
   Responses API の `previous_response_id`、手動 replay 時の assistant item と `phase` 保持、preamble、compaction、verification loop を運用文書に残す。
9. **structured outputs と prompt caching を前提化**
   parse-sensitive な schema は prompt に長く書くより Structured Outputs を使う。prompt caching のため、静的指示を前、動的 user context を後ろに置く。不要な current date 注入は削る。
10. **vision / computer use は `image_detail` を意図的に選ぶ**
   GPT-5.5 の `auto` はより詳細を保持する。精度重視なら `original` / `high`、コスト重視なら `low` を明示し、OCR・click accuracy・dense image では縮小前提を再評価する。

## 実行モード判定（着手前に必ず行う）

依頼を受けたら、監査や編集に入る前に以下の順で実行モードを決める。判定結果は artifact または作業結果に 1 行残す。

1. **依頼に複数の合理的解釈があり、設計判断や合意形成を伴う場合**
   `/grill-me` などの確認フローで依頼を完全指定にしてから 2 / 3 を再判定する。
   例: 「GPT-5.5 に揃える」（対象・モデル方針・API 変更範囲が未確定）、中央 model registry と各 skill の SoT 衝突整理。
2. **依頼が明確で、破壊的変更を伴う場合**
   中央モデルレジストリ、`AGENTS.md` / `CLAUDE.md` の構造変更、既存 skill description 変更、複数ファイル横断改修は Plan を提示し、repo の Plan review gate を通してから監査フローへ進む。
3. **依頼が明確で、変更が局所かつ破壊性がない場合**
   単発処理。監査フローはスキップし、「典型修正パターン」だけ参照して小さく直す。

## 監査フロー（リポジトリ全体に対する整備手順）

> 上記「実行モード判定」で **2（Plan）** を選んだ場合に本フローを使う。各 Phase 完了時に `.context/<task-name>/<nn>-<phase>.md` の artifact を残し、それを次 Phase の開始条件にする。**3（単発）** の場合はこのフローをスキップして「典型修正パターン」だけ参照する。

### Phase 1: スコープ確定

整備対象を確定する。最低でも次を確認する。

- 対象ファイル群（典型: `AGENTS.md`, `CLAUDE.md`, `.claude/skills/**`, `skills/**`, `docs/**`, `prompts/**`, `rules/**`, agent harness config）。
- モデル指定や reasoning 設定が分散していないか。中央 registry があれば、まずそこを SoT として確認する。
- API クライアント実装の変更が必要か。必要な場合は文書・プロンプト整備と切り分ける。
- GPT-5.5 一本化か、`gpt-5.4-mini` / `gpt-5.4-nano` / `gpt-5.5-pro` などとの役割分担か。
- artifact 配置先のタスク名。指定がなければ `gpt-5-5-tuning-<対象短縮>` 形式で決め、理由を残す。

artifact: `.context/<task>/01-scope.md`（対象ファイル一覧、除外理由、モデル指定の所在、依頼解釈、タスク名）。

### Phase 2: 監査

Phase 1 で確定したファイルを読み、下記「典型修正パターン」と照合して指摘リストを作る。各指摘には次を必須項目として残す。

- `path:line` または該当箇所の引用
- 該当する典型修正パターン記号（A-L、複数可）
- 判定理由
- 推奨アクション（置換案）

artifact: `.context/<task>/02-audit.md`（典型パターン記号でカラム化した指摘テーブル）。

### Phase 3: 改修

監査結果に基づき編集する。リポジトリの正規指示ファイルや model registry を SoT とし、AI 別ファイル・skill・docs が SoT と矛盾していたら SoT 側に寄せる。重複を増やさない。

破壊的な変更（中央 registry、`AGENTS.md` / `CLAUDE.md` の構造変更、既存 skill description 変更、API クライアント編集）の前にはユーザー確認を取る。

artifact: `.context/<task>/03-changes.md`（変更ファイル一覧、変更理由、残置理由）。

### Phase 4: 検証

- repo の docs lint、skill validation、prompt eval、unit test があれば実行する。
- 変更済みプロンプトまたは skill を 1 本選び、代表タスクで dry run またはレビューを行う。
- API パラメータに触れた場合は OpenAI 公式 docs の現行記述と照合する。

artifact: `.context/<task>/04-verify.md`（lint / eval / dry run 結果、未検証リスク）。

## 典型修正パターン（Audit 観点）

### A. 旧プロンプトをそのまま GPT-5.5 に持ち込んでいる

- 兆候: 「既存の GPT-5.2 / GPT-5.4 prompt を維持して model だけ置換」と書いている。
- 対応: product contract を残した最小 prompt から再評価する方針に置換する。

### B. effort を固定値や魔法語で代用している

- 兆候: すべて `high` / `xhigh`、または `think hard` / `step by step` を reasoning 設定の代替として推奨。
- 対応: `medium` 起点、`low` / `none` / `high` / `xhigh` の使い分け、eval-gated escalation に書き換える。

### C. outcome より手順が過剰に細かい

- 兆候: product 要件ではない step-by-step process、毎ターン plan/reflection 強制、長い手順固定。
- 対応: outcome、success criteria、constraints、allowed side effects、evidence rules、output shape を中心にする。手順固定は必要な箇所だけ残す。

### D. instruction priority と停止条件が曖昧

- 兆候: 新旧指示の優先順位、override scope、いつ終わるか、何を blocked とするかが不明。
- 対応: instruction priority、completion contract、missing context gate、verification loop を短く追加する。

### E. verbosity と reasoning を混同している

- 兆候: 「よく考えさせるために長く答えさせる」「簡潔化のため reasoning を下げる」など。
- 対応: 最終回答長は `text.verbosity` や output contract、推論量は `reasoning.effort` で別々に調整する。

### F. tool 固有指示が system prompt に肥大化している

- 兆候: 各 tool の入力、失敗時対応、side effect、retry policy が system prompt に大量にある。
- 対応: tool description へ移し、system prompt には共通 tool policy と permission boundary だけを残す。

### G. tool-heavy workflow の persistence / completeness が弱い

- 兆候: 取得・検証が必要な作業で「必要なら tool を使う」だけ、empty result recovery がない。
- 対応: prerequisite lookup、dependency checks、selective parallelism、empty result recovery、coverage check を明示する。

### H. `phase` や assistant item replay を落としている

- 兆候: Responses API の returned output items を手動 replay する設計なのに `phase` の保持に触れていない。
- 対応: 手動 state 管理では assistant output item と `phase` を変更せず戻す契約を追加する。

### I. prompt 内 schema が長く、Structured Outputs を使っていない

- 兆候: JSON schema や parse-sensitive な形式を自然言語 prompt に長く埋め込む。
- 対応: Structured Outputs を標準にし、prompt には必要最小限の output intent とエラー時挙動だけを残す。

### J. prompt caching を壊す配置になっている

- 兆候: static instructions の前に日付・ユーザー固有情報・動的 retrieval context が挿入される。current date を毎回 prompt に入れる。
- 対応: static first / dynamic last に並べ替え、不要な日付注入を削る。

### K. vision / computer use の image detail 前提が古い

- 兆候: 常に縮小、常に `low`、または `auto` の挙動を旧モデル前提で説明している。
- 対応: `original` / `high` / `low` を目的別に明示し、OCR・dense UI・click accuracy では詳細保持を優先する。

### L. skill description が貧弱

- 兆候: `description` が短すぎて起動条件・スコープ・除外条件が読み取れない。
- 対応: 「起動する場面」「起動しない場面」「対象粒度」が読み取れる description に改稿する。既存 skill の description 変更は自動起動条件が変わるため、編集前に確認する。

## プロンプト書き換えの最小例

### 旧

> Use GPT-5.5 with high reasoning. Think step by step. Follow this 14-step process every time. Use the search tool if needed. Return JSON using the schema described below. Today is 2026-05-02.

### 新

> Complete the task with the following contract.
>
> - Outcome: <expected result>
> - Success criteria: <measurable checks>
> - Constraints: <must keep / must avoid>
> - Allowed side effects: <none / draft only / write files / external action with approval>
> - Evidence rules: <provided context only / retrieved sources with citations / codebase inspection required>
> - Output shape: <short prose / table / structured output name>
> - Completion rule: stop only after every requested item is covered or marked `[blocked]` with the missing input.

API 側は、まず `reasoning.effort: medium` と `text.verbosity` の適切な値から評価する。parse-sensitive な出力は Structured Outputs を使う。

## ユーザーへの確認が必須なケース

次のいずれかに該当するときは、編集前に必ずユーザー確認を取る。

- 中央モデルレジストリの書き換え。
- `AGENTS.md` / `CLAUDE.md` の構造的書き換え。
- 既存 skill の `description` 変更。
- API クライアントコード、tool handler、provider adapter の編集。
- irreversible side effect を持つ tool policy の変更。

## 完了条件

- 対象ファイル群に対し、上記「典型修正パターン」の違反が残っていない、または残置理由が artifact / ADR / 作業結果で説明されている。
- OpenAI 公式 docs の現行記述と、モデル ID、`reasoning.effort`、`text.verbosity`、image detail、`phase`、Structured Outputs、tool guidance の扱いが矛盾していない。
- 中央 SoT と AI 別ファイル / skill / docs が矛盾していない。
- 検証結果と未検証リスクが `.context/<task>/` または作業結果に残っている。
