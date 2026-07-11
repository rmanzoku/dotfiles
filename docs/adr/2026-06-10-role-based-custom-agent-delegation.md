---
title: "Role-Based Custom Agent Delegation"
date: 2026-06-10
agent_model: "GPT-5 Codex"
status: "superseded"
updated_at: 2026-07-08
updated_by_agent_model: "OpenAI Codex GPT-5"
---

# Role-Based Custom Agent Delegation

> Superseded on 2026-07-08. このリポジトリの `AGENTS.md` では、role-based custom agent への委譲を必須または推奨する運用ルールとして持たない。private agent 定義や過去の設計判断は残せるが、repo 作業時の委譲義務としては扱わない。

## Context

これまでは複数モデルの使い分けを中心に、調査、レビュー、検証を分散する運用が多かった。
今後はモデル差分そのものではなく、作業の性質に応じて `tech`、`biz`、`personal` などの custom agent を積極的に呼び出したい。

## Decision

複数モデルの使い分け自体を目的にせず、役割が明確な作業は role-appropriate なサブエージェント、custom agent、または runner へ委譲する。
親 Agent は委譲前に目的、背景、対象範囲、制約、許可する副作用、期待成果物、検証方法を明示し、最終判断、統合、ユーザーへの報告責任を保持する。

Codex では、特に以下の使い分けを標準とする。

- `tech`: 設計レビュー、実装方針の検証、コードレビュー、アーキテクチャ判断、不可逆リスクや長期保守性の評価
- `biz`: 事業前提、顧客価値、収益性、運用設計、市場・競合観点、意思決定のトレードオフ整理
- `personal`: 予定調整、タスク整理、連絡文案、調査メモ整理、日程・優先度・実務段取りの整理

互換 alias として残していた長い agent 名（`senior-engineer` / `biz-consultant` / `private-secretary`）は 2026-06-12 に削除し、短名のみを正式名とする。
alias 併存は同一 description の agent が一覧に重複して並び、呼び出し側の選択が恣意的になるうえ、定義の手動同期コストが残るため廃止した。

`personal` には secret 実値、認証情報、secret reference 自体とその解決結果を扱わせない。
また、個人予定や連絡文脈は raw data ではなく必要最小限の要約として渡す。

## Consequences

役割に合う視点を早めに取り入れやすくなる一方、軽微な単発作業で過剰に委譲すると遅延や文脈伝達コストが増える。
そのため、委譲は「役割として切り出せるか」と「親 Agent が検収できる成果物を返せるか」を条件にする。

alias 削除に伴い、過去に長名 agent を配備したマシンでは `~/.claude/agents/` と `~/.codex/agents/` の長名ファイルを 1 回だけ手動除去する必要がある（chezmoi は source が消えた target を自動では削除しない）。
1Password `Secrets Manifest` 内の長名 6 ファイルの登録行も削除対象とする。
