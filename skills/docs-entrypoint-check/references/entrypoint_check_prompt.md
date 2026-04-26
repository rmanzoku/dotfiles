# Docs Entrypoint Check Prompt

この reference は `check` モード専用の基準である。
target repo の docs entrypoint と読み始めの導線を確認するときだけ、この制約を強く適用する。

## Hard Constraints

- 対象はチェック対象 repo の内部に限定する。
- 外部サービスや他 repo には言及しない。
- Skill Creator が既に導入されている前提で確認する。
- Skill 体系を変更する提案をしない。
- 新しい Skill を提案しない。
- 既存 Skill には説明改善だけを提案してよい。

## Review Goal

AI エージェントが次の順で探索できる状態を目標とする。

1. `README`
2. `docs index`
3. `architecture docs`
4. `service docs`
5. `code`

## Review Areas

### Agent探索性

- docs 入口が一意か
- docs index が読み順として機能するか
- architecture / service / design-system へ迷わず到達できるか

### docs構造

- 巨大ファイルに偏っていないか
- 1トピック1ファイルに近いか
- README / index が navigation として機能するか
- architecture / services / design-system が分離されているか
- 推奨パスが無い場合でも、まず `docs/` 配下に相当文書がないか探し、見つかったら「欠落」ではなく「推奨パスへ正規化」の改善案にする

### アーキテクチャ記述

- サービス責務
- 依存関係
- データ所有
- API
- フロー

の 5 点が AI にとって追いやすいかを確認する。

### 構造化情報

- YAML
- JSON
- 箇条書き
- 表形式

のような chunk 化しやすい形式が使われているかを確認する。

### Skillとの接続

- docs から関連 Skill が見つけやすいか
- Skill 説明が trigger と用途を十分に表現しているか

### RAG / コンテキスト効率

- docs 粒度
- 冗長重複
- architecture 情報の集中度

を確認する。

## Expected Human Report Sections

1. リポジトリ全体評価
2. Agent探索評価
3. docs構造改善提案
4. 構造レベルの書き換え候補

ただしこの skill ではスクリプト出力 JSON を正とし、人間向けの文面はそこから整形する。
JSON に存在しない section や finding は補わない。
