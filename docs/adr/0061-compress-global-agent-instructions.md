---
title: "ADR 0061: グローバル AI 指示を経験的等価性検証つきで圧縮する"
status: accepted
date: 2026-08-04
worked_at: 2026-08-04 13:10 JST
agent_model: Claude Fable 5
---

# ADR 0061: グローバル AI 指示を経験的等価性検証つきで圧縮する

## Context

`~/.codex/AGENTS.md`(common-rules template + Codex 固有節)は 90 行 / 約 7,000 字まで成長し、連作記事の基準(ゴミ定義・増幅の式・書き方 7 Tips)で自己監査した結果、次の 4 種の冗長が確認された。

1. モデル既定挙動の教示(tool error のツール別対応 335 字など)
2. クラスタ内重複(secret 3 本、ログ 3 本、artifact gate 3 本、反映運用の再説明)
3. 機械執行済みルールの詳細文言(phase_artifact_hook / validator が保証する範囲)
4. agent 定義 description との二重持ち(tech / biz の用途説明)

## Decision

1. common-rules を 51→34 bullets、Codex 固有節を 25→12 bullets に圧縮し、配備後 90 行→62 行(約 31% 減)とする。削るのは上記 4 種に該当する箇所に限り、固有判断(Freee/Google 境界、fallback 禁止、匿名比較、作業姿勢コア 8 本、Plan 2 本)は保持する。
2. 圧縮の等価性は empirical-prompt-tuning の手法で検証する。旧・新を読むブラインド実行者(sonnet、新規 subagent)に同一シナリオ 3 種+hold-out 1 種([critical] 付きチェックリスト事前固定)を実行させ、[critical] 達成が同等であることを確認してから適用する。実施結果: 全 [critical] 11/11 で新旧同等、圧縮起因の新規不明瞭点 0、hold-out(Freee/Google 境界)も全項目達成。
3. repo AGENTS.md の重複ブロック(Q8 で自己完結維持を決定済み)は同じ統合文言へ同期し、instruction-gc の近似非一致検査で乖離を監視し続ける。
4. 削除した詳細の受け皿: ツール別 error 対応はモデル既定挙動として文書化しない。ログ内容の詳細列挙は `docs/runner-skill-governance.md`。自動実行の chezmoi 管理規定は repo AGENTS.md「Desktop 自動実行設定管理」節。fork_context の runtime 観測は ADR-0040。tech/biz の用途は各 agent 定義の description。

## Consequences

- 全セッションの常駐指示が約 1/3 軽くなり、1 ルール 1 記述の原則(gpt-5-6 / fable-5 tuning 準拠)に揃う
- 検証記録は dotfiles `.context/2026-08-04-instruction-cleanup/05-06` に保存(ephemeral)。判断本体は本 ADR を正本とする
- 公開予定の記事「AGENTS.md とCLAUDE.md、全文公開」は掲載全文と行数表現の更新が必要(workspace 側 publish_time_tasks に記載)
- 新旧共通で残る構造的曖昧性(Phase 該当判定、ADR 要否閾値、secret 初期登録者、personal allowlist 粒度)は圧縮と独立した将来の改善候補として検証記録に残した
