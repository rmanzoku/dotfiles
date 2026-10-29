---
title: "ADR 0084: 窓口の定義、Harness 重複の削除、Claude 指示ファイルの template 化"
status: accepted
date: 2026-10-29
worked_at: 2026-10-29 JST
agent_model: "Claude Opus 5.5 (claude-opus-5-5)"
---

# Context

ADR 0082 のもとになった棚卸しで、未決のまま残した事項がある。2026-10-29、利用者がそれらに回答した。回答は次のとおり。

- Codex への委譲は、マシン全体の既定に書かない。委譲するかは各リポジトリで決める。そのため executor の既定を定める ADR も置かない。
- 窓口（オーケストレーター）の定義を共通ルールに書く。既存の「委譲」節の一部を置き換え、常時読み込まれる量を増やさない。
- Harness と重複するルールは、棚卸しの案どおり削除する。
- Claude の指示ファイルを template にする。
- レーン運用はマシン全体には書かない。`agent-orchestration-evaluator` の reference に置く。
- source の `Library/` を private にし、700 を維持する。

# Decision

1. **共通ルールの「委譲」節を「窓口と委譲」に置き換える。** 先頭の 2 bullet（委譲の判断基準、委譲時の入力契約）を、次の 2 bullet にする。
   - 利用者と対話するセッションを窓口とし、subagent・サブセッション・外部 AI の起動・指示・検収・統合は窓口かセッションオーナーが持つ。窓口として起動されていないときは、渡された依頼文を正本とし、恒久指示の git 反映や再委譲をしない。
   - 作業を分けるかは Harness の基準に従う。加えて、資源を専有する作業と、利用者との往復を要しない作業も分割の理由に含める。

   「Codex を既定とする」文は入れない。
2. **Harness 標準と重複する規定を削除または修正する。**
   - 共通ルール: 「最小実装」「必要な行だけ変更」「エラーの意味分類」、Plan で「Phase ごとに Skill を明示」を削除する。「成功条件」はバグ修正の確認手段の 1 文に圧縮する。一時ファイルの置き場は、Harness の指定（scratchpad など）を優先するよう修正する。
   - Claude 固有: 「import の説明」「Codex 節の無視」、artifact gate の hook と validator（ADR 0072 で撤去済み）、sed・perl・xargs の使い方を削除する。
   - Codex 固有: artifact gate の hook と validator を削除する。「恒久設定を緩めず、実行時だけ danger-full-access」も、実際の config が恒久的に `danger-full-access` であり矛盾するため削除する。
3. **`dot_claude/CLAUDE.md` を `dot_claude/CLAUDE.md.tmpl` にする。** `includeTemplate "common-rules.md"` で共通ブロックを取り込み、Codex 固有節を Claude に配備しない。ADR 0050 を改訂する。
4. **レーン運用の一般版は `skills/agent-orchestration-evaluator/references/tuning-patterns.md` の「Lane design」節に置く。** 中身は規模の判定、分割の判定、repo `AGENTS.md` 用のテンプレート。常時承認と回ごとの承認は、Harness の権限設定で分ける。
5. **source の `Library/` を `private_Library/private_LaunchAgents/` にリネームする。** apply しても `~/Library` と `~/Library/LaunchAgents` が 700 のまま保たれる。

# Consequences

- 共通ルールの bullet 数は、ADR 0082 の前の 40 から 34 に減る。Claude に配備されるファイルから Codex 固有節がなくなる。
- 未対応: 棚卸しで「緩和」とした 2 件は今回の範囲外として残す。共通ルールの「不足時は仮実装を出さず確認に留める」と、「md を編集したらファイル全体を見直す」の 2 件。
- このマシンでは apply によって `~/Library/LaunchAgents/local.ac-awake.plist` が配備される。plist は `Disabled` のままで、`launchctl bootstrap` はしない。
