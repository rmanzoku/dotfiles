---
name: instruction-cleaner
description: "Close out staleness on always-loaded instruction surfaces (rules, skill descriptions, agent definitions): consume instruction-gc and docs-evaluator findings, fix dead references, and propose deletions, trigger-overlap fixes, consolidation, and skill-docs contradiction fixes with probe evidence. Use when instruction-gc is non-green or for a staleness sweep, description diet, or 掃除・統廃合."
---

# Instruction Cleaner

dotfiles repo の常時露出指示面(共通ルール、skill description、agent 定義)の staleness を閉じる workflow。検知はセンサーに、根拠は ADR に置き、この skill は再現可能な手順だけを持つ(層分離: `docs/runner-skill-governance.md` §Layering、設計判断は ADR-0065)。

## 役割分担

| 役割 | 担当 | 起動 |
|---|---|---|
| 機械検知 | `scripts/instruction-gc`(閾値・退役語彙・drift・manifest・露出予算) | 毎回。安い |
| 意味検知 | `docs-evaluator`(統廃合候補・重複 guidance・skill と docs の矛盾。**report-only 契約は変えない**) | 意味クラスを掃く run で cleaner が明示起動 |
| 動的検知 | 発火 probe(blank-slate 選択器) | description の取り合いはこれで直接観測する |
| 閉包 | cleaner(この skill) | findings を作業項目化し、修正または PR 提案で閉じる |
| 検証手法 | empirical-prompt-tuning | probe の設計規約として参照する。**skill の再現性改善は EPT の役割**で、この skill の対象外 |

docs-evaluator の report(`Issues & Risks` と mode 固有節)からは、「対象・クラス・根拠・重要度」を 1 件 1 行の作業項目に抽出して閉包責任を引き取る。report は `.context/` のエフェメラルなので、**抽出せずに run を終えたら finding は消える**前提で扱う。

## stale 分類と処理

| クラス | 検知 | 検証 | 処理 |
|---|---|---|---|
| 死参照(退役 CLI 名・不存在 path・install ずれ) | gc | 不要 | 直接修正 |
| モデル既定挙動の教示 | 判断(evaluator / run 内) | 挙動 probe | 削除 PR |
| 期限切れ一時ルール | gc の ADR expiry + 判断 | 挙動 probe | 削除 PR(ADR に解除を記録) |
| 重複(ルール間・skill と docs の矛盾) | evaluator / gc 近似検査 | 挙動 probe | 統合・修正 PR |
| description の取り合い(trigger 重複) | 発火 probe で衝突を観測 | 修正後に発火 probe 再実行 | description 修正 PR |
| skill 統廃合候補(役割重複・未使用) | evaluator(stale-docs-review)+ 使用実績 | 発火 probe + 移行手順 | 統廃合 PR(manifest・install を同時更新) |

運用クラスの正本はこの表とする(設計根拠: 上 4 クラスは ADR-0061 の削除 4 分類を運用向けに再構成、下 2 クラスは ADR-0065 decision 9 で追加)。

## KPI(この 3 点だけ。削除量は KPI ではない)

- **鮮度 SLO**: gc の fail は即時解消。warn は次回 run までに解消するか、却下理由を PR / 作業結果に明記する
- **露出予算**: `docs/instruction-baseline.json` の値を超えない。意図的に増やすときは同じ変更内で baseline を更新し、増加理由を commit message に書く
- **等価性ガード**: 意味を持つ行の削除・圧縮は probe で維持を示したものだけを掃除に数える。probe を通らない削除は rollback する

## ワークフロー

1. **observe**: `scripts/instruction-gc` を実行する。意味クラス(表の下 5 行)を掃く run では `docs-evaluator` を最狭 mode(例: `stale-docs-review` / `guidance-consistency-review`)で起動し、report から作業項目を抽出する
2. **classify**: 各 finding を上表のクラスへ割り当て、自動修正か提案かを決める
3. **verify**: 削除・圧縮・統合ごとに probe を設計する
   - ルール本文の変更 → **挙動 probe**: blank-slate subagent に新 ruleset 全文と現実的シナリオを渡し、[critical] 付き固定チェックリストで判定(empirical-prompt-tuning の invocation contract に従う)
   - description の変更 → **発火 probe**: 旧一覧と新一覧を別々の blank-slate 選択器に渡し、同一プロンプト集合(現実的発話 + 発火してはならない distractor)で選択を比較。critical 全一致、かつ新の正答数が旧を下回らないこと
4. **propose**: 機械的修正は直接 commit。意味的変更は PR にし、本文へ probe 結果・before/after 字数・却下 warn の理由を書く
5. **close**: gc を再実行し green を確認。baseline を実測値へ更新(下がった場合は必ず、上がった場合は意図的な時だけ)。**判断で検知した stale は、可能なら gc の check(STALE_TERMS・閾値・allowlist 等)へ機械化してから閉じる**(ratchet。同じ判断を二度させない)

## 実行環境の制約

- chezmoi checkout(`~/.local/share/chezmoi`)は複数セッションで共有される。dirty なら worktree を作って作業し、`chezmoi apply --source <worktree>` で配備検証する。共有 checkout で作業する場合は、HEAD blob に自分の編集だけを適用した staged blob を作り(`git hash-object -w` → `git update-index --cacheinfo`)、他セッションの未 commit 変更を巻き込まない
- 配備反映は対象を絞る: `chezmoi apply <target-path>`。全体 apply をしない
- skill を編集したら `scripts/skill-quick-validate skills/<name>` を通し、`gh skill install . <name> --from-local --agent claude-code --scope user --force` と `--agent codex` で再 install する(installed 実体が露出面)。description の YAML 値に `: ` を含めるときは必ずダブルクォートで囲む(installer は厳密な YAML パース)
- common-rules を編集したら repo ルートの AGENTS.md の重複 bullet を逐語同期する(gc check 3 が近似非一致を fail にする)
- git 未追跡の private_*(biz / tech / personal)は編集・commit しない。露出量の計測には installed 実体(`~/.claude/agents/`)を使ってよい
- 統廃合で skill を退役させたら、名前を gc の STALE_TERMS へ追加し、manifest から削除し、installed 実体を除去する

## してはならないこと

- 削除行数・削除バイト数を成果として報告すること(KPI は鮮度・予算・等価性のみ)
- probe なしの意味的削除、probe 失敗後の削除続行
- docs-evaluator の report-only 契約を変えること(検出と閉包の分離が KPI 勾配の逆向きを防ぐ)
- 思想・根拠の長文をこの skill に書き足すこと(根拠は ADR-0065 / ADR-0061、層分離は governance doc が正本)
- レポート時系列ファイルの新設(PR と gc 出力が記録。増やしてよい永続ファイルは baseline JSON のみ)
- 一度の掃除で複数クラスの大規模変更を混ぜること(probe の帰属が壊れる。1 PR = 1 クラス相当を目安)

## Validation

```bash
scripts/skill-quick-validate skills/instruction-cleaner
scripts/instruction-gc
```
