---
title: "ADR 0070: dads-design は上流の公式 Markdown を主参照とし、git 管理外の共有キャッシュへ取得する"
status: "Accepted"
date: "2026-08-28"
worked_at: "2026-08-28 JST"
agent_model: "Claude Opus 5 (Claude Code)"
---

# ADR 0070: dads-design は上流の公式 Markdown を主参照とし、git 管理外の共有キャッシュへ取得する

## Context

`skills/dads-design` は、デジタル庁デザインシステム（DADS, β版）の調査結果を repo 内の
`references/*.md` に転記して持つ知識スキルとして作られた（2026-06-22）。2026-08-28 に上流を
再照合したところ、2 か月で以下が動いていた。

- コンポーネント 46 → 49 種（`switch` / `toc` / `notice-block` 追加）
- slug 変更 `dialog` → `modal-dialog`（スキルが無効な URL を提示する状態だった）
- 名称変更 パンくずリスト → パンくずナビゲーション、グローバルメニュー → 水平メニュー
- ボトムナビゲーション・スクロールトップボタンの非推奨化
- 機能カラー（フォーカスカラー / 検索ハイライトカラー）の追加

一方で `@digital-go-jp/design-tokens` は v2.0.1 のまま動いていない。**動くのはドキュメント側**で、
転記した要約ほど陳腐化が速いという非対称があった。

同時に、上流が 2026-07 以降に**全ドキュメントの Markdown アーカイブ配布**を開始していたことが
判明した（`/dads/resources/` の `dads-markdown-YYYYMMDD.zip`、125 ファイル / 展開 753KB）。
同梱 README に「主に AI 参照用途として Markdown 形式へ変換した」と明記され、各ファイルは
`title` / `category` / `slug` / `source_url` の Front Matter を持つ。これは本スキルが手作業で
再現していたものの上位互換である。

設計の選択肢は 3 つあった。

1. 従来どおり転記を維持し、定期的に人手で追随する
2. Markdown アーカイブを repo へ vendoring し、スキルに同梱する
3. 上流アーカイブを主参照とし、repo には判断・運用・索引だけを置く

## Decision

**選択肢 3 を採る。** repo が持つのは「上流から機械的に引けないもの」に限る。

### 情報源の階層

| 順 | 情報源 | 置き場所 | 内容 |
|---|---|---|---|
| 1 | 公式 Markdown ドキュメント | **git 管理外の共有キャッシュ** | 設計原則・作例・コンポーネント個別ガイドライン・a11y 要件の詳細 |
| 2 | `assets/dads-tokens.css` | repo 同梱（MIT） | 実数値（全 HEX / サイズ / box-shadow） |
| 3 | `references/*.md` | repo 同梱 | 判断の要点、成果物への適用ルール、ライセンス運用、索引 |

`references/*.md` は上流と重複する記述を落とした。全 49 コンポーネントの用途説明は
名称 / slug / 状態の索引へ、13 色相 × 13 階調の HEX 全表とエレベーションの box-shadow 全文は
`assets/dads-tokens.css` への導線へ置き換えた。**判断基準は「`tokens.css` に値があるものは持たない、
無いものは持つ」**とし、機能カラー・余白・レイアウト・リンクテキスト・アイコンのように
トークン化されていない規定は repo 側に残す。

### キャッシュを git 管理しない理由

- **ライセンス**: Markdown アーカイブは上流の区分で「デザインシステム本体」に属し、Figma /
  コードスニペットに認められた「加工して組み込む場合は出典不要」の緩和が適用されない。
  再配布は可能だが出典記載が必要になる。同梱・再配布せず利用者環境で都度取得すれば、
  この義務を本 repo の配布物へ持ち込まずに済む
- **重複**: 753KB / 125 ファイルは上流の完全な複製であり、repo が持つ意味がない
- **陳腐化**: アーカイブ URL は日付入り（`dads-markdown-YYYYMMDD.zip`）で、vendoring すると
  「repo 内の古い写し」が正本を騙る状態になる

### キャッシュの配置

`${XDG_DATA_HOME:-~/.local/share}/dads-design/`（`DADS_DOCS_DIR` で上書き可）。

skill ディレクトリ内へ置く案（`.gitignore` する）も検討した。`gh skill install --from-local` は
gitignore されたファイルもコピーするため、repo 側で 1 回取得すれば両 agent へ配布される利点がある。
それでも共有キャッシュを採ったのは、配備先が symlink ではなく**実体コピー**で、claude-code と
codex に同じデータが二重化するため。共有キャッシュなら実体は 1 つで、repo も配備先も汚れない。

### 取得スクリプト

`skills/dads-design/scripts/dads-docs`（Python 標準ライブラリのみ）。

- `status` 状態表示 / `check` 存在確認のみ（あり=0, なし=3）/ `fetch [--force]` 取得
- アーカイブ URL は `/dads/resources/` から毎回発見する。ファイル名に日付が入り固定できないため。
  **発見に失敗したら URL を推測せず失敗させる**（暗黙 fallback の禁止）
- 進捗は stderr へ逐次出力し、リトライ 3 回・各試行の結果・失敗理由を残す（無出力の待機を作らない）
- 展開は zip slip を防ぎつつ一時ディレクトリで行い、成功後に差し替える。同じ日付なら再ダウンロードしない
- `manifest.json` に `archive_date` / `source_url` / `site_version` / `fetched_at` / `file_count` を残す

`gh skill install` は実行ビットを保存しないため、**`python3 <skill>/scripts/dads-docs` で起動する**
運用とし、SKILL.md にもその形で記載する。

## Consequences

- ドキュメント側の更新は `fetch` の再実行だけで追随できる。repo 側の手作業追随が必要なのは、
  索引（コンポーネントの増減・改名・非推奨化）とトークン package の版上げに縮む
- **ネットワークと初回セットアップが前提になる**。未取得でも `assets/dads-tokens.css` と
  `references/*.md` で最低限の適用はできるが、コンポーネント選定と設計原則の確認は劣化する。
  この劣化を検知できるよう `check` を分離した
- 新しいマシンでは install 後に 1 回 `fetch` が要る。手順は
  [docs/skills-install-manifest.md](../skills-install-manifest.md) の「install 後に追加手順が要る skill」に記載した
- キャッシュは chezmoi 管理外（`dot_local/` は `~/.local/bin` のみを持つ）。machine-local な
  再取得可能データとして扱い、dotfiles へ昇格させない

## Alternatives considered

- **転記の維持**: 2 か月で 5 種類の陳腐化が出た実績があり、追随コストが読めない
- **アーカイブの vendoring**: ライセンス上の出典義務を配布物へ持ち込み、753KB の複製を抱え、
  日付入り URL との対応が切れる
- **skill 内 `.gitignore` キャッシュ**: agent ごとに実体が二重化する。`gh skill install` が
  gitignore ファイルもコピーする挙動に依存する点も、上流実装の変更に弱い
