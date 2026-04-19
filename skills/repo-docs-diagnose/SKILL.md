---
name: repo-docs-diagnose
description: Diagnose whether a repository's README, docs index, architecture docs, service docs, design-system docs, operational docs, and agent entrypoint guidance are structured for AI coding agents to explore efficiently. Use when asked to review repo docs structure, AI/agent readability, onboarding flow, RAG/context efficiency, docs navigation, or to propose bootstrap doc skeletons such as README/docs index/agent entrypoint templates. Bootstrap proposals are only for explicit initialization requests containing terms like 初期化, bootstrap, scaffold, 雛形, テンプレート, starter, ひな形, or 叩き台を作る.
---

# repo-docs-diagnose

AI エージェントが repo を読む入口として docs 構造が機能しているかを診断する。
通常は read-only の診断を返し、明示的な初期化依頼がある場合だけ docs/entrypoint/運用文書の雛形提案を返す。

## Workflow

1. 現在の作業ディレクトリを診断対象 repo として扱う。
2. `SKILL.md` と同じディレクトリ配下の `scripts/executable_repo_docs_diagnose.py` を実行して JSON を取得する。
3. JSON の `mode` を確認する。
4. `mode=diagnose` なら診断レポートを返す。
5. `mode=bootstrap` なら診断レポートに加えて雛形提案を返す。
6. 対象 repo は変更しない。書き換え例や雛形は提案として返すだけに留める。

## Script Usage

基本:

```bash
python3 <skill-dir>/scripts/executable_repo_docs_diagnose.py
```

bootstrap 判定を含める:

```bash
python3 <skill-dir>/scripts/executable_repo_docs_diagnose.py \
  --request-text "AI向けに docs 骨格を初期化したい"
```

比較用 repo を使う:

```bash
python3 <skill-dir>/scripts/executable_repo_docs_diagnose.py \
  --reference-repo /path/to/reference/repo
```

重要:
- `--reference-repo` は比較ヒューリスティクス専用。未指定時は cross-repo 比較をしない。
- `--request-text` に bootstrap keyword が含まれない限り `mode=diagnose` にする。
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

`diagnose`:
- `bootstrap_candidates` には path、reason、priority、required sections だけを載せる。
- 既存 docs が見つかった場合は、`source_paths` を添えて「推奨パスへ寄せる」提案にする。
- starter paragraph、Markdown 本文、ready-to-paste block は出さない。
- zip 由来の診断制約を適用する。対象 repo 診断では新 Skill 提案や Skill 体系変更提案をしない。

`bootstrap`:
- `bootstrap_candidates` に starter snippet と section outline を含めてよい。
- 提案対象は README、docs index、agent entrypoint、architecture overview、service index、design-system index、operational docs/ADR に限定する。
- repo 設定変更、CI 変更、code scaffolding、skill system 変更は提案しない。

## Response Rendering

JSON の `report_section` を使って次の並びで返す:

`diagnose`:
1. リポジトリ全体評価
2. Agent探索評価
3. docs構造改善提案
4. Skillドキュメント改善
5. 構造レベルの書き換え候補

`bootstrap`:
1. リポジトリ全体評価
2. Agent探索評価
3. 提案ファイル一覧
4. 各ファイルの目的
5. 必須見出し
6. starter snippets

## References

- 診断観点と制約の詳細は `references/ai_repo_diagnostic_prompt.md` を読む。
- agent entrypoint の雛形は `references/agent_entrypoint_template.md` を読む。
- `agents/openai.yaml` を更新した後は validator を実行する。

## Validation

```bash
python3 /Users/rmanzoku/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
  skills/repo-docs-diagnose
```
