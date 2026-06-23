---
title: "Runner And Skill Governance"
date: 2026-06-22
agent: "OpenAI Codex GPT-5.5"
---

# Runner And Skill Governance

This document is the dotfiles repository's source of truth for deciding when to add or change global Skills, runner Skills, and wrapper commands.

## Policy

New Skills and runners are not added for convenience alone.
They are added when they turn a repeated failure pattern or high-risk boundary into a normal, observable route.

Prefer the smallest mechanism that prevents the observed problem:

1. Repository docs or `AGENTS.md`
2. Thin wrapper guard
3. Adapter or option in an existing runner
4. New runner Skill
5. New general Skill

## Good Runner Candidates

Runner work is justified when one or more of these risks are recurring or likely to cause real damage:

- A CLI or MCP tool has dangerous defaults for auth, account, profile, project, company, `cwd`, or environment.
- Secret, OAuth, token, account principal, or company selection is involved.
- AI agents repeatedly choose a wrong command, env var, fallback path, profile, or recovery sequence.
- The command is long-running, talks to external services, retries, or can appear silently hung.
- The result must be replayable or auditable through `.context/` artifacts.
- Failure classification changes the next safe action.
- The workflow is reused across multiple repositories, agents, or sessions.

## Poor Runner Candidates

Do not add a runner when:

- The task is one-off.
- A README note or existing `AGENTS.md` rule is enough.
- A thin wrapper guard is enough.
- The CLI is simple, read-only, and low-risk.
- The main benefit is shorter typing.
- The tool has not yet produced a repeated failure pattern.

## Runner Classes

- Secret runner: protects secret material, stdout, and restore/write-back flow.
- Credential/account runner: protects principal, profile, project, company, credential path, and explicit fallback policy.
- Delegation runner: makes model handoff observable and replayable.
- External API runner: standardizes timeout, retry, rate-limit, and failure classification.

These classes can share a common pattern, but each adapter owns its tool-specific contract.

## Responsibility Boundaries

AGENTS files define the rule of conduct.
Docs define the governance rationale and decision criteria.
Runner Skills define the executable workflow.
Wrapper commands enforce final local preconditions before calling the underlying tool.

Global AI instruction files should stay thin.
Put detailed tool-specific or repository-specific governance in the working repository's docs or Skills.

## Required Design Notes

When adding a new runner or expanding an existing one, record why the lower-cost options were insufficient.
The note can live in the Skill, in this document if it changes policy, or in an ADR when the decision changes long-term architecture or operations.
