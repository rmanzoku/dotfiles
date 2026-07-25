---
name: fable-5-tuning
description: "Audit and rewrite repository docs, skills, prompts, and agent harness scaffolding so they fit Claude Fable 5 behavior and API guidance: explicit opt-in adoption above the Opus tier, always-on thinking with no thinking configuration, summarized-only reasoning visibility, no assistant prefill, 30-day data retention requirement, minutes-long turns with async check-ins, full effort sweeps where low/medium rival prior flagships, de-prescribed goal-and-constraints prompts, encouraged asynchronous subagent delegation, explicit self-verification harnesses with fresh-context verifiers, scope and autonomy boundaries, grounded progress claims, memory surfaces, refusal handling, and long-session readability. Use when the user wants to migrate or readiness-check prompts, AGENTS.md / CLAUDE.md / skill files, agent rules, or eval harnesses for Claude Fable 5 or Claude Mythos 5. Do not use for broad Claude SDK migrations or application feature rewrites beyond prompt, model, and orchestration guidance."
---

# Fable 5 Tuning

リポジトリのドキュメント、スキル、プロンプト、agent harness を Claude Fable 5(および同一仕様の Claude Mythos 5)に合わせて整備するためのスキル。

API クライアントコードの自動移行は対象外。SDK や Messages API 呼び出しの実装修正は公式 Claude API 移行手順へ委譲し、本スキルは人間と AI が読む運用文書・プロンプト・ハーネス設計に集中する。

## 起動する場面

- ユーザーが「Fable 5 向けに整備したい」「Fable 5 migration」「Fable 5 readiness」「Mythos 5 対応」と発話した。
- 長期自律作業・ゼロベース監査など Fable 5 を明示採用する workflow の文書・プロンプトを整備する。
- 旧モデル向けの step-by-step scaffolding、委譲抑制 guardrail、進捗報告前提、context 残量表示を見直す。

## 起動しない場面

- Claude SDK / API 呼び出しコード自体の移行。
- 「最新モデルへ更新」という一般依頼。既定のアップグレード先は Opus 系であり、Fable 5 はユーザーが明示選択した場合だけ対象にする(`opus-5-tuning` を参照)。
- 単発の質問応答で文書編集や監査を伴わない場合。

## 参照する公式ソース

作業中は最新の公式ドキュメントを確認する。

- Introducing Claude Fable 5 and Claude Mythos 5: <https://platform.claude.com/docs/en/about-claude/models/introducing-claude-fable-5-and-claude-mythos-5>
- Prompting Claude Fable 5: <https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5>
- Migration guide: <https://platform.claude.com/docs/en/about-claude/models/migration-guide>
- Effort: <https://platform.claude.com/docs/en/build-with-claude/effort>
- Prompt caching: <https://platform.claude.com/docs/en/build-with-claude/prompt-caching>
- 発表: <https://www.anthropic.com/news/claude-fable-5-mythos-5>

## Fable 5 で押さえる項目

1. **明示採用のみ・前提条件を先に確認**
   価格は Opus tier より上($10/$50)。30 日 data retention が必須で、ZDR 組織は全リクエスト 400 になる。機密性・予算・retention 境界の引き受けを caller が明示した workflow だけを対象にする。
2. **thinking 設定は全削除**
   thinking は常時 ON。`{type: "disabled"}` も `{type: "enabled", budget_tokens}` も 400。raw CoT は返らず、`display: "summarized"` で要約のみ得られる。reasoning を表示する製品は要約表示へ切り替える。prefill も非対応。
3. **長 turn 前提の設計**
   高 effort の難タスクは 1 リクエスト数分かかりうる。timeout、streaming、async な進捗確認、progress UX を前提に文書化する。「即応答」を前提にした運用手順は書き換える。
4. **Effort は low/medium を含めて sweep**
   low/medium でも旧世代 flagship の xhigh/max に匹敵しうる。既定は high、capability-sensitive は xhigh。作業が正しく終わるのに時間がかかりすぎる場合は effort を下げる。
5. **De-prescribe: 手順書ではなく goal + constraints**
   旧モデル向けの過剰に prescriptive な step-by-step scaffolding は Fable 5 の出力品質をむしろ下げる。目標・制約・完了条件を示し、手順の列挙は削る方向で A/B する。
6. **委譲は奨励し async にする(Opus 5 と逆)**
   parallel subagent は信頼できる。委譲抑制の guardrail は撤去し、「いつ委譲すべきか」を明示する。spawn-and-block より async 通信(長命 subagent が context を保持)を推奨する。
7. **自己検証は明示的に組み込む(Opus 5 と逆)**
   長期 build では「自分の検証 harness を確立し一定周期で実行する」ことを指示し、self-critique より fresh-context の verifier subagent を推奨する。
8. **スコープ境界と自律動作**
   相談・質問には assessment で止め、依頼されていない隣接アクションを取らない境界を明示する。一方で自律 pipeline では「可逆な in-scope 作業は許可を求めず進める」「計画や約束だけで turn を終えない」指示を入れる(early stopping 対策)。
9. **進捗主張は tool result で裏取り**
   長期作業では「進捗報告の各主張を今セッションの tool result と突き合わせ、未検証は未検証と明示する」指示を入れる。
10. **Memory surface と intent**
    学びを書き込む場所(単純な `.md` でよい)と書式を与えると性能が上がる。依頼には背景・誰のためか・何を可能にするかの intent を添える。
11. **Context anxiety と長セッションの readability**
    context 残量カウントを見せると自発的に切り上げようとすることがある。残量表示を避けるか「context は十分。切り上げるな」を入れる。長セッションの最終サマリは「見ていなかった読者への再接地」として書かせる。
12. **Refusal / fallback**
    research biology・cybersecurity の多くは対象外ドメインで、隣接する正当作業でも classifier が false positive しうる。`stop_reason: "refusal"` を content 読み取り前に処理し、fallback へのオプトインを既定とする。Fable の thinking block は他モデルへの replay 時に drop される(課金されない)。
13. **実行経路は Claude CLI に限らない**
    Fable 5 は `claude-cli-runner` だけでなく `copilot-cli-runner` など他 CLI runner 経由でも実行される。世代固有の挙動補正は各 runner の prompt profile(model adapter)が担い、role prompt や skill 本文へ固定しない。Copilot 経由では hard AI-credit cap・retention 境界の明示引き受けが必須(runner skill の契約に従う)。

## Opus 5 との反転で事故りやすい点

同時期のモデルでも補正方向が逆の項目がある。文書がどちらの世代向けかを必ず明示する。

| 項目 | Opus 5 | Fable 5 |
|---|---|---|
| Subagent 委譲 | cap する(過委譲傾向) | 奨励し async にする(信頼できる) |
| 自己検証 | scaffolding を削除(組み込み済み) | 明示的に harness 化(fresh-context verifier 推奨) |
| 手順の粒度 | literal 実行前提で明確化 | de-prescribe(goal + constraints へ) |
| thinking | 既定 ON、disabled は effort high 以下 | 常時 ON、設定自体を削除 |

## 実行モード判定

依頼を受けたら、編集前に次を決める。判定結果は artifact または作業結果に残す。

1. 複数の合理的解釈がある、または設計合意が必要な場合は、確認してから進める。
2. 中央モデル registry、`CLAUDE.md` / `AGENTS.md` 構造、既存 skill description、複数ファイル横断の破壊的変更を伴う場合は、Plan を提示してから実装する。
3. 明確で局所的な修正なら単発処理として進める。

## 監査フロー

Phase を持つ作業では `.context/<task>/` に artifact を残し、各 Phase の完了条件にする。

### Phase 1: スコープ確定

- 対象ファイル群を列挙する。
- Fable 5 採用の前提(明示選択、retention、予算 cap)が文書化されているか確認する。
- API コード側変更を対象外として切り分ける。
- 旧 Opus / Sonnet 前提の語句を `rg` で洗い出す。

artifact: `.context/<task>/01-scope.md`

### Phase 2: 監査

各対象を「典型修正パターン」と照合し、`path:line`、パターン記号、理由、推奨アクションを記録する。

artifact: `.context/<task>/02-audit.md`

### Phase 3: 改修

正規指示ファイルや model registry を SoT として、重複を増やさず最小修正する。skill description を変更する場合は起動条件が変わるため特に明示する。

artifact: `.context/<task>/03-changes.md`

### Phase 4: 検証

- `scripts/skill-quick-validate <skill-dir>` など repo の検証を実行する。
- `rg` で stale な旧モデル前提の残存を確認する。
- 可能なら旧 scaffolding を外した版との A/B で読み解きやすさ・品質を確認する。

artifact: `.context/<task>/04-verify.md`

## 典型修正パターン

### A. thinking 設定が残っている

- 兆候: `thinking: {type: "disabled"}`、`budget_tokens`、thinking の on/off 記述。
- 対応: thinking 設定を全削除し、深さは `output_config.effort` で扱う。reasoning 表示は `display: "summarized"` 前提へ。

### B. Prefill 前提が残っている

- 兆候: 末尾 assistant prefill で出力形式や続きを強制している。
- 対応: structured outputs(`output_config.format`)または system 指示へ置き換える。

### C. 過剰 prescriptive な scaffolding

- 兆候: 旧モデル向けの詳細な step-by-step 手順、固定 checklist の強制。
- 対応: goal・constraints・完了条件へ de-prescribe し、旧 scaffolding 除去版と A/B する。

### D. 委譲抑制 guardrail が残っている

- 兆候: 「subagent を使うな」「委譲は最小限に」等の旧モデル向け抑制。
- 対応: 撤去し、委譲が望ましい条件と async 通信(長命 subagent、逐次報告)を明示する。

### E. 検証 harness の欠如

- 兆候: 長期 build の workflow に自己検証の仕組みがない。
- 対応: 「検証方法を確立して周期実行」「fresh-context verifier subagent で仕様照合」を明示する(Opus 5 の「検証 scaffolding 削除」と逆方向であることに注意)。

### F. 短 turn 前提の運用

- 兆候: 即応答前提の timeout、同期ブロッキングの進捗確認、固定進捗報告 scaffolding。
- 対応: 長 turn 前提の timeout / streaming / async 確認へ書き換え、強制進捗 scaffolding は削除する。

### G. スコープ・自律性指示の欠如

- 兆候: assessment 依頼で修正まで実行しうる prompt、または自律 pipeline で許可待ち・計画だけの turn 終了が起きうる prompt。
- 対応: 「相談は assessment で止める」「可逆な in-scope 作業は許可を求めず進める」「進捗主張は tool result で裏取り」を追加する。

### H. Memory surface がない

- 兆候: 長期・反復作業なのに学びの書き込み先がない。
- 対応: 書き込み先ファイル・書式・参照タイミングを指定する。

### I. Refusal / retention 未考慮

- 兆候: `stop_reason` 処理や fallback 方針がない、ZDR / retention 条件を確認していない。
- 対応: refusal 処理と fallback オプトインを既定化し、retention 前提を採用条件として文書化する。

### J. Context 残量の露出

- 兆候: harness が残 token カウントを表示している、または「context を節約せよ」指示がある。
- 対応: 残量表示を避けるか、「context は十分にある。切り上げ・要約・新セッション提案をするな」を追加する。

### K. Skill description が弱い

- 兆候: 起動条件、除外条件、対象粒度が description から読めない。
- 対応: literal に解釈できる description へ更新する。変更前後で誤発火と不発火を確認する。

## プロンプト書き換え最小例

旧:

> 次の手順を順に実行してください: 1) ... 2) ... 3) ...(詳細な手順列挙)。subagent は使わず、3 tool call ごとに進捗を報告してください。

新:

> Goal: <目的と完了条件>
> Constraints: <制約・許可される副作用・retention/予算前提>
> 独立して並列化できる部分は subagent へ委譲し、async に進捗を受け取りながら作業を続けてください。検証方法を自分で確立し、一定周期で仕様と照合してください。進捗報告の各主張は tool result で裏付け、未検証項目は未検証と明示してください。

`effort` は呼び出し側で設定する。既定は `high`、capability-sensitive は `xhigh`。`low` / `medium` も sweep 対象にする。

## 完了条件

- Fable 5 採用の前提(明示選択・retention・予算 cap)と実行経路(claude-cli-runner / copilot-cli-runner 等)が文書化されている。
- 対象ファイルに thinking 設定・prefill・過剰 prescriptive scaffolding・委譲抑制・短 turn 前提が残っていない。
- 委譲奨励 / 明示的検証 harness / scope・自律性 / 進捗裏取り / memory / refusal 方針が公式ドキュメントと矛盾せず、Opus 5 向け文書と混同されない形で世代が明示されている。
- API コード変更と文書 / prompt tuning の責務が分離されている。
- 変更根拠、検証結果、残置理由が artifact または作業結果に残っている。
