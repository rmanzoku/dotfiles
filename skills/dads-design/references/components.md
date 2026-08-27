# DADS コンポーネント索引（49種）

**この索引は「何が在るか」を引くためのもの。用途・設計原則・作例・アクセシビリティ要件は公式Markdown（`<docs>/components/<slug>/index.md`）が正本。** `<docs>` は `python3 scripts/dads-docs status` が示す `docs root`。未取得なら `python3 scripts/dads-docs fetch`。

- 各コンポーネントのURL: `https://design.digital.go.jp/dads/components/<slug>/`
- 実装: GitHub `digital-go-jp/design-system-example-components-html` / `-react`（MIT）、Tailwind は `digital-go-jp/tailwind-theme-plugin`、各 Storybook
- 変更履歴は `<docs>/components/<slug>/changelog.md`（存在するもののみ）

## 状態の意味
- **非推奨**: アクセシビリティ／ユーザビリティの観点から公式が deprecated と表示。新規設計では選ばない。やむを得ず使う場合は不利益を受けるユーザーの存在を前提に扱う。
- **準備中**: 本サイトのガイドラインが未整備。Figma v1系デザインデータ内のガイドラインを参照する（コンポーネントには互換性がある）。Figma v2・HTML/React 実装は提供済みのものが多い。

| 日本語名 | slug | 状態 |
|---|---|---|
| アコーディオン | accordion | ― |
| イメージスライダー | image-slider | ― |
| インプットテキスト | input-text | ― |
| 引用ブロック | blockquote | 準備中 |
| カード | card | ― |
| 箇条書きリスト | list | ― |
| 画像 | image | 準備中 |
| カルーセル | carousel | ― |
| 緊急時バナー | emergency-banner | ― |
| 検索ボックス | search-box | 準備中 |
| コンボボックス | combobox | 準備中 |
| スイッチ | switch | 準備中 |
| 水平メニュー | horizontal-menu | 準備中 |
| スクロールトップボタン | scroll-top-button | **非推奨** |
| ステップナビゲーション | step-navigation | 準備中 |
| 説明リスト | description-list | 準備中 |
| セレクトボックス | select | ― |
| タブ | tab | 準備中 |
| チェックボックス | checkbox | ― |
| チップタグ | chip-tag | 準備中 |
| チップラベル | chip-label | 準備中 |
| 注釈ブロック | notice-block | 準備中 |
| ディスクロージャー | disclosure | ― |
| ディバイダー | divider | ― |
| テーブルコントロール | table-control | 準備中 |
| テーブル／データテーブル | table | ― |
| テキストエリア | textarea | ― |
| ドロワー | drawer | ― |
| ノティフィケーションバナー | notification-banner | ― |
| パンくずナビゲーション | breadcrumb | ― |
| ハンバーガーメニューボタン | hamburger-menu-button | ― |
| 日付ピッカー／カレンダー | date-picker | ― |
| ファイルアップロード／ドロップエリア | file-upload | ― |
| プログレスインジケーター | progress-indicator | 準備中 |
| ページナビゲーション | page-navigation | 準備中 |
| ヘッダーコンテナ | header-container | ― |
| ボタン | button | ― |
| ボトムナビゲーション | bottom-navigation | **非推奨** |
| 見出し | heading | ― |
| メガメニュー | mega-menu | 準備中 |
| メニューリスト | menu-list | ― |
| メニューリストボックス | menu-list-box | ― |
| モーダルダイアログ | modal-dialog | 準備中 |
| 目次 | toc | 準備中 |
| モバイルメニュー | mobile-menu | ― |
| ユーティリティリンク | utility-link | ― |
| ラジオボタン | radio | ― |
| ランゲージセレクター | language-selector | ― |
| リソースリスト | resource-list | 準備中 |

## 名称・slug の変遷（古い記述に出会ったときの読み替え）
上流のリネームは本索引が追随するが、外部の記事や過去の成果物には旧称が残る。

| 旧 | 新 | 時期 |
|---|---|---|
| slug `dialog` | slug `modal-dialog` | 旧URLは無効 |
| パンくずリスト | パンくずナビゲーション | 2026-08-19 |
| グローバルメニュー | 水平メニュー | 2026-05-27 |
