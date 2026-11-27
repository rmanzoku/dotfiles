---
title: "ADR 0087: GPT-6.2 の prompt 整備を別 skill（gpt-6-2-tuning）にする"
status: accepted
date: 2026-11-27
worked_at: 2026-11-27 JST
agent_model: "Claude Opus 5.5 (claude-opus-5-5)"
---

# Context

OpenAI の latest-model guide が `gpt-6.2-astra` と `gpt-6.2-sol` を扱うようになり、利用者から GPT-6.2 向けのチューニング skill を作るよう指示があった。既存の `gpt-6-tuning`（ADR 0076）は GPT-6 Astra の観察に基づき、確認しすぎとテストしすぎを補正する内容になっている。

GPT-6.2 の公式 prompting guidance は、次の点で GPT-6 向けの補正と向きが逆か、別の観点を加えている。

- 確認しすぎではなく、次の手を提案して確認を待つ傾向を補正する。
- 検証を絞るのではなく、終える前に依頼の各項目を確かめる網羅的な確認パスを求める。テストの追加は依頼・repo 要件・回帰に限る。
- 既定で簡潔なので、「簡潔に」の指示を見直す。
- Responses API の top-level `instructions` が `input` の後ろに付く。会話途中の履歴編集で reasoning item が捨てられる。

# Decision

1. GPT-6.2 向けの整備は新しい skill `gpt-6-2-tuning` に置き、`gpt-6-tuning` には混ぜない。1 つの skill に両世代を入れると、同じ観点で逆向きの指示が並び、どちらの補正を当てるかを読み手が判断しなければならなくなるため。
2. `gpt-6-tuning` は GPT-6 / 6.1 / 6-luna の担当として残し、description と本文に GPT-6.2 は `gpt-6-2-tuning` を使うと書く。退役はしない。
3. `codex-runner` の `gpt-6` prompt profile は 6.2 にもそのまま当てる。adapter の内容（契約の完遂、可逆な作業は確認なしで進める、検証はリスクに比例）は 6.2 のガイドと矛盾しないため、runner は変更しない。

# Consequences

- 両 skill を Claude Code と Codex に配備し、`docs/skills-install-manifest.md` に追記する。
- reasoning effort の全段階と既定値、Codex の GPT-6.2 用 base instructions の内容は未確認で、skill の未確認事項に残した。
- GPT-6 / 6.1 を使わなくなったら、`gpt-6-tuning` の退役を検討する。
