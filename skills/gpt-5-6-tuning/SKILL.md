---
name: gpt-5-6-tuning
description: "Audit and rewrite repository docs, skills, prompts, and agent harness scaffolding so they fit GPT-5.6 behavior and API guidance: lean prompts that state each instruction once, trimming repeated rules and no-op examples, effort baselines carried from GPT-5.5 then tested one level lower, none-to-max effort ladder, default-concise output with intentional text.verbosity, explicit autonomy boundaries naming safe actions, eval-gated Pro Mode, persisted reasoning context, bounded programmatic tool calling, scoped tool exposure, cache-friendly static-first layout, and sol/terra/luna variant allocation kept in the resolver. Use when the user wants to migrate or readiness-check prompts, AGENTS.md / CLAUDE.md / skill files, agent rules, or eval harnesses for GPT-5.6. Do not use for broad OpenAI SDK migrations or application feature rewrites beyond prompt, model, and orchestration guidance."
---

# GPT-5.6 Tuning

リポジトリのドキュメント・スキル・プロンプト・エージェント運用ルールを GPT-5.6 の挙動に合わせて整備するためのスキル。

本スキルは **人間やエージェントが読む運用文書・プロンプト側** の整備に特化する。SDK 移行、API クライアント実装、プロダクト機能の作り替えは、OpenAI 公式 docs を確認したうえで別タスクとして扱う。

## 起動する場面

- ユーザーが「GPT-5.6 向けに整備したい」「GPT-5.6 readiness」「GPT-5.6 prompt tuning」「5.6 系(sol / terra / luna)対応」と発話した。
- 既存の `AGENTS.md` / `CLAUDE.md` / `SKILL.md` / `docs/**` / `prompts/**` / `rules/**` が GPT-5.5 以前の前提に寄っていないか棚卸しを依頼された。
- 肥大化した system prompt(繰り返しルール、無効 example、tool description の重複)、旧 brevity 指示、autonomy boundary の曖昧さ、Pro Mode / persisted reasoning / PTC の扱いを整理したい。

## 起動しない場面

- OpenAI SDK、Responses API 呼び出し、tool handler、認証、provider adapter を広く書き換える場合。
- 単発の OpenAI API 質問に答えるだけで、文書やプロンプトの改修を伴わない場合。
- モデル選定や最新 API 仕様の確認のみが目的の場合。

## 参照する公式ソース

作業中、迷ったら OpenAI 公式 docs を直接確認する。日付・パラメータ・推奨値は変わり得るため、古い記憶で断定しない。

- Using GPT-5.6: <https://developers.openai.com/api/docs/guides/latest-model?model=gpt-5.6>
- GPT-5.6 Prompt Guidance: <https://developers.openai.com/api/docs/guides/prompt-guidance?model=gpt-5.6>
- Models: <https://developers.openai.com/api/docs/models>
- Reasoning models: <https://developers.openai.com/api/docs/guides/reasoning>
- Structured outputs: <https://developers.openai.com/api/docs/guides/structured-outputs>
- Prompt caching: <https://developers.openai.com/api/docs/guides/prompt-caching>

## GPT-5.6 で押さえる項目

1. **rewrite ではなく trim(5.5 との違い)**
   GPT-5.5 への移行は fresh baseline が推奨だったが、5.6 は既存 5.5 プロンプトを土台に **削る** 方向が公式推奨。繰り返しルール、挙動を変えない style 指示、無効 example、モデルが確実にこなす process step を削除する。内部評価では lean 化で score +10-15%、tokens -41〜66%。
2. **各指示は一度だけ述べる**
   同じルールの再掲・強調の重複は削る。example は product 要件をエンコードするものだけ残す。
3. **`reasoning.effort` は現行 baseline から 1 段下げをテスト**
   5.5/5.4 からの移行は現行 effort を baseline に、1 段下げて品質が保てるか評価する。新規は `medium` 起点。`none`〜`max` の 6 段があり、`max` は品質最優先ワークロード限定。
4. **既定でより簡潔 — brevity 指示を見直す**
   5.6 は 5.5 より簡潔に応答する。旧 brevity 指示は不要になりうるため、残す前に再評価する。一貫した長さ制御は `text.verbosity`、task 固有の要求は prompt で指定する。
5. **Autonomy boundary は安全アクションを明示列挙**
   routine な local action は無承認で実行を許可し、external write・破壊的操作・scope 拡大は承認必須にする。「安全なアクション」を名指しで列挙するのが公式推奨。
6. **Pro Mode は eval-gated**
   `reasoning.mode: "pro"` は品質がレイテンシより重要な単一回答向け。eval で効果を確認してから採用し、既定にはしない。
7. **Persisted reasoning を multi-turn 設計に組み込む**
   `reasoning.context`(`auto` / `all_turns` / `current_turn`)で reasoning を turn 間で再利用できる。長い agentic workflow の状態管理文書に扱いを明記する。
8. **PTC は bounded workflow 限定**
   Programmatic Tool Calling(JS で tool を束ねて hosted runtime 実行)は、複数結果をコードで縮約する定型 workflow に使う。各結果が次の判断を変える場合や承認が必要な場合は使わない。program output と final message の両方を検収する。
9. **Tool は scope を絞って公開**
   タスクに関係する tool だけを公開する。tool 固有の指示は tool description へ(system prompt には共通方針のみ)。
10. **Prompt caching は static-first**
    explicit prompt caching は write 1.25× / read 割引。静的指示を前、動的 context を後ろに置き、不要な日付注入を削る。
11. **Variant 配分は resolver に置く**
    `gpt-5.6-sol`(flagship)/ `gpt-5.6-terra`(低コスト)/ `gpt-5.6-luna`(高ボリューム)の role 配分は中央 resolver / registry / ADR に置き、skill 本文へ固定しない(例示する場合は non-authoritative と明記)。
12. **実行経路は codex-cli-runner の prompt profile が担う**
    GPT-5.6 の CLI 実行は `codex-cli-runner` の `gpt-5-6` prompt profile が世代補正を注入する。role prompt に世代補正を固定しない。

## 実行モード判定

依頼を受けたら、監査や編集に入る前に以下の順で実行モードを決める。判定結果は artifact または作業結果に 1 行残す。

1. 依頼に複数の合理的解釈があり、設計判断や合意形成を伴う場合は、確認フローで依頼を完全指定にしてから再判定する。
2. 中央モデルレジストリ、`AGENTS.md` / `CLAUDE.md` の構造変更、既存 skill description 変更、複数ファイル横断改修は Plan を提示してから監査フローへ進む。
3. 依頼が明確で変更が局所かつ破壊性がない場合は単発処理とし、「典型修正パターン」だけ参照して小さく直す。

## 監査フロー

Phase を持つ作業では `.context/<task>/` に artifact を残し、各 Phase の完了条件にする。

### Phase 1: スコープ確定

- 対象ファイル群を列挙する。
- 中央 model registry / resolver の有無と variant 配分の所在を確認する。
- API クライアント側変更を対象外として切り分ける。
- GPT-5.5 以前の前提の語句を `rg` で洗い出す。

artifact: `.context/<task>/01-scope.md`

### Phase 2: 監査

各対象を「典型修正パターン」と照合し、`path:line`、パターン記号、理由、推奨アクションを記録する。

artifact: `.context/<task>/02-audit.md`

### Phase 3: 改修

正規指示ファイルや model registry を SoT として、重複を増やさず最小修正する。skill description を変更する場合は起動条件が変わるため特に明示する。

artifact: `.context/<task>/03-changes.md`

### Phase 4: 検証

- repo の docs lint、skill validation、prompt eval があれば実行する。
- lean 化した prompt は削減前後の A/B(代表タスクの dry run)で品質維持を確認する。
- API パラメータに触れた場合は OpenAI 公式 docs の現行記述と照合する。

artifact: `.context/<task>/04-verify.md`

## 典型修正パターン

### A. 5.5 前提の全面 rewrite 方針が残っている

- 兆候: 「5.6 移行はゼロから prompt を作り直す」と書いている。
- 対応: 既存 5.5 prompt を土台に trim する方針(繰り返し・無効 example・不要 process step の削除)へ置換する。

### B. 指示の重複・強調の再掲

- 兆候: 同じルールが複数箇所で再掲・強調されている。CRITICAL / MUST の重ね掛け。
- 対応: 各指示を一度だけ述べる形に統合する。

### C. effort 固定や魔法語での代用

- 兆候: 全 route `high` / `xhigh` 固定、`think hard` / `step by step` を effort 代替に使用。
- 対応: 現行 baseline から 1 段下げテスト、新規は `medium` 起点、`max` は品質最優先のみ、eval-gated escalation に書き換える。

### D. 旧 brevity 指示の持ち越し

- 兆候: 5.5 向けの「簡潔に」「短く」指示が多数残っている。
- 対応: 5.6 は既定で簡潔。brevity 指示は再評価して削るか、`text.verbosity` と task 固有指定へ置き換える。

### E. Autonomy boundary が曖昧

- 兆候: 何を無承認で実行してよいか列挙がない、または全アクションに承認を要求。
- 対応: 安全な routine local action を名指しで列挙して無承認許可し、external write・破壊的操作・scope 拡大だけ承認必須にする。

### F. Pro Mode の乱用・未評価採用

- 兆候: `reasoning.mode: "pro"` を既定にしている、または latency-sensitive 経路で使っている。
- 対応: eval で品質向上を確認した品質最優先経路だけに限定する。

### G. Persisted reasoning 未考慮

- 兆候: multi-turn agentic workflow の文書に `reasoning.context` の扱いがない。
- 対応: `auto` / `all_turns` / `current_turn` の選択と再開時の挙動を運用文書に明記する。

### H. PTC の誤適用

- 兆候: 結果ごとに判断が変わる workflow や承認が必要な操作に PTC を使っている。program output だけ検収している。
- 対応: bounded workflow に限定し、program output と final message の両方を検収する。

### I. Tool 公開範囲が過大

- 兆候: タスクに無関係な tool まで常時公開、tool 固有指示が system prompt に肥大化。
- 対応: タスク関連 tool だけに絞り、tool 固有指示は tool description へ移す。

### J. Prompt caching を壊す配置

- 兆候: static 指示の前に日付・ユーザー固有情報・動的 context が挿入される。
- 対応: static first / dynamic last に並べ替え、不要な日付注入を削る。

### K. Variant 配分が skill 本文に固定されている

- 兆候: 「researcher は gpt-5.6-sol」等が skill 本文で正本化されている。
- 対応: 配分は resolver / registry / ADR へ移し、skill には resolver 参照だけ残す(例示は non-authoritative と明記)。

### L. Skill description が貧弱

- 兆候: 起動条件・スコープ・除外条件が description から読み取れない。
- 対応: literal に解釈できる description へ改稿する。変更前後で誤発火と不発火を確認する。

## プロンプト書き換えの最小例

### 旧

> あなたは慎重なアシスタントです。必ず step by step で考えてください。重要: 出力は必ず簡潔に。繰り返しますが、簡潔にしてください。以下の 12 の手順に従ってください: 1) ... 12) ...。全ツールを自由に使ってください。

### 新

> Outcome: <期待成果>
> Success criteria: <検証可能な完了条件>
> Allowed side effects: <安全な routine local action の列挙は無承認可 / external write・破壊的操作・scope 拡大は要承認>
> Output shape: <形式>
> Completion rule: 全項目を完了するか、`[blocked]` と不足入力を明示して停止する。

API 側は現行 effort を baseline に 1 段下げをテストし、長さは `text.verbosity` で制御する。公開する tool はタスク関連に絞る。

## ユーザーへの確認が必須なケース

- 中央モデルレジストリの書き換え。
- `AGENTS.md` / `CLAUDE.md` の構造的書き換え。
- 既存 skill の `description` 変更。
- API クライアントコード、tool handler、provider adapter の編集。
- irreversible side effect を持つ tool policy の変更。

## 完了条件

- 対象ファイル群に「典型修正パターン」の違反が残っていない、または残置理由が artifact / ADR / 作業結果で説明されている。
- OpenAI 公式 docs の現行記述と、effort baseline 方針、`text.verbosity`、autonomy boundary、Pro Mode、persisted reasoning、PTC、caching、variant 配分の扱いが矛盾していない。
- lean 化は削減前後の検証(A/B または代表 dry run)で品質維持が確認されているか、未検証リスクとして明記されている。
- 中央 SoT と AI 別ファイル / skill / docs が矛盾していない。
- 検証結果と未検証リスクが `.context/<task>/` または作業結果に残っている。
