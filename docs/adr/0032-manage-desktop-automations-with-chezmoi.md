---
title: "Manage Desktop Automations With Chezmoi"
date: 2026-05-13
agent: "Codex (GPT-5)"
status: accepted
---

# Context

Codex Desktop stores recurring automations under `~/.codex/automations/`. Some files in that tree are stable definitions, while others are runtime state. Claude Desktop / Claude Code also writes task-related files under `~/.claude/tasks`, but those files are UUID-scoped execution records with locks and high-water marks.

Persistent automation setup should be reproducible across machines, but applying transient execution state through chezmoi would risk copying stale locks, replay metadata, or machine-local scheduling noise.

# Decision

- Manage stable, secret-free Desktop automation definitions in this dotfiles repository through chezmoi.
- Treat Codex Desktop `~/.codex/automations/<automation-id>/automation.toml` as the canonical managed definition.
- Treat Codex Desktop `~/.codex/automations/<automation-id>/memory.md` as runtime operating context by default because it can change after each run.
- Ignore runtime state such as `.run-jitter-salt`, locks, high-water marks, logs, session history, and UUID-scoped task state.
- Keep Claude `~/.claude/tasks` unmanaged unless a future version exposes a stable declarative schedule file distinct from runtime execution records.

# Consequences

New automations can be restored with `chezmoi apply` when they are declarative and secret-free. Machine-local execution state and frequently updated operating notes remain local, reducing the chance of stale or invalid scheduler behavior after restore.
