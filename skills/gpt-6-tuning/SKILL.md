---
name: gpt-6-tuning
description: "Audit and rewrite prompts, AGENTS.md / CLAUDE.md, skills, and agent harness scaffolding for the GPT-6 family (astra, 6.1-sol, sol, luna): over-asking, early stops, skill conflicts, completion criteria, test volume, delegation, and effort. Use to migrate or readiness-check prompts for GPT-6. Not for broad SDK migrations."
---

# GPT-6 Tuning

リポジトリのドキュメント・スキル・プロンプト・エージェント運用ルールを GPT-6 世代の挙動に合わせて整備するためのスキル。

本スキルは **人間やエージェントが読む運用文書・プロンプト側** の整備に特化する。SDK 移行、API クライアント実装、プロダクト機能の作り替えは、OpenAI 公式 docs を確認したうえで別タスクとして扱う。

## 起動する場面

- ユーザーが「GPT-6 向けに整備したい」「GPT-6 readiness」「GPT-6 prompt tuning」「astra / 6.1-sol / luna 対応」と発話した。
- 既存の `AGENTS.md` / `CLAUDE.md` / `SKILL.md` / `docs/**` / `prompts/**` / `rules/**` が GPT-5.6 以前の前提に寄っていないか棚卸しを依頼された。
- GPT-6 が確認を求めすぎる、途中で止まる、skill の指示で作業を止める、テストをやりすぎる、といった症状を prompt 側で直したい。

## 起動しない場面

- OpenAI SDK、Responses API 呼び出し、tool handler、認証、provider adapter を広く書き換える場合。
- 単発の OpenAI API 質問に答えるだけで、文書やプロンプトの改修を伴わない場合。
- モデル選定や最新 API 仕様の確認のみが目的の場合。

## 参照する公式ソース

作業中、迷ったら OpenAI 公式 docs を直接確認する。日付・パラメータ・推奨値は変わり得るため、古い記憶で断定しない。公式の prompting guidance は GPT-6 Astra で観察された挙動を基準にしており、他の variant は自分のワークロードで評価するよう求めている。

- Using GPT-6: <https://developers.openai.com/api/docs/guides/latest-model>（`?model=gpt-6.1-sol` などで variant 別の表示）
- Prompt guidance: <https://developers.openai.com/api/docs/guides/prompt-guidance>（同上）
- Rethinking skills and prompts for GPT-6 Astra: <https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra>
- Models: <https://developers.openai.com/api/docs/models>
- Codex models: <https://developers.openai.com/codex/models>

## GPT-6 で押さえる項目

1. **作り直さず監査する**
   既存 prompt は土台として残し、作り直さない。代わりに、モデルが読む skill・AGENTS.md・docs に挙動を歪める指示がないかを監査する。公式はこの監査を強く推奨している。GPT-5.6 のような削減量の数値は公表されていない。
2. **確認しすぎを補正する**
   GPT-6 は以前の世代より確認質問をしやすい。文脈から意図を推定して行動に寄せ、目的を達成するまで続けるよう促す。「〜できますか」「手伝って」は実行の依頼として扱わせる。可逆な作業は完了させてから、具体的な成果物で承認を求める形にする。
3. **ユーザー指示を skill より優先させる**
   長い指示に強い一方、文脈に敏感で、曖昧または矛盾する skill の指示で早く止まる。ユーザー指示が skill の指示に優先すると明記する。skill が原因で止まったときは、該当ファイルを名指しして指示を引用させる。
4. **旧世代向けの強い制止文言を緩める**
   過剰に慎重な境界指示は生産的な作業を止める。強い許可・禁止の文言は、旧モデルが無許可で実行していた操作に限って残す。安全と分かっている workflow は個別に許可する。共通ルール `## 可逆性と自走範囲` の 3 条件は維持し、その外側に重ねた過剰な制止だけを削る。
5. **完了条件を明示する**
   最初の実装で止まりやすい。完了条件を先に書き、実行・確認・修正まで含めるならそれを依頼文に書く。追加の探索をさせたいときは、その範囲も指定する。
6. **テスト量をリスクに合わせる**
   Astra は検証をやりすぎる傾向がある。単に「テストを実行して」と言うだけの定型文は削る。可逆で影響の小さい変更ではテストを省き、変更に見合ったテストだけを実行させる。一方、Codex の Luna 用組み込み指示は「依頼がなければテストしない」なので、Luna に検証させたいときは success criteria に検証を書く。
7. **書式を指定する**
   既定ではリスト中心の書式になりやすい。散文がほしいときは「簡潔な段落で」と明示する。決まり文句や対比を使った言い回しは避けさせる。
8. **委譲を促す**
   subagent への委譲が少なくなりがち。並列化で速度や品質が上がる場面では明示的に委譲を促す。agent 間のメッセージは読みやすい形にさせる。
9. **Skill と AGENTS.md は短く、段階的に開示する**
   description は起動条件が分かる範囲で短くする。root 文書は他の文書へ案内するだけの router にする。手順を細かく決めすぎない。「編集のたびに全 docs を読む」のような一律の指示は、「schema 変更時は X.md を参照」のような条件付きにする。Sol や Luna に合わせた指示は Astra を縛りすぎることがあるので、どのモデルが読むかも考える。
10. **effort は現行を引き継ぐ**
    移行時は現在の実効 effort を維持する（GPT-5.6 の「1 段下げてテスト」とは異なる）。Astra と 6.1-sol には `none` がなく、6-sol と Luna にはある。`minimal` は `low` に置き換える。Codex には `ultra`（subagent による並列分担）があるが、Luna の上限は `max`。Codex の既定 effort は 6.1-sol が `low`、他は `medium`（API docs の 6.1-sol 既定は `medium` で、Codex とは異なる）。
11. **Variant 配分は resolver に置く**
    `gpt-6-astra`（最難度）/ `gpt-6.1-sol`（Astra に近い性能を低コストで）/ `gpt-6-sol`（前世代の workhorse）/ `gpt-6-luna`（大量処理）の役割配分は、中央 resolver / registry / ADR に置き、skill 本文に固定しない。GPT-6 に `terra` はない。
    GPT-6.1 専用の prompting guidance はなく、公式 docs で 6.1-sol に固有なのはパラメータ面だけ（effort は `low`〜`max`、`none` / `minimal` 非対応、tool calling は Responses API 必須）。挙動補正は本スキルの GPT-6 共通項目を適用し、品質とコストは代表タスクで Astra と比較して決める。
12. **Codex 組み込み指示と重複させない**
    Codex は GPT-6 用の base instructions で、行動への偏り、ユーザー指示の優先、不要な警告の抑制などをすでに注入している。Codex 経由で使う prompt にはこれらを再掲せず、タスク固有の契約だけを書く。
13. **実行経路は codex-cli-runner の prompt profile が担う**
    GPT-6 の CLI 実行では、`codex-cli-runner` の `gpt-6` / `gpt-6-luna` prompt profile が世代補正を注入する。role prompt に世代補正を固定しない。

## 未確認事項

公式資料やローカル証拠で確認できていない。断定せず、必要なら代表タスクで確かめる。

- `codex exec` で persistent mode（ターンを終えず follow-up を続ける）が有効になるか。runner の timeout 設計に影響する。
- 非対話実行での `ultra` の挙動（subagent が起動するか、成果物や commit にどう影響するか）。
- 6.1-sol / 6-sol / Luna が Astra と同じ傾向（確認しすぎ・テストしすぎ）を持つか。

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
- GPT-5.6 以前の前提の語句（`terra`、「1 段下げ」、「既定で簡潔」、`think hard` など）を `rg` で洗い出す。

artifact: `.context/<task>/01-scope.md`

### Phase 2: 監査

各対象を「典型修正パターン」と照合し、`path:line`、パターン記号、理由、推奨アクションを記録する。

artifact: `.context/<task>/02-audit.md`

### Phase 3: 改修

正規指示ファイルや model registry を SoT として、重複を増やさず最小修正する。skill description を変更する場合は起動条件が変わるため特に明示する。

artifact: `.context/<task>/03-changes.md`

### Phase 4: 検証

- repo の docs lint、skill validation、prompt eval があれば実行する。
- 変更した prompt は、変更前後で代表タスクを実行し、停止・確認質問・テスト量・完了率を比較する。
- API パラメータに触れた場合は OpenAI 公式 docs の現行記述と照合する。

artifact: `.context/<task>/04-verify.md`

## 典型修正パターン

### A. 確認や停止を誘発する文言

- 兆候: 「不明点があれば必ず確認する」「各ステップで承認を得る」のような一律の確認要求。
- 対応: 文脈から推定できることは推定して進めさせる。承認が必要な操作は、可逆性の 3 条件を満たさない操作と scope 拡大に限定して名指しする。

### B. Skill と AGENTS.md の衝突・曖昧さ

- 兆候: skill と AGENTS.md が別のことを言っている。ユーザー指示との優先順位が書かれていない。
- 対応: 矛盾を解消し、ユーザー指示が skill に優先すると明記する。skill で止まったときは該当指示を引用させる。

### C. 完了条件がない

- 兆候: 成果や終了条件が書かれておらず、最初の実装で終わってしまう。
- 対応: 検証可能な完了条件を先に書き、実行・確認・修正を含むならそれを明記する。

### D. テストの定型文

- 兆候: 「必ずテストを実行する」が変更内容に関係なく書かれている。
- 対応: 変更のリスクに見合った検証を求める形にする。Luna に検証させたい場合は success criteria に書く。

### E. GPT-5.6 の effort 方針の持ち越し

- 兆候: 「現行から 1 段下げてテスト」、Astra / 6.1-sol に `none` を指定、`minimal` の使用、`think hard` で effort を代用。
- 対応: 現行の実効 effort を維持し、variant ごとの対応 level を確認する。

### F. 書式・長さ指示の持ち越し

- 兆候: GPT-5.6 の「既定で簡潔」を前提にした指示、散文を期待しているのに書式指定がない。
- 対応: 必要な書式（段落か、リストか）を明示し、決まり文句を避けさせる。

### G. 委譲の指示がない

- 兆候: 並列化できる大きな作業でも、委譲について何も書かれていない。
- 対応: 並列化で速度や品質が上がる条件を書き、委譲を促す。

### H. 一律の文書読み込み

- 兆候: 「編集前に必ず全 docs を読む」「リポジトリ全体をレビューしてから作業する」。
- 対応: 条件付きの参照に変え、root 文書は router にする。

### I. 不要な警告・安全チェックリスト

- 兆候: 仮定のリスクに対する警告や checklist を毎回出させる指示。
- 対応: 削除する。実際の操作境界は可逆性の 3 条件で管理する。

### J. Variant 配分の固定・`terra` 参照

- 兆候: skill 本文で「worker は gpt-6.1-sol」などを正本化している。`terra` を参照している。
- 対応: 配分は resolver / registry / ADR に移し、skill には resolver 参照だけ残す（例示は non-authoritative と明記）。

### K. Codex 組み込み指示の再掲

- 兆候: Codex 経由の prompt で、行動への偏り・ユーザー指示の優先・警告抑制を繰り返し書いている。
- 対応: Codex の base instructions と重なる部分を削り、タスク固有の契約だけ残す。

### L. Skill description が長い・曖昧

- 兆候: description が長すぎる、または起動条件・スコープ・除外条件が読み取れない。
- 対応: 起動条件が分かる最短の形にする。変更前後で誤発火と不発火を確認する。

## プロンプト書き換えの最小例

### 旧

> 不明点があれば必ず確認してから進めてください。各ステップの前に承認を取ってください。作業前にリポジトリの docs をすべて読んでください。変更後は必ずテストを実行してください。

### 新

> Outcome: <期待成果>
> Success criteria: <検証可能な完了条件。実行・確認・修正を含むならそう書く>
> Allowed side effects: <可逆な in-scope 作業は無承認で可 / 3 条件を満たさない操作と scope 拡大は要承認>
> Context: 文脈から推定できることは推定して進める。ユーザー指示は skill の指示に優先する。<schema 変更時は X.md を参照>
> Verification: 変更のリスクに見合った検証を行う。
> Completion rule: 全項目を完了するか、`[blocked]` と不足入力を明示して停止する。

## 完了条件

- 対象ファイル群に「典型修正パターン」の違反が残っていない、または残置理由が artifact / ADR / 作業結果で説明されている。
- OpenAI 公式 docs の現行記述と、確認・停止の補正、skill 優先順位、完了条件、テスト量、effort、variant 配分の扱いが矛盾していない。
- 変更した prompt は、変更前後の比較で改善が確認されているか、未検証リスクとして明記されている。
- 中央 SoT と AI 別ファイル / skill / docs が矛盾していない。
- 検証結果と未検証リスクが `.context/<task>/` または作業結果に残っている。
