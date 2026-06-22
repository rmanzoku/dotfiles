# DADS デザイントークン リファレンス

デジタル庁デザインシステム（DADS, β版）のデザイントークンを数値で網羅したリファレンス。

- **実数値（HEX / rem / box-shadow）の正本**: `@digital-go-jp/design-tokens` v2.0.1 の `tokens.css`（MIT License, Copyright (c) 2023 デジタル庁）。本スキルの `assets/dads-tokens.css` に同梱。
- **意味づけ・命名・運用ルール**: 公式ドキュメント `https://design.digital.go.jp/dads/foundations/*`。
- DADSはβ版。トークンは更新されうる（更新告知: `/dads/updates-dads/`）。重要な配色・サイズを確定する前に最新版（npm `@digital-go-jp/design-tokens` / Figma Community）の確認を推奨。
- 実装で即利用する場合は `assets/dads-tokens.css` を読み込み `var(--color-key-700)` 等のCSS変数を参照するのが最も確実。

## 目次
1. カラー（プリミティブ／ニュートラル／セマンティック／キー）
2. タイポグラフィ（フォント／サイズ／行間／テキストスタイル）
3. 角丸（border-radius）
4. エレベーション（影）
5. 余白（spacing）
6. レイアウト（ブレークポイント／グリッド）
7. リンクテキスト
8. アイコン

---

## 1. カラー

色相 = 10系統（Blue, Light Blue, Cyan, Green, Lime, Yellow, Orange, Red, Magenta, Purple）× 各13階調（50〜1200）。
数値が大きいほど暗い。**キーカラー（プライマリ）は Blue**（`--color-key-*` は Blue にエイリアス）。

### 1.1 プリミティブカラー（全色相 × 全階調 HEX）

CSS変数名: `--color-primitive-<hue>-<step>`（例: `--color-primitive-blue-700`）。

| step | blue | light-blue | cyan | green | lime | yellow | orange | red | magenta | purple |
|---|---|---|---|---|---|---|---|---|---|---|
| 50 | #e8f1fe | #f0f9ff | #e9f7f9 | #e6f5ec | #ebfad9 | #fbf5e0 | #ffeee2 | #fdeeee | #f3e5f4 | #f1eafa |
| 100 | #d9e6ff | #dcf0ff | #c8f8ff | #c2e5d1 | #d0f5a2 | #fff0b3 | #ffdfca | #ffdada | #ffd0ff | #ecddff |
| 200 | #c5d7fb | #c0e4ff | #99f2ff | #9bd4b5 | #c0f354 | #ffe380 | #ffc199 | #ffbbbb | #ffaeff | #ddc2ff |
| 300 | #9db7f9 | #97d3ff | #79e2f2 | #71c598 | #ade830 | #ffd43d | #ffa66d | #ff9696 | #ff8eff | #cda6ff |
| 400 | #7096f8 | #57b8ff | #2bc8e4 | #51b883 | #9ddd15 | #ffc700 | #ff8d44 | #ff7171 | #f661f6 | #bb87ff |
| 500 | #4979f5 | #39abff | #01b7d6 | #2cac6e | #8cc80c | #ebb700 | #ff7628 | #ff5454 | #f137f1 | #a565f8 |
| 600 | #3460fb | #008bf2 | #00a3bf | #259d63 | #7eb40d | #d2a400 | #fb5b01 | #fe3939 | #db00db | #8843e1 |
| 700 | #264af4 | #0877d7 | #008da6 | #1d8b56 | #6fa104 | #b78f00 | #e25100 | #fa0000 | #c000c0 | #6f23d0 |
| 800 | #0031d8 | #0066be | #008299 | #197a4b | #618e00 | #a58000 | #c74700 | #ec0000 | #aa00aa | #5c10be |
| 900 | #0017c1 | #0055ad | #006f83 | #115a36 | #507500 | #927200 | #ac3e00 | #ce0000 | #8b008b | #5109ad |
| 1000 | #00118f | #00428c | #006173 | #0c472a | #3e5a00 | #806300 | #8b3200 | #a90000 | #6c006c | #41048e |
| 1100 | #000071 | #00316a | #004c59 | #08351f | #2c4100 | #6e5600 | #6d2700 | #850000 | #500050 | #30016c |
| 1200 | #000060 | #00234b | #003741 | #032213 | #1e2d00 | #604b00 | #541e00 | #620000 | #3b003b | #21004b |

### 1.2 ニュートラル

| トークン | 値 | 備考 |
|---|---|---|
| `--color-neutral-white` | #ffffff | |
| `--color-neutral-black` | #000000 | |
| `--color-neutral-solid-gray-50` | #f2f2f2 | |
| `--color-neutral-solid-gray-100` | #e6e6e6 | |
| `--color-neutral-solid-gray-200` | #cccccc | |
| `--color-neutral-solid-gray-300` | #b3b3b3 | |
| `--color-neutral-solid-gray-400` | #999999 | |
| `--color-neutral-solid-gray-420` | #949494 | **白背景に対しコントラスト比 3:1**（非テキストの境界） |
| `--color-neutral-solid-gray-500` | #7f7f7f | |
| `--color-neutral-solid-gray-536` | #767676 | **白・黒の双方に 4.5:1**（テキスト最小） |
| `--color-neutral-solid-gray-600` | #666666 | **黒背景に対し 3:1** |
| `--color-neutral-solid-gray-700` | #4d4d4d | |
| `--color-neutral-solid-gray-800` | #333333 | |
| `--color-neutral-solid-gray-900` | #1a1a1a | 本文テキスト相当 |

不透明度グレー `--color-neutral-opacity-gray-<step>` = `rgba(0,0,0,α)`。α: 50=0.05, 100=0.1, 200=0.2, 300=0.3, 400=0.4, 420=0.42, 500=0.5, 536=0.54, 600=0.6, 700=0.7, 800=0.8, 900=0.9。背景の上に重ねる罫線・分割線・無効状態などに使用。

### 1.3 セマンティック（システム）カラー

用途別トークン。明暗2段階（-1 が標準、-2 が濃い）。

| トークン | 参照プリミティブ | 解決HEX | 用途 |
|---|---|---|---|
| `--color-semantic-success-1` | green-600 | #259d63 | 成功・完了・安全 |
| `--color-semantic-success-2` | green-800 | #197a4b | 成功（濃） |
| `--color-semantic-error-1` | red-800 | #ec0000 | エラー・危険 |
| `--color-semantic-error-2` | red-900 | #ce0000 | エラー（濃） |
| `--color-semantic-warning-yellow-1` | yellow-700 | #b78f00 | 警告（黄系） |
| `--color-semantic-warning-yellow-2` | yellow-900 | #927200 | 警告 黄（濃） |
| `--color-semantic-warning-orange-1` | orange-600 | #fb5b01 | 警告（橙系） |
| `--color-semantic-warning-orange-2` | orange-800 | #c74700 | 警告 橙（濃） |

### 1.4 キーカラー（プライマリ）

`--color-key-<step>`（50〜1200）は **Blue にエイリアス**。サービスのブランド色に合わせて差し替える設計（DADSの「スタイルガイド」概念）。
- 例: キー標準 `--color-key-700` = #264af4 / 濃 `--color-key-800` = #0031d8 / 淡背景 `--color-key-50` = #e8f1fe。

### 1.5 カラー運用原則
- 前景色と背景色は必ず両方指定する。
- **色のみで情報を区別しない**（色覚多様性: 状態・リンク等は形・下線・アイコンを併用）。
- テキストは原則コントラスト比 **4.5:1 以上**（DADSはサイズによらず4.5:1を採用）。詳細は `accessibility.md`。

---

## 2. タイポグラフィ

### 2.1 フォントファミリー
| 区分 | CSS変数 | 値 |
|---|---|---|
| 和文・標準（本文/見出し） | `--font-family-sans` | `'Noto Sans JP', -apple-system, BlinkMacSystemFont, sans-serif` |
| 等幅（コード等） | `--font-family-mono` | `'Noto Sans Mono', monospace` |

Noto Sans JP は SIL Open Font License 1.1。欧文専用ファミリは定義されず、和文フォントの欧文グリフを使用。

### 2.2 ウェイト
`--font-weight-400` = 400（N: Normal） / `--font-weight-700` = 700（B: Bold）。中間ウェイトは使わない。

### 2.3 フォントサイズ
`--font-size-<px>`（rem値。root=16pxで 1rem=16px）。

| トークン | rem | px |
|---|---|---|
| `--font-size-14` | 0.875 | 14 |
| `--font-size-16` | 1 | 16 |
| `--font-size-17` | 1.0625 | 17 |
| `--font-size-18` | 1.125 | 18 |
| `--font-size-20` | 1.25 | 20 |
| `--font-size-22` | 1.375 | 22 |
| `--font-size-24` | 1.5 | 24 |
| `--font-size-26` | 1.625 | 26 |
| `--font-size-28` | 1.75 | 28 |
| `--font-size-32` | 2 | 32 |
| `--font-size-36` | 2.25 | 36 |
| `--font-size-45` | 2.8125 | 45 |
| `--font-size-48` | 3 | 48 |
| `--font-size-57` | 3.5625 | 57 |
| `--font-size-64` | 4 | 64 |

### 2.4 行間（line-height）
`--line-height-<n>`: 100=1.0, 120=1.2, 130=1.3, 140=1.4, 150=1.5, 160=1.6, 170=1.7, 175=1.75。

用途の目安: 100=ボタン等1行 / 120・130=情報密度優先（管理・業務画面） / 140=大きめ見出し / 150=本文の最低限 / 160=一般的な本文 / 170=可読性重視の本文 / 175=広いグリッド幅の本文。

### 2.5 テキストスタイル（合成トークン）
命名規則 `<カテゴリ>-<サイズpx><N|B>-<行間%>`（例 `Std-16N-170` = Standard / 16px / 400 / line-height 1.7）。`tokens.css` には素トークン（サイズ・行間・ウェイト）のみ含まれ、合成スタイルはFigma側の定義。代表カテゴリ:

- **Display（Dsp）48/57/64px**: 特大見出し。line-height 140%。例 `Dsp-64B-140`。
- **Standard（Std）16〜45px**: 見出し〜本文の主力。本文は `Std-16N-170` / `Std-17N-170` / `Std-16N-175`。見出しは `Std-20B-150`〜`Std-45B-140`。字間 letter-spacing は 16〜26pxで 2%(0.02em)、32〜36pxで 1%、45pxで 0。
- **Dense（Dns）14/16/17px**: 情報密度優先（管理・業務画面）。line-height 120%/130%。
- **Oneline（Oln）14/16/17px**: UI/ボタン等の1行。line-height 100%、字間 2%。
- **Mono 14/16/17px**: コード等（Noto Sans Mono）。line-height 150%。

本文の既定はおおむね **16px / line-height 1.7（`Std-16N-170`）**。見出しは Bold + line-height 1.4〜1.5。

---

## 3. 角丸（border-radius）

`--border-radius-<n>`（rem）。

| トークン | rem | px | 用途の目安 |
|---|---|---|---|
| `--border-radius-4` | 0.25 | 4 | 小（タグ・チップ・入力欄の一部） |
| `--border-radius-6` | 0.375 | 6 | 小〜中 |
| `--border-radius-8` | 0.5 | 8 | 角丸スモール（ボタン・入力欄） |
| `--border-radius-12` | 0.75 | 12 | 角丸ミディアム（長方形） |
| `--border-radius-16` | 1 | 16 | 角丸ミディアム（正方形）/ カード |
| `--border-radius-24` | 1.5 | 24 | 大きめコンテナ |
| `--border-radius-32` | 2 | 32 | 角丸ラージ（正方形） |
| `--border-radius-full` | 624.9375 | ― | 完全な円/ピル形状（高さの50%相当を強制） |

公式の「角の形状」分類: なし=0 / スモール=8 / ミディアム=正方形16・長方形12 / ラージ=正方形32・長方形16 / フル=50%。

---

## 4. エレベーション（影 / box-shadow）

`--elevation-<1..8>`。値が大きいほど高い（手前に浮く）。すべて2層構成（広く淡い影 + 近く濃い影）。

| トークン | box-shadow |
|---|---|
| `--elevation-1` | `0 2px 8px 1px rgba(0,0,0,0.1), 0 1px 5px 0 rgba(0,0,0,0.3)` |
| `--elevation-2` | `0 2px 12px 2px rgba(0,0,0,0.1), 0 1px 6px 0 rgba(0,0,0,0.3)` |
| `--elevation-3` | `0 4px 16px 3px rgba(0,0,0,0.1), 0 1px 6px 0 rgba(0,0,0,0.3)` |
| `--elevation-4` | `0 6px 20px 4px rgba(0,0,0,0.1), 0 2px 6px 0 rgba(0,0,0,0.3)` |
| `--elevation-5` | `0 8px 24px 5px rgba(0,0,0,0.1), 0 2px 10px 0 rgba(0,0,0,0.3)` |
| `--elevation-6` | `0 10px 30px 6px rgba(0,0,0,0.1), 0 3px 12px 0 rgba(0,0,0,0.3)` |
| `--elevation-7` | `0 12px 36px 7px rgba(0,0,0,0.1), 0 3px 14px 0 rgba(0,0,0,0.3)` |
| `--elevation-8` | `0 14px 40px 7px rgba(0,0,0,0.1), 0 3px 16px 0 rgba(0,0,0,0.3)` |

運用: 重なる要素は最低2段階の差をつける（例: 下にレベル1のボタンがあるダイアログはレベル3以上）。

---

## 5. 余白（spacing）

- **基準単位 = 8px グリッド**。余白・サイズは原則 8 の倍数（4pxは半グリッドとして補助的に）。
- 例示スケール: 8（等倍）/ 24（3倍）/ 64（8倍）。1画面の余白スケールは3〜5段階に収まることが多い。
- 注: `@digital-go-jp/design-tokens` v2.0.1 の `tokens.css` には **spacingトークンは含まれない**（8の倍数で運用する方針のため）。実装では `0.5rem`(8) `1rem`(16) `1.5rem`(24) `2rem`(32) `3rem`(48) `4rem`(64) 等を直接用いる。

---

## 6. レイアウト

| 項目 | 値 |
|---|---|
| ブレークポイント | **768px**（1点）。768px未満 = モバイル/タブレット、768px以上 = デスクトップ |
| グリッド | 12カラム基本。リキッドレイアウト（カラムまたはガターの一方可変） |
| ガター | 本文文字サイズの約2倍を目安（可変。固定pxの公式値なし） |
| マージン | ページ幅に応じ可変 |
| コンテンツ最大幅 | 公式の固定値明示なし（サービス側のスタイルガイドで決める） |
| カラム割り例 | 2カラム=9+3 / 8+4 / 6+6、3カラム=4+4+4 / 3+6+3、4カラム=3+3+3+3、オフセット=2offset+8 等 |

---

## 7. リンクテキスト

状態別の装飾規則（HEX値はFigma側。色相の方向性のみ公式記載）。

| 状態 | 規則 |
|---|---|
| Default | 青色テキスト＋**下線（必須）**。外部/新規タブは末尾にアイコン＋代替テキスト |
| Hover | 青が明るくなり下線が太くなる |
| Focus | 黒の外枠線＋黄色背景 |
| Active | オレンジ色 |
| Visited | マゼンタ/赤紫 |

原則: 色のみに依存せず下線等を併用。ターゲットサイズは最小 24×24px（上下に各4pxの余白があれば確保とみなす）。

---

## 8. アイコン

| 項目 | 値 |
|---|---|
| ターゲットサイズ（操作要素のアイコン） | 44×44px 以上 |
| コントラスト（テキストの一部） | 背景に対し 4.5:1 以上 |
| コントラスト（非テキスト要素） | 背景に対し 3:1 以上 |
| 配置種別 | フロント（ブロック先頭）/ リード（行頭）/ テール（行末）/ エンド（ブロック末尾） |

注: アイコンの出典フォント・標準サイズ・グレード等の具体仕様は公式HTMLに明記なし。Material Symbols 系のアイコンは Apache License 2.0（`licensing.md` 参照）。実アイコンは Figma / リソースページを参照。
