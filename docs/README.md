---
title: "Documentation Index"
updated_at: 2026-06-23
---

# Documentation Index

このディレクトリは、dotfiles repo の運用 docs と ADR の入口です。
現在の運用ルールは `README.md`、`AGENTS.md`、この `docs/` 配下の canonical docs、各 `SKILL.md` を優先し、ADR は背景・採用理由・履歴として扱います。

## Current Policy

| Topic | Canonical Source |
|---|---|
| Human setup and daily operation | [../README.md](../README.md) |
| Repository-local AI operating rules | [../AGENTS.md](../AGENTS.md) |
| Adopting / forking this dotfiles repository | [adopting-this-dotfiles.md](adopting-this-dotfiles.md) |
| Runner / Skill creation governance | [runner-skill-governance.md](runner-skill-governance.md) |
| Skill install manifest | [skills-install-manifest.md](skills-install-manifest.md) |
| Chezmoi source / target semantics | [../.claude/skills/chezmoi-knowledge/SKILL.md](../.claude/skills/chezmoi-knowledge/SKILL.md) |

## ADR History

ADRs under [adr/](adr/) record decisions and rationale.
They are historical evidence unless an active entrypoint links them as current procedure.

Frequently referenced ADRs:

| Topic | ADR |
|---|---|
| Role-based custom agents | [adr/2026-06-10-role-based-custom-agent-delegation.md](adr/2026-06-10-role-based-custom-agent-delegation.md) |
| Private agent restore from 1Password | [adr/0039-restore-private-agent-definitions-from-1password.md](adr/0039-restore-private-agent-definitions-from-1password.md) |
| Keep global agent instructions thin | [adr/0046-keep-global-agent-instructions-thin.md](adr/0046-keep-global-agent-instructions-thin.md) |
| Separate owner-specific dotfiles state | [adr/0047-separate-owner-specific-dotfiles-state.md](adr/0047-separate-owner-specific-dotfiles-state.md) |
| Multi-account OAuth profiles | [adr/0045-manage-multi-account-oauth-profiles.md](adr/0045-manage-multi-account-oauth-profiles.md) |
| Use direct OP CLI runner for 1Password auth | [adr/0044-use-op-cli-runner-for-1password-cli-auth.md](adr/0044-use-op-cli-runner-for-1password-cli-auth.md) |

## ADR Metadata Convention

For new or materially updated ADRs, use this front matter shape prospectively:

```yaml
---
title: "Short Decision Title"
date: YYYY-MM-DD
agent_model: "Agent / model name"
status: "accepted"
---
```

Optional fields:

- `updated_at`
- `updated_by_agent_model`
- `supersedes`
- `superseded_by`

Do not rewrite older ADRs solely to normalize metadata.
When an older ADR is materially edited, prefer moving it toward this convention as part of the same change.

## Skill Docs

First-party publisher skills live under [../skills/](../skills/).
Each skill's `SKILL.md` is the executable contract for that skill and can override general repository rules only for its specific workflow.
Install and restore commands are listed in [skills-install-manifest.md](skills-install-manifest.md).
