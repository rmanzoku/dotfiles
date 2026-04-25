---
name: opus-4-7-tuning
description: "Audit and rewrite repository docs, skills, prompts, and harness scaffolding so they fit Claude Opus 4.7's behavior (literal instruction following, adaptive thinking, xhigh effort default, fewer subagents/tool calls, built-in progress updates, high-res vision). Use when the user wants to migrate or readiness-check a repo for Opus 4.7, modernize CLAUDE.md / AGENTS.md / skill files written for older Opus or Sonnet versions, or scrub stale prompting patterns (fixed thinking budgets, hand-rolled progress scaffolds, sampling-parameter advice). Do NOT use for application-side SDK code changes — that is the job of the official `claude-api` skill / `/claude-api migrate`."
---

# Opus 4.7 Tuning

リポジトリのドキュメント・スキル・プロンプト類を Claude Opus 4.7 の挙動に合わせて再整備するためのスキル。

API クライアントコードの自動移行は対象外（公式 `claude-api` スキル / `/claude-api migrate` の領分）。本スキルは **人間が読んで AI を運用する文書側** の整備に特化する。

## 起動する場面

次のいずれかに該当するときに起動する。

- ユーザーが「Opus 4.7 向けに整備したい」「Opus 4.7 マイグレーション」「Opus 4.7 readiness」と発話した。
- 既存の `CLAUDE.md` / `AGENTS.md` / `.claude/skills/**/SKILL.md` / `docs/**` 等が、Opus 4.6 以前を前提に書かれていないか棚卸しを依頼された。
- 旧来のプロンプティング指示（固定 thinking budget、`temperature` 指定、強制進捗フレーズ、`/think hard` 風の効きの薄いキーワード等）の見直し依頼を受けた。

## 起動しない場面

- API リクエストの SDK 引数を書き換えたい場合 → `claude-api` スキルへ委譲。
- 単発の質問応答で文書編集を伴わない場合 → 通常応答で良い。

## 参照する公式ソース

作業中、迷ったらこれらを直接当たる。バージョンに応じて常に最新を優先する。

- アナウンス: <https://www.anthropic.com/news/claude-opus-4-7>
- Claude Code ベストプラクティス: <https://claude.com/blog/best-practices-for-using-claude-opus-4-7-with-claude-code>
- Migration Guide（Opus 4.6 → 4.7 / 4.5 以前 → 4.7）: <https://platform.claude.com/docs/en/about-claude/models/migration-guide>
- Adaptive Thinking: <https://platform.claude.com/docs/en/build-with-claude/adaptive-thinking>
- Effort パラメータ: <https://platform.claude.com/docs/en/build-with-claude/effort>
- Task Budgets（beta）: <https://platform.claude.com/docs/en/build-with-claude/task-budgets>
- 高解像度ビジョン: <https://platform.claude.com/docs/en/build-with-claude/vision#high-resolution-image-support-on-claude-opus-4-7>

## Opus 4.7 で押さえる 9 項目

これは「文書を読みながら違反を見つける」ためのチェックリストでもある。

1. **Adaptive thinking（固定 budget は廃止）**
   `thinking: {type: "enabled", budget_tokens: N}` は 400 エラー。`thinking: {type: "adaptive"}` + `output_config.effort` に置換。Adaptive thinking は **デフォルト OFF** で、明示的に有効化する必要がある。
2. **Sampling パラメータの非サポート**
   `temperature` / `top_p` / `top_k` を非デフォルト値にすると 400。挙動の調整は **プロンプトで** 行う。
3. **Effort パラメータが最重要レバー**
   推奨デフォルトは `xhigh`（コーディング・エージェント）。`high` 以上が知能要求タスクの最低ライン。`low` / `medium` は厳格にスコープを切る側に倒れたので、複雑タスクで under-thinking を感じたら effort を上げるのが正解（プロンプト改修より優先）。
4. **応答長の自動可変**
   タスク複雑度に応じて自動調整。固定の冗長プロンプトを残すと逆に荒れる。長さ・スタイルが必要なら **positive example** を提示する形で書き直す。
5. **より文字通りの指示追従**
   暗黙の一般化を期待しない。「同様に他の N 件も処理して」のような言外の汎化指示は効きが弱い。要件は明示し、対象範囲もリスト化する。
6. **直接的なトーン**
   validation-forward な前置きや絵文字は減る。声色プロンプトは新しいベースラインで再評価する。
7. **エージェント進捗更新の内製化**
   「3 ツールごとに要約せよ」「N ステップごとに進捗を出力」のような強制スキャフォールドは **削除** する。残すと過剰になる。長さ・形式の好みがあれば「進捗更新はこういう形で」と明示しつつ短い example を 1 件添える。
8. **サブエージェント生成の保守化**
   デフォルトで spawn 数が減った。複数の独立タスクを並列に流したい場合は「複数の独立項目はファンアウトせよ」「直接終わらない作業のみ subagent」と明示する。
9. **ツール呼び出しの抑制 + 推論の増加**
   ツール多用が必要なら effort を上げる。それでも足りないなら「いつ・なぜそのツールを使うか」を方針として書く。

加えて API レイヤー側の事項として、トークナイザー変更（同テキストで 1.0–1.35x のトークン数）、prefill 廃止、thinking display デフォルトが `omitted`、`task_budget`（beta）導入、画像が最大 2576px / 最大 3x の画像トークン、座標は 1:1。これらは API ドキュメントに残せていれば十分で、運用文書に書く必要は通常ない。

## 実行モード判定（着手前に必ず行う）

依頼を受けたら、Phase 1 に入る前に以下の順で実行モードを決める。判定結果は artifact / コミットメッセージに 1 行残す。

1. **依頼に複数の合理的解釈があり、設計判断や合意形成を伴う場合**
   → `/grill-me` を起動して依頼を完全指定にしてから 2 / 3 を再判定する。
   例: 「Opus 4.7 に揃える」（揃え方の方針未確定）、新規 skill 設計、複数 SoT 衝突時の整理方針。

2. **依頼が明確で、破壊的変更を伴う場合**
   （中央レジストリ書き換え / `CLAUDE.md` / `AGENTS.md` の構造変更 / 既存 skill description 変更 / 複数ファイル横断改修）
   → Plan を提示し、レビューゲート（CLAUDE.md「Plan 共通ルール」）を通過してから Phase 1 へ。

3. **依頼が明確で、変更が局所（破壊性なし）の場合**
   → 単発処理。Phase フローはスキップし「典型修正パターン」だけ参照する。

`/grill-me` 経由で依頼が完全指定された後は、再度この判定に戻り 2 / 3 を選ぶ。

## 監査フロー（リポジトリ全体に対する整備手順）

> 上記「実行モード判定」で **2（Plan）** を選んだ場合に本フローを使う。各 Phase 完了時に `.context/<task-name>/<nn>-<phase>.md` の artifact を残し、それを次 Phase の開始条件にする（ワークスペース共通ルールに準拠）。**3（単発）** を選んだ場合はこのフローをスキップして「典型修正パターン」だけ参照する。

### Phase 1: スコープ確定

整備対象を確定する。最低でも次を確認する。

- どのファイル群が対象か（典型: `CLAUDE.md`, `AGENTS.md`, `.claude/skills/**`, `.claude/commands/**`, `docs/**`, `rules/**`, `prompts/**`）。
- モデル指定がリポジトリ内に分散していないか（中央レジストリがあれば、まずそこを確認する）。
- API コード側の改修は別タスクとして切り分ける（`claude-api` スキル / `/claude-api migrate`）。
- ユーザー依頼が「Opus 4.7 に揃える」のように曖昧な場合は、解釈を必ず確認する。最低限の確認テンプレ:
  - 全モデルを `claude-opus-4-7` 一本化するのか、役割別に使い分けるのか（例: precommit を `claude-haiku-4-5` のままにするか）。
  - Opus 4.7 系以外（Sonnet 4.6、Haiku 4.5 等）を残す方針か。
  - 中央レジストリの値変更と AI 別ファイル整備のどちらが先か（順序付けで作業安全性が変わる）。
- artifact 配置先のタスク名（`.context/<task>/` の `<task>` 部分）はユーザーから指定がなければ Phase 1 で確認する。指定が無いまま進める場合は `opus-4-7-tuning-<対象短縮>` 形式で提案し、Phase 1 artifact 内にその選定理由を残す。

artifact: `.context/<task>/01-scope.md`（対象ファイル一覧、除外理由、モデル指定の所在、依頼解釈の確認結果、タスク名の決定経緯）。

### Phase 2: 監査

Phase 1 で確定したファイルを 1 本ずつ読み、下記「典型修正パターン」と照合して **指摘リスト** を作る。各指摘には次を必須項目として残す。

- `path:line` または該当箇所の引用
- 該当する **典型修正パターン記号**（A〜K、後述。複数該当時は併記）
- 判定理由
- 推奨アクション（置換案）

「典型修正パターンに該当しない違反」を見つけた場合は、新規パターンとして本スキルへの追加候補にする旨をメモする（その場では拡張せず、Iteration 完了後にユーザーへ提案）。

artifact: `.context/<task>/02-audit.md`（典型パターン記号でカラム化した指摘テーブル）。

### Phase 3: 改修

監査結果に基づき編集する。リポジトリの正規指示ファイル（多くは `AGENTS.md` または `CLAUDE.md`）を SoT とし、AI 別ファイル・skill・docs が SoT と矛盾していたら SoT 側に寄せる。重複を増やさない。

破壊的な変更（CLAUDE.md / AGENTS.md / 中央モデルレジストリの書き換え）の前にユーザー確認を取る。

artifact: `.context/<task>/03-changes.md`（変更ファイル一覧と要約）。

### Phase 4: 検証

- リポジトリにルール lint や docs lint があれば実行する（例: `sh scripts/rules-lint.sh`、`markdownlint`）。
- 変更済みドキュメントを 1 本選び、「実際にエージェントが読み解けるか」をドライランで確認する。可能なら `.context/` に test prompt を置いて実行ログを残す。

artifact: `.context/<task>/04-verify.md`（lint 結果、ドライラン結果、残タスク）。

## 典型修正パターン（Audit 観点）

監査時に最頻出のアンチパターンと、置き換え案。

### A. 廃止された API パラメータ表現が文書に残っている

- 兆候: `temperature: 0` / `top_p` / `top_k` / `thinking.budget_tokens` を「推奨」「必須」と書いている。
- 対応: 削除し、Adaptive thinking + effort で代替する旨を 1 行で書く。例:

  > Opus 4.7 ではサンプリングパラメータと固定 thinking budget は使用しない。挙動はプロンプトと `effort`（推奨デフォルト `xhigh`）で誘導する。

### B. 強制スキャフォールド

- 兆候: 「N ツール呼び出しごとに進捗を要約」「各ステップ終わりに 1 行ステータスを出力」など。
- 対応: 削除。それでも形式に強い好みがある場合だけ、positive example 1 件で書き換える。

### C. 否定形プロンプト過多

- 兆候: 「〜してはいけない」「〜は禁止」のリストが冗長で、肯定表現の代替が無い。
- 対応: 「望ましい形」を 1〜2 件の例で示す。否定リストは絶対に守らせたいガードレールだけに絞る。

### D. 暗黙の汎化前提

- 兆候: 「同様の処理を他の関連箇所にも適用して」「適切に判断して」のような委譲文。
- 対応: 対象を列挙する、または「対象範囲は次のとおり: …」と明示する。

### E. モデル ID のハードコード

- 兆候: skill / docs に `claude-opus-4-6` などが直書き。
- 対応: 中央モデルレジストリ（例: `rules/model_registry.yaml`）を SoT にし、各文書はそこを参照する。フォールバックとしてインライン記載する場合だけ最新 ID を書く。

### F. 「Effort をプロンプトで再現しよう」とする工夫

- 兆候: 「ultrathink」「think hard」「very carefully」などのマジックワード推奨が文書化されている。
- 対応: 削除し、「複雑タスクでは effort を上げる（`high`/`xhigh`）」に置換。プロンプトで増減を促す例は残してよいが、effort 設定の代替ではないと明示する。

### G. 古いトーン・ボイス指示

- 兆候: 「絵文字を使って親しみやすく」「冒頭で同意を示してから」のような Opus 4.6 のスタイルを前提にした指示。
- 対応: Opus 4.7 のベースライン（直接的、検証フレーズ少なめ）で再評価する。**ブランド・UX 要件など肯定的な必要性が示せない場合はデフォルトで削除**。残す判断には根拠（誰のどの要件か）を artifact / コミットメッセージに 1 行残す。

### H. サブエージェント期待

- 兆候: 「タスクは可能な限り subagent に分割」というデフォルト指示。
- 対応: 「直接完了できない作業のみ subagent。複数の独立項目はファンアウトする時のみ複数 spawn」に置換。

### I. 画像処理の旧前提

- 兆候: 「画像は 1568px に縮小して送る」「座標はスケール変換」など。
- 対応: 「Opus 4.7 は最大 2576px / 約 3.75MP、座標は 1:1。トークン消費が増えるため、不要なら事前ダウンサンプル」に更新。

### J. Claude Code 用の interaction 指示が古い

- 兆候: 「都度確認しながら進める」「1 ステップごとにユーザー承認を取る」が default 化している。
- 対応: 「初回ターンで intent / constraints / acceptance criteria / 関連ファイルパスをまとめて与え、以降は委譲タスクとして自走させる」に寄せる。確認が必要なゲートは明示的に列挙する。

### K. skill description が貧弱

- 兆候: SKILL.md の frontmatter `description` が極端に短い、起動条件・スコープ・除外条件が読み取れない、機能名の繰り返しのみ（例: 「リファクタリングを行う」「コードを書く」）。
- 対応: Opus 4.7 はリテラル解釈に倒れたため、貧弱な description は **誤発火と不発火の両方** を増やす。「起動する場面」「起動しない場面」「カバーするタスクの粒度」が読み取れる長さに改稿する。description 変更は SKILL.md「ユーザーへの確認が必須なケース」に該当するため、編集前に確認を取る。

## 正解形リファレンス（望ましい例）

監査時、subagent は「悪い兆候」だけでなく「望ましい形」と対比して指摘する方が判定が安定する。本リポジトリ内では以下が良い参照例として機能する（リポジトリ非依存で読む場合は構造のみ拾う）。

- **中央レジストリ参照のみで自身は SoT を持たない skill**（典型 E の対極）
  例: `.claude/skills/research/SKILL.md` / `.claude/skills/deck/SKILL.md` の `## Model Assignment` セクション。`rules/model_registry.yaml → skills.<name>.roles.*` を参照するだけで、ID は記載しない。
- **subagent 起動を「条件・責務・フォールバック」まで明示**（典型 H の対極）
  例: `.claude/skills/research/SKILL.md` の `researcher_4` セクション。`grok_enabled=true` の条件、Phase C/D 介入禁止の責務、`Agent` 失敗時のフォールバック判定までを書ききっている。
- **確認ゲートを特定事象に限定**（典型 J の対極）
  例: `.claude/skills/research/SKILL.md` Phase A Step 1。スコープ未確定 / API 課金許諾の 2 点に限り `STOP してユーザーに確認する` と書き、それ以外は自走させる。
- **subagent prompt の禁止事項リストを責務分離のため肯定形と併記**（典型 C の対極）
  例: `.claude/skills/research/SKILL.md` Phase B Step 3 の「サブエージェントへのプロンプト骨子」。担当範囲（肯定形）と禁止事項（否定形）を対で書いている。

これらは「典型 X 違反を見つけたら、対極の正解形と対比して置換案を出す」ための参照点。置換案を構造から書き起こすより、既存の良い形を真似る方が品質が安定する。

## プロンプト書き換えの最小例

### 旧

> あなたは慎重なエンジニアです。tool を 3 回呼ぶごとに進捗を要約してください。temperature=0、ultrathink で熟考してください。同様の修正を他の似た箇所にも適用してください。

### 新

> あなたはシニアエンジニアとして、次のタスクを完遂してください。
>
> - Intent: <意図>
> - Constraints: <制約>
> - Acceptance criteria: <受け入れ条件>
> - 対象ファイル: `path/a.ts`, `path/b.ts`, `path/c.ts`（この 3 ファイル以外は対象外）
> - 進捗更新は不要。完了時にだけ変更点を 5 行以内で要約する。
> - 複雑な判断が必要なら深く考えてください（このタスクは見た目より分岐が多い）。

`effort` は呼び出し側で `xhigh` を設定する想定（プロンプトに書かない）。

## ユーザーへの確認が必須なケース

次のいずれかに該当するときは、編集前に必ずユーザー確認を取る。

- 中央モデルレジストリ（例: `rules/model_registry.yaml`）の書き換え。
- `CLAUDE.md` / `AGENTS.md` の構造的書き換え（節の追加・削除・節順入れ替え）。
- 既存スキルの description 変更（自動起動条件が変わるため）。
- API クライアントコードの編集（範囲外、`claude-api` スキルへ案内）。

## 完了条件

- 対象ファイル群に対し、上記「典型修正パターン」の各項目で違反が残っていない（または残置理由が ADR / コミットメッセージで説明されている）。
- 中央 SoT と AI 別ファイル / skill / docs が矛盾していない。
- 変更の根拠と判断は `.context/<task>/` 配下に artifact として残っている。
- ユーザーが配置先（グローバル / リポジトリ内）に応じて scaffolding を最終確定できる状態。
