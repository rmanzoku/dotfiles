---
title: "ADR 0082: Harness 標準に寄せ、自走範囲の規定を緩める"
status: accepted
date: 2026-10-28
worked_at: 2026-10-28 JST
agent_model: "Claude Opus 5.5 (claude-opus-5-5)"
---

# Context

2026-10-28、利用者はマシン全体の AI 運用方針を次のように示した。

- Claude をオーケストレーター（窓口）とする。
- 作業は費用効率のため Codex に App Server 経由で任せる。
- Harness（Claude Code・Codex）が持つ標準の振る舞いを、こちらで重ねてテキスト化しない。
- Harness の保守的な部分を解除する方向でルールを整える。

この方針に照らして、共通ルール、repo の `AGENTS.md`、agent 定義、plugin を棚卸しした（作業 worktree の `.context/ai-ops-policy-review/report.md`）。そのうえで、利用者が次の項目を承認した。

# Decision

1. **可逆性と自走範囲の節を 6 bullet から 3 bullet に圧縮する。** 権限設定は実行できる範囲を決めるだけとし、範囲内の操作は ADR 0068 の 3 条件で判定する。確認を求めるのは、3 条件を満たさないか判定できない操作だけとする。削除したのは次の規定で、いずれも 3 条件と「判定できなければ止まる」から同じ結論が導けることを確認した。
   - 取り消し手段の存在を根拠にしない
   - 停止点の細則
   - 規約を推測しない
   - permission ≠ 実行してよい
   - prompt 回避の禁止
2. **`worker` と `mechanical` の agent 定義を Claude・Codex の両方から削除する。** 利用者の判断: Harness が持つ汎用 subagent の抽象化にすぎず不要。要件の決まった作業は Codex（`codex-runner`）が担う。
3. **Claude Code の codex plugin（`codex@openai-codex`）を無効にする。** Codex への経路を `codex-runner` に一本化する。ADR 0012 の有効化判断を置き換える。marketplace の登録は残す。
4. **repo `AGENTS.md` から共通ルールとの重複を削除する。** 対象は「作業姿勢」「恒久指示の反映運用」「Artifact」のうち共通ルールと同文のもの。ADR 0061 の Decision 3（自己完結の維持）を置き換える。この repo では共通ルールも読み込まれるので、二重に読む必要がない。他者がこの repo を参照する場合は、共通ルールの正本を読めばよい。
5. **ADR とドキュメントの読み方を共通ルールに加える。** ADR やドキュメントは過去の判断の記録であり、現時点で最適であることを示さない。現在の目的・指示・観測事実と食い違う場合は、記録に合わせて判断を曲げず、見直しを提案する。全リポジトリに適用するため、repo 個別ではなく共通ルールに置く。
6. **コンピューター操作を Codex に委ねる場合の検証時期を決める。** ルール化するときと、新しいマシン（新規セッション環境）を用意するときに smoke を行う。`codex-runner` の app-server 経路は server からの承認 request を拒否するため、承認を伴う操作が完走するかは環境に依存する。この委譲をルール化する作業は、本 ADR の範囲外とする。

# Evidence

1 の効果検証には empirical-prompt-tuning を使った。条件は次のとおり。
- 白紙の実行者は sonnet で、計 10 run。
- シナリオは ADR 0068 の A・B・C をそのまま使い、取り消し手段のある SaaS 操作をホールドアウト D として加えた。

結果は次のとおり。
- [critical] は新旧とも全 run で ○、正答率は全 run で 100%。
- 圧縮版の所要時間は 15.7〜19.3 秒で、旧版の A・B・C（21.7〜29.0 秒）より短かった。
- ホールドアウトでの低下はなかった。
- 厳密な収束条件（新規不明点 0 が 2 ラウンド連続）には未達で、resource cutoff で打ち切った。残った不明点は境界の例示を求めるもので、旧版でも同じ種類が出ていた。
- 証跡は作業 worktree の `.context/ai-ops-policy-review/eval/`。

# Consequences

- chezmoi は source を削除しても target を消さない。そのため既存マシンでは `~/.claude/agents/{worker,mechanical}.md` と `~/.codex/agents/{worker,mechanical}.toml` を 1 回だけ手動で削除する。
- `scripts/instruction-gc` の role 名検査から `worker` と `mechanical` を外した。
- ADR 0068 の判定例の表は、引き続き境界判断の参照に使える。条文から消した規定の意図も 3 条件に含まれる。
- 未決だった事項（窓口の定義、Codex への既定の振り分け、Harness と重複する他の bullet の削除、Claude 指示ファイルの template 化）は [ADR 0084](0084-orchestrator-rules-and-claude-template.md) で決めた。
