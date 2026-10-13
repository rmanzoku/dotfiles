---
title: "Keep owner-specific automation prompts machine-local"
created_at: 2026-10-14T02:05:29+09:00
agent_model: "GPT-6"
status: accepted
---

# Context

The uncommitted Issue Intake automation definition included owner-specific Google and GitHub principals, profiles, repositories, a Project identifier, and a grant of external mutation authority in its prompt. This public dotfiles repository separates account mappings and project policy from reusable configuration, as described in [the adoption guide](../adopting-this-dotfiles.md).

# Decision

- Manage the automation's identity, schedule, model, execution environment, and paused state through the existing chezmoi `modify_` merge script.
- Preserve its existing prompt and app-managed project target fields in the machine-local `~/.codex/automations/changer-issue-intake/automation.toml`. Do not import them into git.
- Remove the owner-specific prompt and its incremental collection policy from the shared source. Preserve the configured local prompt verbatim rather than rebuilding or weakening its account boundaries.
- Refuse to apply when the existing automation lacks a nonempty single-line prompt, matching the current Desktop-generated representation. No default prompt or account fallback is provided.

# Restoration and consequences

On a new machine, first create the automation in Codex with the intended repository and an owner-approved prompt containing the required account boundaries and mutation policy. Then apply the managed definition, review the local configuration, and activate it explicitly when appropriate. The shared definition sets `PAUSED`.

This intentionally leaves project policy restoration to the owner or the working repository. This dotfiles repository restores scheduling metadata; it does not recreate authorization or private account mappings. Runtime state remains ignored under the existing automation ignore rules.
