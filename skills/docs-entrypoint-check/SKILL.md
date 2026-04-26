---
name: docs-entrypoint-check
description: "Check whether a repository has minimal AI-readable documentation entrypoints and bootstrap skeletons: README, docs index, architecture/service/design-system/operational entrypoints, and agent guidance. Use for lightweight docs navigation checks, onboarding entrypoint checks, or explicit bootstrap skeleton requests containing 初期化, bootstrap, scaffold, 雛形, テンプレート, starter, ひな形, or 叩き台を作る. Do not use for full documentation audits, link graph analysis, contradiction checks, stale document review, TODO/deferred work governance, or source-of-truth evaluation; use docs-evaluator for those."
---

# Docs Entrypoint Check

AI エージェントが repo を読み始めるための最小 entrypoint があるかを確認する。
通常は read-only の軽量チェックを返し、明示的な初期化依頼がある場合だけ docs/entrypoint/運用文書の雛形提案を返す。

広い docs 監査、全テキスト文書の棚卸し、未到達リンク、矛盾、廃止文書、TODO 管理、ADR の正本化、正本と一時文書の分離は `docs-evaluator` に任せる。

## Workflow

1. 依頼が full docs audit、link graph analysis、contradiction check、stale docs review、TODO/deferred work governance、source-of-truth evaluation のいずれかなら、この skill の script は実行せず `docs-evaluator` にルーティングする。ここでのルーティングは「この skill の成果物として scope 外判定と handoff summary を返す」ことを指し、この skill 内で `docs-evaluator` を実行しない。
2. 現在の作業ディレクトリをチェック対象 repo として扱う。
3. `SKILL.md` と同じディレクトリ配下の `scripts/executable_docs_entrypoint_check.py` を実行して JSON を取得する。repo root の `scripts/` ではなく skill ディレクトリ配下の script を使う。
4. JSON の `mode` を確認する。
5. `mode=check` なら entrypoint チェック結果を返す。
6. `mode=bootstrap` ならチェック結果に加えて、存在しない target の雛形提案だけを返す。既存の `README.md` や `AGENTS.md` は「既存のため新規候補なし」と扱い、ユーザーが雛形を明示的に求めても強制的に starter snippet を作らない。既存 entrypoint の内容評価や改稿は `docs-evaluator` または別作業の対象として案内する。
7. 対象 repo は変更しない。書き換え例や雛形は提案として返すだけに留める。

## Script Usage

基本:

```bash
python3 <skill-dir>/scripts/executable_docs_entrypoint_check.py
```

bootstrap 判定を含める:

```bash
python3 <skill-dir>/scripts/executable_docs_entrypoint_check.py \
  --request-text "AI向けに docs 骨格を初期化したい"
```

比較用 repo を使う:

```bash
python3 <skill-dir>/scripts/executable_docs_entrypoint_check.py \
  --reference-repo /path/to/reference/repo
```

重要:
- `<skill-dir>` はこの `SKILL.md` があるディレクトリを指す。repo root の `scripts/` を探索せず、インストール済みまたは publisher source の skill ディレクトリ配下から実行する。
- `--reference-repo` は比較ヒューリスティクス専用。未指定時は cross-repo 比較をしない。
- `--request-text` に bootstrap keyword が含まれない限り `mode=check` にする。
- `--request-text` に `雛形は不要`、`bootstrap は不要`、`no bootstrap`、`without bootstrap` のような否定された bootstrap keyword がある場合は `mode=check` にする。
- 出力は JSON のみ。人間向け応答は JSON を整形して作る。

## Detection Rules

- 評価順は `README*` → `docs/README*` / `docs/index*` → architecture/service/design-system docs → operational docs → agent guidance docs。
- `findings.category` は次の固定列挙だけを使う:
  - `docs-index`
  - `architecture`
  - `services`
  - `design-system`
  - `operational`
  - `entrypoint`
  - `spec-structure`
  - `size`
- oversized-doc は markdown/text が `300 行超` または `12 KB超` のときに出す。
- 固定パスを創作上の唯一解として扱わない。まず `docs/` 配下を探索し、該当文書があれば「推奨パスへ正規化する」提案に変換する。
- operational docs は `docs/adr`, `docs/governance`, `docs/standards`, `docs/contributing`, `docs/runbooks` のいずれかがあるかで判定する。
- agent entrypoint は `AGENTS.md`, `CLAUDE.md`, `docs/agent_entrypoint.md`, `docs/agents/README.md` のいずれかで判定する。
- `critical` / `high` があるときは低価値な文体指摘を抑制する。
- severity ごとの findings は最大 3 件に制限する。

## Mode Rules

`check`:
- `bootstrap_candidates` には `path`、`reason`、`priority`、`required_sections` だけを載せる。既存 docs の再利用候補がある場合だけ `source_paths` を追加してよい。
- 既存 docs が見つかった場合は、`source_paths` を添えて「推奨パスへ寄せる」提案にする。
- starter paragraph、Markdown 本文、ready-to-paste block は出さない。
- entrypoint check の制約を適用する。対象 repo チェックでは新 Skill 提案や Skill 体系変更提案をしない。
- JSON に `bootstrap_candidates` が含まれていても、`mode=check` の人間向け応答では `findings` を主成果物にする。ユーザーが skeleton / candidate を求めていない限り、`bootstrap_candidates` は内部的な構造候補として扱い、starter snippet や提案ファイル一覧として展開しない。

`bootstrap`:
- `bootstrap_candidates` に `starter_snippet`、`starter_content_type`、`report_section`、section outline を含めてよい。
- 提案対象は README、docs index、agent entrypoint、architecture overview、service index、design-system index、operational docs/ADR に限定する。
- repo 設定変更、CI 変更、code scaffolding、skill system 変更は提案しない。

## Response Rendering

JSON の `report_section` を使って次の並びで返す:

`check`:
1. リポジトリ全体評価
2. Agent探索評価
3. docs構造改善提案
4. 構造レベルの書き換え候補

JSON に存在しない `report_section` は出さない。空セクションを補うために、JSON にない改善項目や broad docs audit の findings を創作しない。

`bootstrap`:
1. リポジトリ全体評価
2. Agent探索評価
3. 提案ファイル一覧
4. 各ファイルの目的
5. 必須見出し
6. starter snippets

`bootstrap` でも既存ファイルそのものの starter snippet は出さない。`README.md` や `AGENTS.md` が既存なら「既存のため新規候補なし」と説明する。
未作成の推奨 target は、`source_paths` が付いていても starter snippet を出してよい。その場合は「既存 docs を参考に、この missing target の形を提案している」と明示し、既存 source を置き換えるように見せない。

## References

- `mode=check` の観点と制約の詳細が必要なときだけ `references/entrypoint_check_prompt.md` を読む。
- `mode=bootstrap` で agent entrypoint が missing target として出たときだけ `references/agent_entrypoint_template.md` を読む。既存 `AGENTS.md` がある場合は、この template を強制的に提示しない。
- `agents/openai.yaml` を更新した後は validator を実行する。

## Validation

```bash
scripts/skill-quick-validate skills/docs-entrypoint-check
```
