---
name: instruction-cleaner
description: Raise the cleaning rate of always-loaded instruction surfaces (AGENTS.md rules, skill descriptions, agent definitions) in the dotfiles repo. Runs instruction-gc, classifies findings by the ADR-0061 stale classes, fixes mechanical dead references, and proposes semantic deletions with probe evidence. Use when instruction-gc is non-green or for a staleness sweep, description diet, or instruction 掃除.
---

# Instruction Cleaner

連作「増幅と掃除」の掃除率 c を、この dotfiles repo の常時露出面に対して所有する workflow。設計判断の正本は ADR-0065、stale 分類の正本は ADR-0061。検知は `scripts/instruction-gc`、検証は empirical-prompt-tuning の probe 方式を使う。

## 対象面(露出頻度順)

1. first-party skill の description(毎セッション全文露出。最大の面)
2. common-rules(`.chezmoitemplates/common-rules.md` → 配備先 AGENTS.md / CLAUDE.md import)
3. agent 定義の description と本文(`dot_claude/agents/` / `dot_codex/agents/`)
4. skill 本文(発火時のみ露出。優先度は下)

external skill(repo `skills/` に実体がないもの)は読み取り専用。ダイエトは upstream 提案か install 差し替え判断としてユーザーへ返す。

## KPI(この 3 点だけ。削除量は KPI ではない)

- **鮮度 SLO**: gc の fail は即時解消。warn は次回 run までに解消するか、却下理由を PR / 作業結果に明記する
- **露出予算**: `docs/instruction-baseline.json` の値を超えない。意図的に増やすときは同じ変更内で baseline を更新し、増加理由を commit message に書く
- **等価性ガード**: 意味を持つ行の削除・圧縮は probe で維持を示したものだけを掃除に数える。probe を通らない削除は rollback する

## stale 分類(ADR-0061 の 4 クラス)

| クラス | 例 | 処理 |
|---|---|---|
| 死参照 | 退役 CLI 名、存在しない path、install 鮮度ずれ | 自動修正してよい |
| モデル既定挙動の教示 | 現行モデルが指示なしで満たす行(旧 rg 指定行) | 削除提案 + 挙動 probe |
| 期限切れ一時ルール | 解除条件が成立した ADR 由来の行 | 削除提案(ADR に解除を記録) |
| 重複 | 他ルール・他文書と同内容 | 統合提案 + 挙動 probe |

## ワークフロー

1. **observe**: `scripts/instruction-gc` を実行し、findings を分類する。露出量は gc の baseline チェックを使う
2. **classify**: 各 finding を上表のクラスへ割り当て、自動修正か提案かを決める
3. **verify**: 削除・圧縮ごとに probe を設計する
   - ルール本文の変更 → **挙動 probe**: blank-slate subagent に新 ruleset 全文と現実的シナリオを渡し、[critical] 付き固定チェックリストで判定(empirical-prompt-tuning の invocation contract に従う)
   - description の変更 → **発火 probe**: 旧 description 一覧と新一覧を別々の blank-slate 選択器に渡し、同一プロンプト集合(現実的発話 + 発火してはならない distractor)で選択を比較。critical プロンプト全一致、かつ新の正答数が旧を下回らないこと
4. **propose**: 機械的修正は直接 commit。意味的変更は PR にし、本文へ probe 結果・before/after 字数・却下 warn の理由を書く
5. **close**: gc を再実行し green を確認。baseline を実測値へ更新(下がった場合は必ず、上がった場合は意図的な時だけ)

## 実行環境の制約

- chezmoi checkout(`~/.local/share/chezmoi`)は複数セッションで共有される。dirty なら worktree を作って作業し、`chezmoi apply --source <worktree>` で配備検証する。共有 checkout で作業する場合は、HEAD blob に自分の編集だけを適用した staged blob を作り(`git hash-object -w` → `git update-index --cacheinfo`)、他セッションの未 commit 変更を巻き込まない
- 配備反映は対象を絞る: `chezmoi apply <target-path>`。全体 apply をしない
- skill を編集したら `scripts/skill-quick-validate skills/<name>` を通し、`gh skill install . <name> --from-local --agent claude-code --scope user` と `--agent codex` で再 install する(installed 実体が露出面)
- common-rules を編集したら repo ルートの AGENTS.md の重複 bullet を逐語同期する(gc check 3 が近似非一致を fail にする)
- git 未追跡の private_*(biz / tech / personal)は編集・commit しない。露出量の計測には installed 実体(`~/.claude/agents/`)を使ってよい

## してはならないこと

- 削除行数・削除バイト数を成果として報告すること(KPI は鮮度・予算・等価性のみ)
- probe なしの意味的削除、probe 失敗後の削除続行
- レポート時系列ファイルの新設(PR と gc 出力が記録。増やしてよい永続ファイルは baseline JSON のみ)
- 一度の掃除で複数クラスの大規模変更を混ぜること(probe の帰属が壊れる。1 PR = 1 クラス相当を目安)

## Validation

```bash
scripts/skill-quick-validate skills/instruction-cleaner
scripts/instruction-gc
```
