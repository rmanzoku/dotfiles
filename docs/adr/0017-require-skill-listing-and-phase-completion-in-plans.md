---
title: "ADR 0017: Plan 共通ルールに Skill 明示と Phase 完走原則を追加する"
status: accepted
date: 2026-04-06
worked_at: 2026-04-06 09:14 JST
agent_model: GPT-5 Codex
---

# ADR 0017: Plan 共通ルールに Skill 明示と Phase 完走原則を追加する

## Context

Plan モードでは、Phase を含む Plan が提示されても、各 Phase でどの Skill を使うかが明示されず、
実装時に Skill 選択が後ろ倒しになることがあった。

また、Phase を提示したあとに追加許可待ちを前提とした曖昧な止まり方が残り、
実装者がどこまで自走すべきかを毎回判断する余地があった。

一方で、このリポジトリでは `dotfile-update` のように `chezmoi apply` 前のユーザー確認を必須とする
既存 Skill / repo ルールがあるため、完走原則を無条件に優先すると既存契約と衝突する。

さらに、共通ルール同期は通常 4 ファイルを対象にするが、2026-04-06 のユーザー回答「3ファイル同期」により、
今回は `dot_qwen/QWEN.md` を一時的に同期対象から外す必要がある。

## Decision

- `# Plan 共通ルール` に「Phase を含む Plan では、各 Phase ごとに使用する Skill を明示し、使用しない Phase は `なし` と明記すること」を追加する。
- `# Plan 共通ルール` に「Phase を含む Plan は、途中確認を前提にせず完走できる粒度で提示し、Phase 提示後は不測の事態がない限り停止せず最後まで進めること」を追加する。
- ただし、`chezmoi apply` 前確認のように、既存 Skill / repo ルールで明示された事前確認は例外として維持する。
- 今回の同期対象は `dot_claude/CLAUDE.md`、`dot_codex/AGENTS.md`、`dot_gemini/GEMINI.md` の 3 ファイルに限定する。
- `dot_qwen/QWEN.md` の非反映は恒久方針ではなく、2026-04-06 のユーザー回答「3ファイル同期」に基づく一時例外として `.context` artifact とこの ADR に残す。

## Consequences

- Plan 提示時点で各 Phase の Skill 前提が明確になり、実装者が Skill 選択を後から判断しなくて済む。
- Phase 完走原則により、不要な許可待ち停止は減る。
- 既存 Skill / repo ルールの事前確認は維持されるため、`chezmoi apply` のような確認必須操作とは衝突しない。
- `dot_qwen/QWEN.md` は今回未更新のため、次回の共通ルール更新またはユーザーの明示指示時に再評価が必要になる。
