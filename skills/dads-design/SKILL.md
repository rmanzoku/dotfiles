---
name: dads-design
description: >-
  デジタル庁デザインシステム（DADS, β版）準拠のデザインを成果物に適用するためのデザイントークン（配色・タイポグラフィ・余白・角丸・エレベーション）・設計原則・コンポーネント索引・アクセシビリティ要件・ライセンス情報と、公式Markdownドキュメント一式の取得スクリプト。
  Webページ、レポート、スライド、ドキュメント等の成果物を作成・スタイリングするとき、色・フォント・余白・角丸・影を決めるとき、アクセシブル(JIS X 8341-3:2016 AA / コントラスト4.5:1)な配色が必要なとき、また「DADS」「デジタル庁デザインシステム」「デザイントークン」「公的/行政っぽい信頼感のあるデザイン」に言及されたら必ずこのスキルを参照すること。
  DADSと無関係な一般的フロントエンド実装やアプリのロジックには使わない。
---

# DADS デザイン適用スキル（dads-design）

デジタル庁デザインシステム（DADS, β版 / `https://design.digital.go.jp/dads/`）に準拠したデザインを、成果物へ**安全かつ一貫して適用する**ためのスキル。

DADS はβ版で更新が速い。そこで本スキルは**上流の一次資料を主参照とし、リポジトリ側には判断・運用・要約だけを持つ**設計にしている。要約を厚くすると必ず陳腐化するため、上流で機械的に引ける事実（コンポーネントの用途説明、全HEX値、作例）は意図的に持っていない。

## 情報源の優先順位

| 順 | 情報源 | 何を引くか |
|---|---|---|
| 1 | **公式Markdownドキュメント**（キャッシュ） | 設計原則・作例・コンポーネント個別のガイドライン・アクセシビリティ要件の詳細。デジタル庁が**AI参照用途を明示**して配布している一次資料 |
| 2 | `assets/dads-tokens.css` | 実数値（全プリミティブ色HEX・サイズ・box-shadow）。MIT で同梱済み |
| 3 | `references/*.md` | 判断の要点、成果物への適用ルール、ライセンス運用、索引 |

上流を読まずに済ませたい軽い作業なら 2〜3 だけで足りる。**配色や構成を確定する作業では 1 を必ず開く。**

## セットアップ（初回 / 鮮度確認）

公式Markdownは容量（展開 753KB / 125ファイル）と上流との重複、および「デザインシステム本体」としての再配布上の扱いを避けるため**git管理せず**、共有キャッシュへ取得する。

スキルの配備先では実行ビットが落ちるため、**`python3` で起動する**（依存は標準ライブラリのみ）。以下の `<skill>` はこの SKILL.md があるディレクトリ。

```bash
python3 <skill>/scripts/dads-docs status
```

`state: NOT FETCHED` なら取得する（数秒。ネットワークが要る）:

```bash
python3 <skill>/scripts/dads-docs fetch
```

- キャッシュ: `${XDG_DATA_HOME:-~/.local/share}/dads-design/`（`DADS_DOCS_DIR` で上書き可）。claude-code / codex の両配備先から同じ実体を参照する
- `status` が示す `docs root` 配下が展開先。以降このパスを `<docs>` と呼ぶ
- `check` は取得せず存在確認のみ（あり=0 / なし=3）。スクリプト経由で判定したいときに使う
- アーカイブのURLは日付入り（`dads-markdown-YYYYMMDD.zip`）なのでリソースページから毎回発見する。発見できなければURLを推測せず失敗する
- 定期的に `fetch` を実行する。同じ日付なら再ダウンロードせず終了し、新しければ差し替える

### `<docs>` の歩き方
```
<docs>/index.md                        全体の入口
<docs>/MANIFEST.md                     全収録ファイルの一覧
<docs>/foundations/<topic>/index.md    color, typography, spacing, layout, elevation, icon, link-text
<docs>/components/<slug>/index.md      各コンポーネント（slug は references/components.md の索引から引く）
<docs>/components/<slug>/changelog.md  そのコンポーネントの変更履歴
<docs>/guidance/, <docs>/webaccessibility/, <docs>/updates/
```
各ファイルは Front Matter（`title` / `category` / `slug` / `source_url`）付き。`source_url` で公式ページに戻れる。

## DADSの中核思想（外さない3点）
1. **アクセシビリティ最優先**（「誰一人取り残されない」）。目標は JIS X 8341-3:2016 AA（=WCAG 2.0）。テキストはサイズによらずコントラスト **4.5:1 以上**。色だけで情報を伝えない。→ `references/accessibility.md`
2. **8pxグリッド＋限定スケール**。余白は8の倍数、フォントサイズ・行間・角丸・影は決められたスケールから選ぶ（恣意的な数値を作らない）
3. **スタイルガイドとして再定義する前提**。DADSは汎用プラットフォームで、各組織が自ブランドに合わせキーカラー等を差し替えて「スタイルガイド」を作る思想。だからキーカラーは Blue 固定ではなく**差し替え可能**な変数。ただし**フォーカスカラー（Yellow-300 + Black の2重構造）は変更禁止**の機能カラーで、差し替え対象ではない

## 主要トークン（クイック参照）
完全な数値は `assets/dads-tokens.css`（MIT, `var(--token-name)` で参照）、選び方の要点は `references/design-tokens.md`。

- **キーカラー（プライマリ）= Blue系**。標準 `--color-key-700` #264af4 / 濃 `--color-key-800` #0031d8 / 淡背景 `--color-key-50` #e8f1fe。（ブランド色に差し替え可）
- **セマンティック**: success #259d63（green-600）/ error #ec0000（red-800）/ warning #fb5b01（orange-600）or #b78f00（yellow-700）
- **機能カラー**: フォーカス = Yellow-300 #ffd43d ＋ Black #000000 の2重構造（**変更禁止**）/ 検索ハイライト = シアン系 or マゼンタ系。CSS変数が無いのでプリミティブを直接参照
- **ニュートラル**: 本文 `solid-gray-900` #1a1a1a、薄い文字の下限 `solid-gray-536` #767676（白黒双方に4.5:1）、罫線 `solid-gray-420` #949494（白に3:1）。白 #ffffff / 黒 #000000
- **フォント**: `'Noto Sans JP', -apple-system, BlinkMacSystemFont, sans-serif`（本文・見出し共通）/ コードは `'Noto Sans Mono'`。ウェイトは 400 / 700 のみ
- **本文の既定**: 16px / line-height 1.7（`Std-16N-170`）。見出しは Bold + line-height 1.4〜1.5
- **フォントサイズ**: 14,16,17,18,20,22,24,26,28,32,36,45,48,57,64（px）。本文・UIは16px以上、14pxは原則使わない
- **角丸**: 8（ボタン/入力）/ 12〜16（カード）/ 32（大）/ full（ピル）
- **エレベーション**: `--elevation-1`〜`8`（2層シャドウ）。重なる要素は2段階以上差をつける。影はコントラストの代わりにならない
- **ブレークポイント**: 768px の1点。グリッド12カラム

## 適用ワークフロー

1. **適用モードを選ぶ**
   - **(A) フルDADS**: キーカラーも含め DADS のトークンをそのまま使う。最も「行政・公共」然とした見た目
   - **(B) DADSベースライン＋独自ブランド**: 余白8px・タイプスケール・角丸/影スケール・AAコントラスト等の**構造と原則は DADS に従い**、キーカラー（`--color-key-*`）だけをブランド色に差し替える。DADS自身が想定する「スタイルガイド」の作り方。8pxグリッド、タイプスケール、角丸/影スケール、AAコントラスト、色以外の手掛かり、**フォーカスカラー**は維持する
2. **トークンを読み込む**: 実装なら `assets/dads-tokens.css` を成果物にコピー/インポートし `var(--color-key-700)` 等で参照。値だけ欲しいときは同ファイルを直接読む
3. **アクセシビリティを担保**: `references/accessibility.md` 末尾のチェックリストを満たす（コントラスト・フォーカス・見出し階層・alt・ターゲットサイズ・色以外の手掛かり）
4. **コンポーネントが要るとき**: `references/components.md` で slug と状態を引き、**用途・作例・要件は `<docs>/components/<slug>/index.md` を読む**。実装は GitHub `digital-go-jp/design-system-example-components-html` / `-react`（MIT）、Tailwind は `digital-go-jp/tailwind-theme-plugin`、各 Storybook。本スキルは実装コードを同梱しない。**非推奨**のコンポーネントは選ばない
5. **クレジット**: 加工してUIに組み込む利用は出典明記不要だが、フッター等に「デジタル庁デザインシステム（DADS, β版）を参考に構築」と中立記載を推奨。**「デジタル庁が作成/公認」と誤認させない**。詳細 `references/licensing.md`

### デザインの質を上げるとき
配色・レイアウトの審美性を高めたい場合は、本スキル（トークン・制約・a11y）と `frontend-design` スキルを併用する。DADSはトークンと原則を与え、frontend-design は構図・余白リズム・タイポ階層の練り込みを助ける。

## ライセンス（要点）
- コードスニペット・デザイントークン = **MIT**、Figma = **CC BY 4.0**、Material Symbols = **Apache 2.0**。**商用・改変・再配布いずれも可**
- **公式Markdownドキュメントは「デザインシステム本体」扱い**で、引用・転載時は出典記載が必要。キャッシュを git 管理下や配布物へコピーしない
- 加工してUIに組み込む利用は**出典明記不要**。未編集公開時はクレジット必須
- 同梱 `assets/LICENSE-design-tokens`（MIT全文）は削除しない。詳細は `references/licensing.md`

## 同梱ファイル
| ファイル | 内容 | 読むとき |
|---|---|---|
| `scripts/dads-docs` | 公式Markdownの取得・状態確認（`python3 scripts/dads-docs status｜check｜fetch [--force]`） | 初回セットアップ・鮮度確認 |
| `references/design-tokens.md` | トークンの選び方・トークン化されていない規定（機能カラー/余白/レイアウト/リンク/アイコン） | 値や規則の要点が要るとき |
| `references/components.md` | 49コンポーネントの索引（名称/slug/状態）と名称変遷 | UI部品を選ぶとき（詳細は `<docs>` へ） |
| `references/accessibility.md` | a11y要件・コントラスト・適用時チェックリスト | 配色確定・実装レビュー時 |
| `references/licensing.md` | ライセンス詳細・クレジット運用 | 公開・再配布前 |
| `assets/dads-tokens.css` | 実数値のCSS変数（MIT, v2.0.1） | 成果物に組み込むとき・HEXを引くとき |
| `assets/LICENSE-design-tokens` | 上記CSSのMITライセンス全文 | 再配布時に同梱 |

## 鮮度管理
リポジトリ側の記述が古びていないかは、次で確認する。

- `python3 scripts/dads-docs fetch` — 新しいアーカイブがあれば差し替わる。`status` の `archive_date` / `site_version` が現行値
- `npm view @digital-go-jp/design-tokens version` — v2.0.1 から上がっていれば `assets/dads-tokens.css` を差し替え、`references/design-tokens.md` の照合日を更新する
- `<docs>/updates/` または `https://design.digital.go.jp/dads/updates-dads/` — 名称変更・コンポーネント追加・非推奨化はここに出る。`references/components.md` の索引に反映する

`references/*.md` の照合時点: **2026-08-28（サイト β版 v2.17.1 / Markdown 2026-08-19版 / tokens v2.0.1）**。
