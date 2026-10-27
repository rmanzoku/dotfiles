---
title: "ADR 0081: dotfiles の編集担当を Codex に限定しない"
status: accepted
date: 2026-10-27
worked_at: 2026-10-27 JST
agent_model: "Claude Opus 5.5 (claude-opus-5-5)"
---

# Context

`AGENTS.md` は「このリポジトリの管理責任は Codex が持つ」としており、`dot_*` の編集は Codex が担う運用だった。2026-10-27、利用者から「Codex でのみ編集という制約はすでにない」と明示された。`CLAUDE.md` はすでに Claude Code の `dot_*` 編集を許可しており、記述が食い違っていた。

# Decision

- `AGENTS.md` の管理責任の行を、Codex と Claude Code のどちらが編集してもよいという記述へ置き換える。
- 編集手順の制約（`dotfile-update` / `skill-creator` / `skill-manager` の利用、pre-commit hook、ADR 運用）は AI を問わず同じものを適用する。

# Consequences

Claude Code セッションでも Codex への委譲なしに `dot_*`・`skills/`・docs を変更・commit できる。過去 ADR の `agent_model` にある「dot_* 編集担当」等の記述は当時の記録として残す。
