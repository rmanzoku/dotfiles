# Tuning Patterns

Read this reference in `tune` or `extract-skill` mode, or in `audit` mode only when concrete recommended wording needs its examples. Use the existing `skill-creator` skill for extraction mechanics; do not create a separate extraction workflow here.

## Self-Elision and `self`

```text
Bad: If resolved provider/model matches current agent, always delegate to a same-provider subagent.
Good: If resolved provider/model matches current agent, skip external CLI subprocess construction. Decide between direct execution and a same-provider subagent from parallelism, context isolation, specialty coverage, required independence, owner boundary, and scope.
```

Use `self` for work the parent can complete within the owner and scope. Use aliases for delegated work and give each delegated role a bounded responsibility and reason.

When same-provider delegation is warranted, use the host's defined surface: Claude Code subagent / Agent tool, Codex `spawn_agent`, or Gemini's subagent mechanism when available (otherwise its explicit `agy-cli-runner` route). Define other providers' execution paths before relying on Self-Elision. These are execution paths, not model allocations.

## Resolver, runner, executor, and billing

Point skills to the resolver or registry path; do not make model names, effort, provider settings, timeout defaults, or wrapper commands authoritative in skill text. Execution-only roles should use lightweight defaults unless documented evaluation or risk justifies more. Keep provider-specific delegation as execution guidance, and use the runner mapping in `SKILL.md` when cross-provider delegation is warranted.

Within the requested scope, patch the canonical resolver or equivalent guidance first, then dependent skills/prompts, then any required ADR. Verify their consistency before completing the tune; do not change an already-correct resolver just to follow this order.

The resolver determines role/provider/model/config. The runner owns prompt-file handling, timeout, stream logs, expected artifact checks, summary, and failure reporting. Resolve model, executor, and billing source separately; the executor's runner, credit cap, and usage reporting apply even when it serves another vendor's model. Keep model-generation compensation in model adapters or runner prompt profiles.

## Review, tools, and recovery

Preserve coverage-first finding prompts, then rank, dedupe, or verify in a separate role or phase. Specify outcome- and evidence-based tool guidance instead of quotas. Pair fan-out or autonomous loops with verification capacity, stop conditions, and cleanup.

Require durable artifacts only when handoff, audit, identity, recovery, or user need calls for them. Long-running work must leave sufficient summaries, blocked-state reports, and canonical source references for recovery.

## Bypass remediation

Do not turn a temporary bypass into accepted workflow. When recurrence, skipped validation, setup drift, or reproducibility risk remains, record the cause, bypass and validation gap, permanent-fix candidates across repo-managed and machine-local state, owner boundary, and verification plan. A delegated reviewer may propose a remedy, but the parent verifies it against source-of-truth files before adoption.

## Delegated Prompt Contract

Include role, scope, delegation reason, working directory, prompt path when needed, expected artifacts only when needed, success and cleanup criteria, stop conditions, allowed side effects, evidence rules, recovery expectations, and any prohibition on synthesis, final-response editing, orchestration, or sibling-output access.
