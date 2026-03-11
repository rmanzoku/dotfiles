# Agent Entrypoint Template

`bootstrap` モードで agent entrypoint を提案するときの標準骨格。
このまま全文を貼るのではなく、対象 repo に合わせて section outline と starter snippet を抜き出して使う。

## Required Sections

1. リポジトリの目的
2. 最初に読むべきドキュメント
3. ドキュメント正本
4. Agent探索ルール
5. 守るべき境界
6. Skillルール
7. 変更前チェック
8. 変更後チェック

## Suggested Starter Snippets

### リポジトリの目的

- このリポジトリの主な責務を 3-5 項目で箇条書きする。
- アプリ本体、ドメインロジック、UI、architecture docs、skills のような分類を優先する。

### 最初に読むべきドキュメント

1. `README.md`
2. `docs/index.md` または `docs/README.md`
3. `docs/architecture/overview.md`
4. `docs/architecture/services/`
5. `docs/design-system/`
6. skill 関連 docs
7. 実装コード

### ドキュメント正本

- architecture
- services
- data model
- flows
- design system
- skills

の正本パスを列挙する。

### Agent探索ルール

- 推測で設計を補完しない
- docs を根拠にする
- 変更前に architecture / service 責務 / 関連 Skill / 実装コードを確認する

### 守るべき境界

- サービス責務
- データ所有
- 公開 API
- Skill 責務

を明示し、侵食してはいけない変更例を添える。

### Skillルール

- 新 Skill 体系を提案しない
- Skill Creator と競合する変更をしない
- Skill 説明改善は可能

## Usage Rule

- `diagnose` モードでは path と heading 候補だけ返し、本文は返さない。
- `bootstrap` モードでのみ starter snippet を返す。
