---
title: "Native Office Skill Discovery"
status: accepted
date: 2026-09-12
updated_at: 2026-09-13
worked_at: "2026-09-12T23:58:55+09:00"
agent_model: "GPT-6 Astra"
---

# Native Office Skill Discovery

## 状況

Codex の標準 documents / presentations / spreadsheets / pdf plugins と、Claude document-skills cache を指す4つの user Skill symlink が同時に公開されていた。用途が重複し、Claude cache のバージョン付きパスも Codex 側の配備に持ち込まれていた。

## 決定と理由

Codex の PowerPoint / Excel は自身の標準 plugins へ集約し、対応する cross-host cache symlink を発見対象から除去する。Claude は自身の document-skills plugin を使う。両者の plugin は既存の managed Skill parity の対象外であり、外部 Skill のセット・ref を揃える方針は変えない。

Word / PDF の既存入口は維持する。標準 Word plugin 本文には読取 workflow、PDF 本文には既存ファイルの form 編集があるが、description だけから Word 読取・一般 PDF 編集へ確実に到達するという独立選択 probe は合格しなかった。能力が存在しないと断定せず、入口を除去する根拠が足りないため互換入口を残す。削除量より選択の維持を優先する。

正規の復元手順は `docs/skills-install-manifest.md` に置く。`scripts/instruction-gc` は退役したリンクの再導入を検出する。第三者の plugin cache は編集せず、モデル・effort・permission の既定値には変更を加えない。

## 却下した代替案

- 検証結果によらず4件とも除去する: Word / PDF の選択について不確実性を残すため採らない。
- 検証済みの PowerPoint / Excel も両系列の提示を続ける: 同じファイル形式の候補が競合する。
- バージョン付き cache を複製・編集する: upstream の更新と配備管理が分岐する。
- 4つの無効化設定を config に追加する: 今回の対象は不要な手動リンクであり、リンクの配備方針を直す方が新しい設定と cache path 依存を増やさない。

## 検証と再検討

変更前後の Codex skill discovery、Word / PowerPoint / spreadsheet / PDF の作成・編集・読取の選択、非対象依頼での非選択を確認する。これは入口の検証であり、全機能の成果物品質の同等性を主張しない。標準 plugin の更新等で Word 読取・PDF 編集の選択が明確になり、同じ critical checklist が旧構成以上に合格したときに、残した2つの入口を再検討する。

巻き戻しは作業 artifact に記録した symlink を復元する。Claude plugin cache と Codex 標準 plugin は保持するため再インストールは不要。再導入する場合は manifest と検出規約も同じ判断に合わせて戻す。
