---
name: instruction-cleaner
description: "Close out staleness on always-loaded AI instruction surfaces in any repository: rules, skill descriptions, agent definitions, and related guidance. Use for dead references, expired or duplicate rules, trigger overlap, skill-doc contradictions, description diet, staleness sweeps, or 掃除・統廃合. Use repository sensors when present and portable observation when they are absent."
---

# Instruction Cleaner

任意のリポジトリで、常時または高頻度に読み込まれる AI 指示面（rules、skill description、agent 定義、関連 guidance）の staleness を閉じる。検知と閉包を分離し、意味を変える掃除は probe で等価性を確認する。

リポジトリ固有の sensor 名を前提にしない。既存 sensor が無ければ「Portable defaults」を使って開始する。sensor 不在は停止理由にしない。

## 役割分担

| 役割 | 担当 | 起動 |
|---|---|---|
| 機械検知 | repo の validator / linter / audit。無ければ Portable defaults | 毎回。安い |
| 意味検知 | repo の report-only reviewer / evaluator。無ければ blank-slate review | 意味クラスを掃く run で明示起動 |
| 動的検知 | 発火 probe(blank-slate 選択器) | description の取り合いはこれで直接観測する |
| 閉包 | cleaner(この skill) | findings を作業項目化し、修正または PR 提案で閉じる |
| 検証手法 | empirical-prompt-tuning | probe の設計規約として参照する。**skill の再現性改善は EPT の役割**で、この skill の対象外 |

review report からは、「対象・クラス・根拠・重要度」を 1 件 1 行の作業項目に抽出して閉包責任を引き取る。report が一時成果物なら、run 終了前に findings を作業項目へ抽出する。

## Portable defaults

repo 固有 sensor が見つからないときは、次の 4 スロットをその run の開始時に明記して進める。

- **sensor**: `rg --files --hidden -g '!.git/**'` で hidden な `.github/` 等を含む指示面候補（`AGENTS.md`、`CLAUDE.md`、`*instructions*.md`、`**/SKILL.md`、agent 定義）を列挙し、既存 docs と設定から実際の読み込み面を特定する。`rg` と path 存在確認で死参照・期限語彙・重複規範・trigger 語彙の衝突を調べ、意味クラスは blank-slate reviewer に report-only で評価させる
- **露出指標**: 対象面ごとの文字数と、常時露出する description / rule の合計文字数を before / after で比較する。既存 baseline があればそれを優先する
- **等価性ガード**: repo 既存の validator / test に加え、意味変更には挙動 probe、description 変更には発火 probe を使う。既存 test が無いことを probe 省略の理由にしない
- **ratchet 先**: 既存の最寄りの validator / linter / CI check を使う。無ければ今回の再現可能な検査コマンドを提示し、同種 finding の再発時または依頼範囲に含まれる場合に最小 check として永続化する

永続 ratchet がまだ無くても observe / classify / verify / propose は進める。依頼範囲外で新しい CI や script を勝手に追加せず、close 時に「今回の修正は検証済みだが再発検知は未永続化」と明示する。

## stale 分類と処理

| クラス | 検知 | 検証 | 処理 |
|---|---|---|---|
| 死参照(退役 CLI 名・不存在 path・install ずれ) | 機械 sensor | path / install 確認 | 直接修正 |
| モデル既定挙動の教示 | 判断(evaluator / run 内) | 挙動 probe | 削除提案 |
| 期限切れ一時ルール | 期限語彙 / ADR expiry + 判断 | 挙動 probe | 削除提案(判断記録に解除を記録) |
| 重複(ルール間・skill と docs の矛盾) | reviewer / 機械近似検査 | 挙動 probe | 統合・修正提案 |
| description の取り合い(trigger 重複) | 発火 probe で衝突を観測 | 修正後に発火 probe 再実行 | description 修正提案 |
| skill 統廃合候補(役割重複・未使用) | reviewer + 使用実績 | 発火 probe + 移行手順 | 統廃合提案(manifest・install を同時更新) |

運用クラスの正本はこの表とする。

## KPI(この 3 点だけ。削除量は KPI ではない)

- **鮮度 SLO**: sensor の fail は即時解消。warn は次回 run までに解消するか、却下理由を PR / 作業結果に明記する
- **露出予算**: 既存 baseline、または Portable defaults で得た before 値を超えない。意図的に増やすときは同じ変更内で理由を記録する
- **等価性ガード**: 意味を持つ行の削除・圧縮は probe で維持を示したものだけを掃除に数える。probe を通らない削除は rollback する

## ワークフロー

1. **observe**: repo 固有 sensor を探索して実行する。見つからなければ Portable defaults を使う。意味クラスを掃く run では report-only reviewer を最狭 scope で起動し、report から作業項目を抽出する
2. **classify**: 各 finding を上表のクラスへ割り当て、自動修正か提案かを決める
3. **verify**: 削除・圧縮・統合ごとに probe を設計する
   - ルール本文の変更 → **挙動 probe**: blank-slate subagent に新 ruleset 全文と現実的シナリオを渡し、[critical] 付き固定チェックリストで判定(empirical-prompt-tuning の invocation contract に従う)
   - 削除対象が保守側の規定のとき → [critical] にはその規定が守っているように見える結末そのものを置く。攻め側の結末だけで固定すると、規定が無くても harness 既定で結末が保たれるため probe が空振りで通る
   - description の変更 → **発火 probe**: 旧一覧と新一覧を別々の blank-slate 選択器に渡し、同一プロンプト集合(現実的発話 + 発火してはならない distractor)で選択を比較。critical 全一致、かつ新の正答数が旧を下回らないこと
4. **propose**: repo の権限線とレビュー規約に従う。意味的変更には probe 結果・before/after 指標・却下 warn の理由を添える
5. **close**: 同じ sensor を再実行して green を確認する。既存 baseline は repo の更新規約に従う。**判断で検知した stale は、可能なら最寄りの validator / linter / CI check へ機械化してから閉じる**。永続化が依頼範囲外なら未 ratchet として明示する

## Repository adapter

作業開始時に repo の `AGENTS.md` 等を読み、sensor、baseline、validator、配備、レビュー、artifact の規約をこの core workflow へ差し込む。repo 固有の path や tool を core の必須条件へ昇格させない。

この dotfiles repo では次を adapter とする。

- sensor: `scripts/instruction-gc` と report-only の `docs-evaluator`
- 露出指標: `docs/instruction-baseline.json`
- 等価性ガード: validator + 挙動 / 発火 probe
- ratchet 先: `scripts/instruction-gc` の check（STALE_TERMS・閾値・allowlist 等）
- skill 更新の検証: `scripts/skill-quick-validate skills/<name>`
- 配備: `gh skill install . <name> --from-local --agent claude-code --scope user --force` と `--agent codex`

## してはならないこと

- 削除行数・削除バイト数を成果として報告すること(KPI は鮮度・予算・等価性のみ)
- probe なしの意味的削除、probe 失敗後の削除続行
- report-only sensor / reviewer を修正担当へ変えること(検出と閉包の分離が KPI 勾配の逆向きを防ぐ)
- repo 固有の sensor 不在だけを理由に作業全体を停止すること
- repo 規約や明確な再利用目的のないレポート時系列ファイルを新設すること
- 一度の掃除で複数クラスの大規模変更を混ぜること(probe の帰属が壊れる。1 change set = 1 クラス相当を目安)

## Validation

```bash
# repo 固有 validator があれば実行する
# 無ければ observe で使った portable commands と probe を再実行する
```
