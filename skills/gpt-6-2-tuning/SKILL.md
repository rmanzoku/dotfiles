---
name: gpt-6-2-tuning
description: "Audit and rewrite prompts, AGENTS.md / CLAUDE.md, skills, and agent harness scaffolding for GPT-6.2 (gpt-6.2-astra, gpt-6.2-sol): stopping to propose next steps, routine confirmations, verification passes, carried-over brevity rules, instruction placement, and prefix edits. Use to migrate or readiness-check prompts for GPT-6.2. Not for broad SDK migrations."
---

# GPT-6.2 Tuning

リポジトリのドキュメント・スキル・プロンプト・エージェント運用ルールを GPT-6.2 世代（`gpt-6.2-astra`、`gpt-6.2-sol`）の挙動に合わせて整備するためのスキル。

本スキルは **人間やエージェントが読む運用文書・プロンプト側** の整備に特化する。SDK 移行、API クライアント実装、プロダクト機能の作り替えは、OpenAI 公式 docs を確認したうえで別タスクとして扱う。GPT-6 / 6.1 / 6-luna 向けの整備は `gpt-6-tuning` を使う。

## 起動する場面

- ユーザーが「GPT-6.2 向けに整備したい」「GPT-6.2 readiness」「GPT-6.2 prompt tuning」「6.2-astra / 6.2-sol 対応」と発話した。
- GPT-6 / 6.1 向けに整えた prompt や skill を GPT-6.2 へ移す。
- GPT-6.2 が次の手を提案して止まる、定型的な確認で止まる、最終確認を省いて終える、といった症状を prompt 側で直したい。

## 起動しない場面

- OpenAI SDK、Responses API 呼び出し、tool handler、認証、provider adapter を広く書き換える場合。
- 単発の OpenAI API 質問に答えるだけで、文書やプロンプトの改修を伴わない場合。
- モデル選定や最新 API 仕様の確認のみが目的の場合。

## 参照する公式ソース

作業中、迷ったら OpenAI 公式 docs を直接確認する。日付・パラメータ・推奨値は変わり得るため、古い記憶で断定しない。公式の prompting guidance は GPT-6.2 Astra と Sol で観察された挙動として、両 variant に共通の内容で書かれている。

- Using GPT-6.2: <https://developers.openai.com/api/docs/guides/latest-model>（`?model=gpt-6.2-astra` / `?model=gpt-6.2-sol` で variant 別の表示。同じページに Migration quickstart と Prompting best practices がある）
- Keep the prefix unchanged: <https://developers.openai.com/api/docs/guides/keep-prefix-unchanged>
- Prompt caching: <https://developers.openai.com/api/docs/guides/prompt-caching>
- Async tool calling: <https://developers.openai.com/api/docs/guides/async-tool-calling>
- Models: <https://developers.openai.com/api/docs/models>
- Codex prompting: <https://developers.openai.com/codex/prompting>

## GPT-6 / 6.1 との違い

GPT-6 向けの補正をそのまま持ち込むと、向きが逆になる項目がある。移行時は次を見直す。

| 観点 | GPT-6 / 6.1 向け（`gpt-6-tuning`） | GPT-6.2 |
|---|---|---|
| 止まり方 | 確認質問をしすぎる | 次の手を提案して確認を待つ。権限があっても計画や引き継ぎでターンを終えがち |
| 検証 | 検証・テストをやりすぎるので量を絞る | 依頼の各項目を網羅的に確かめる最終パスを求める。テストの追加は依頼・repo 要件・特定の回帰に限る |
| 文体 | リスト中心になりやすいので書式を指定する | 既定で簡潔・直接的。「簡潔に」の指示は見直す |
| 安定した指示の置き場所 | 特記なし | Responses の top-level `instructions` は `input` の後ろに付く。キャッシュしたい指示は `input` 先頭の `developer` message に置く |
| 会話履歴の編集 | 特記なし | 途中の履歴編集やモデル変更で reasoning item が捨てられる。prefix を変えない |

## GPT-6.2 で押さえる項目

1. **作り直さず監査する**
   既存 prompt は土台として残す。モデルが読む skill・AGENTS.md・docs のうち、GPT-6 以前の補正を持ち込んで逆効果になっている指示を探す。
2. **提案で止まる癖を補正する**
   権限がある作業は、計画・定型的な判断の依頼・引き継ぎでターンを終えず、最後まで進めさせる。確認を求めてよいのは、大きな scope 変更、具体的な障害、利用者にしか決められない判断、不可逆または破壊的な操作の前に限る。共通ルール `## 可逆性と自走範囲` の 3 条件は維持し、それ以外の定型的な確認要求を削る。
3. **曖昧さは可逆な仮定で進める**
   選択肢を並べて止まる、作業の申し出だけで終える、部分的な答えで終える、を避けさせる。妥当で可逆な仮定を置いて進め、仮定は明示させる。
4. **完了前に網羅的な確認パスを求める**
   長いタスクでは、終える前に依頼の各項目を満たしたかを 1 つずつ確かめさせる。GPT-6 向けの「検証を絞る」文言は、テスト量の話（項目 5）と分けて読み替える。長いタスクで最終確認まで粘らせたいときは effort を上げる選択肢がある。
5. **テストは必要なときだけ足す**
   テストの追加は、依頼されたとき、repo が求めるとき、特定の回帰を防ぐときに限る。既存の挙動に依存する呼び出し元を壊さないこと、既存のロジックと API を再利用することを求める。可読性を優先し、code golf、圧縮した書式、過度な間接化や抽象化を避けさせる。
6. **簡潔さの指示を持ち越さない**
   既定で簡潔・直接的なので、「簡潔に」「短く」の指示は見直す。必要なら、利用者の用語を使う、要点を先に書く、能動態で書く、推論を追える程度の文脈を残す、を指定する。外部向けの文書では読み手に合わせさせる。
7. **長いタスクの最終回答は単独で読める形にする**
   最終回答では途中経過が折りたたまれる。最終回答を、作業を初めて見る読み手向けの自己完結した報告にさせ、途中の略語・推論の言い回し・subagent や自動化の用語を持ち込ませない。
8. **安定した指示は先頭の developer message に置く**
   Responses API の top-level `instructions` は 6.2 から `input` の後ろに付く。キャッシュしたい安定した規則は `input` 先頭の `developer` message に置き、`instructions` はリクエストごとの指示だけにする。
9. **prefix を変えない**
   会話途中の履歴編集、一部のモデル変更（ダウングレードを含む）、end user や organization の変更で reasoning item が捨てられ、品質低下とトークン増につながる。過去の developer message や tool call を書き換える harness は見直す。
10. **effort は `medium` から始める**
    新規の連携は `medium` から始める。`none` / `minimal` を使っていたら `low` に置き換える。effort の全段階と既定値は公式ページに明記がないので、使う段階は公式の reasoning guide とモデルページで確かめる。Codex の model catalog 上の既定は両 variant とも `low`。
11. **非同期の質問 tool を検討する**
    利用者への質問が必要でも独立した作業を止めたくない harness では、`request_user_input_async` のような非同期の質問 tool で、質問しながら作業を続けさせる。
12. **Variant 配分は resolver に置く**
    `gpt-6.2-astra`（最難度）と `gpt-6.2-sol`（複雑な作業を低コストで）の役割配分は、中央 resolver / registry / ADR に置き、skill 本文に固定しない。
13. **Codex 組み込み指示と重複させない**
    Codex 経由で使う prompt には、Codex の base instructions がすでに注入している行動の偏りなどを再掲せず、タスク固有の契約だけを書く。GPT-6.2 用の base instructions の中身は未確認なので、重なりは実物で確かめる。
14. **実行経路は codex-runner の prompt profile が担う**
    `codex-runner` は `gpt-6.2-*` にも `gpt-6` prompt profile を当てる。adapter の内容（契約の完遂、可逆な作業は確認なしで進める、検証はリスクに比例）は 6.2 のガイドと矛盾しない。role prompt に世代補正を固定しない。

## 未確認事項

公式資料やローカル証拠で確認できていない。断定せず、必要なら代表タスクで確かめる。

- reasoning effort の全段階、既定値、`none` / `minimal` が拒否されるか（公式ページは移行時に `low` へ置き換えるよう勧めるだけ）。
- Codex の GPT-6.2 用 base instructions の内容と、本スキルの補正との重なり。
- Sol と Astra で挙動の傾向に差があるか（公式の prompting guidance は共通）。
- GPT-6 で観察された確認しすぎ・テストしすぎが 6.2 でも残るか。

## 実行モード判定

依頼を受けたら、監査や編集に入る前に以下の順で実行モードを決める。判定結果は artifact または作業結果に 1 行残す。

1. 中央モデルレジストリや `AGENTS.md` / `CLAUDE.md` の構造変更を伴う場合は Plan を提示してから監査フローへ進む。
2. 依頼が明確で変更が局所なら単発処理とし、「典型修正パターン」だけ参照して小さく直す。それ以外は監査フローへ進む。

## 監査フロー

Phase を持つ作業では `.context/<task>/` に artifact を残し、各 Phase の完了条件にする。

### Phase 1: スコープ確定

- 対象ファイル群を列挙する。
- 中央 model registry / resolver の有無と variant 配分の所在を確認する。
- API クライアント側変更を対象外として切り分ける。
- 持ち越しの語句（「簡潔に」「必ず確認」「テストを絞る」「各ステップで承認」、top-level `instructions` への規則の集約、履歴を書き換える処理など）を `rg` で洗い出す。

artifact: `.context/<task>/01-scope.md`

### Phase 2: 監査

各対象を「典型修正パターン」と照合し、`path:line`、パターン記号、理由、推奨アクションを記録する。

artifact: `.context/<task>/02-audit.md`

### Phase 3: 改修

正規指示ファイルや model registry を SoT として、重複を増やさず最小修正する。skill description を変更する場合は起動条件が変わるため特に明示する。

artifact: `.context/<task>/03-changes.md`

### Phase 4: 検証

- repo の docs lint、skill validation、prompt eval があれば実行する。
- 変更した prompt は、変更前後で代表タスクを実行し、提案で止まった回数・確認質問・最終確認の有無・完了率を比較する。
- API パラメータに触れた場合は OpenAI 公式 docs の現行記述と照合する。

artifact: `.context/<task>/04-verify.md`

## 典型修正パターン

### A. 定型的な確認・承認を求める文言

- 兆候: 「各ステップで承認を得る」「計画を示して確認を待つ」「不明点があれば必ず確認する」。
- 対応: 確認は大きな scope 変更・具体的な障害・利用者にしか決められない判断・3 条件を満たさない操作に限定し、それ以外は可逆な仮定で進めさせる。

### B. 提案や引き継ぎで終える構造

- 兆候: 完了条件がなく、「次は〜できます」で終えても成功扱いになる。
- 対応: 検証可能な完了条件を先に書き、権限がある作業は最後まで実行させる。

### C. 最終確認がない

- 兆候: 長いタスクで、終える前に依頼の各項目を照合させる指示がない。
- 対応: 依頼の各項目を 1 つずつ確かめる最終パスを完了条件に入れる。

### D. GPT-6 向けの「検証を絞る」文言の持ち越し

- 兆候: 「検証は最小限に」「テストを省く」が、依頼項目の確認まで省かせる書き方になっている。
- 対応: 依頼項目の確認とテストの追加を分ける。確認は網羅的に、テストの追加は依頼・repo 要件・回帰に限る。

### E. 簡潔さの指示の持ち越し

- 兆候: 「簡潔に」「短く答える」が system prompt に残っている。
- 対応: 削るか、読み手・要点の順番・用語の指定に置き換える。

### F. 最終回答に作業中の言葉が残る

- 兆候: 長いタスクの最終回答に、略語・subagent 名・途中の推論の言い回しが出る。
- 対応: 最終回答を自己完結した報告にする指示を足す。

### G. 安定した規則が top-level `instructions` にある

- 兆候: Responses API の `instructions` に、毎回同じ規則をまとめている。
- 対応: 安定した規則は `input` 先頭の `developer` message に移し、`instructions` はリクエストごとの指示だけにする。

### H. 履歴を書き換える harness

- 兆候: 過去の developer message や tool call を要約・差し替えする、会話途中でモデルを切り替える。
- 対応: prefix を変えない設計にする。必要なら公式の keep-prefix-unchanged guide に沿って組み直す。

### I. effort の持ち越し

- 兆候: `none` / `minimal` の指定、`think hard` で effort を代用。
- 対応: `low` 以上に置き換え、新規なら `medium` から始めて代表タスクで調整する。

### J. Variant 配分の固定

- 兆候: skill 本文で「worker は gpt-6.2-sol」などを正本化している。
- 対応: 配分は resolver / registry / ADR に移し、skill には resolver 参照だけ残す（例示は non-authoritative と明記）。

### K. Codex 組み込み指示の再掲

- 兆候: Codex 経由の prompt で、行動への偏りや警告抑制を繰り返し書いている。
- 対応: Codex の base instructions と重なる部分を削り、タスク固有の契約だけ残す。

### L. コーディング規約の欠落

- 兆候: 既存ロジックの再利用、呼び出し元の互換性、可読性についての指示がない。
- 対応: 既存の API を再利用し、呼び出し元が依存する挙動を保ち、過度な抽象化や圧縮した書式を避けるよう書く。

## プロンプト書き換えの最小例

### 旧（GPT-6 向け）

> 簡潔に答えてください。不明点があれば確認してください。各ステップの前に計画を示して承認を取ってください。検証は最小限にしてください。

### 新

> Outcome: <期待成果>
> Success criteria: <検証可能な完了条件>
> Allowed side effects: <可逆な in-scope 作業は無承認で可 / 3 条件を満たさない操作と scope 拡大は要承認>
> Autonomy: 権限のある作業は、計画や定型的な確認でターンを終えず最後まで進める。曖昧な点は妥当で可逆な仮定を置いて進め、仮定を明示する。
> Verification: 終える前に依頼の各項目を満たしたかを確かめる。テストは依頼・repo 要件・回帰の防止に必要なときだけ足す。
> Final answer: 作業を初めて見る読み手向けに、自己完結した形で書く。
> Completion rule: 全項目を完了するか、`[blocked]` と不足入力を明示して停止する。

## 完了条件

- 対象ファイル群に「典型修正パターン」の違反が残っていない、または残置理由が artifact / ADR / 作業結果で説明されている。
- OpenAI 公式 docs の現行記述と、止まり方の補正、最終確認、テスト量、文体、指示の置き場所、prefix、effort、variant 配分の扱いが矛盾していない。
- 変更した prompt は、変更前後の比較で改善が確認されているか、未検証リスクとして明記されている。
- 中央 SoT と AI 別ファイル / skill / docs が矛盾していない。
- 検証結果と未検証リスクが `.context/<task>/` または作業結果に残っている。
