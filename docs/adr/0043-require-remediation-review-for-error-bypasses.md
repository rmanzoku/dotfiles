---
title: "Require Remediation Review For Error Bypasses"
date: 2026-06-07
agent: "Codex GPT-5"
updated_at: 2026-06-17T07:29:56+09:00
updated_by: "Codex GPT-5"
status: accepted
---

# Context

Agents often recover from command, tool, environment, permission, dependency, or validation errors by finding a temporary bypass and continuing the original task. That behavior is useful for progress, but it can hide recurring setup gaps, skipped validation, or workflow drift that should be fixed permanently.

AI-authored scripts and skills can turn this recovery habit into permanent fallback logic. In particular, external-connection workflows may silently switch from a failed CLI path to an API call, alternate wrapper, or parent-agent execution path. That can hide the primary failure, spend additional time and tokens on a path that should not be routine, and make idempotency or reproducibility harder to reason about.

The global agent instruction files also duplicated shared policy across Claude, Codex, Qwen, and Gemini. Claude Code does not directly read `AGENTS.md`, so the Claude global instruction file needed an import path if shared policy is centralized.

# Decision

- Treat temporary bypasses as acceptable only when they preserve enough validation to continue responsibly.
- Require an explicit remediation review when an error bypass may recur, skips validation, reveals missing setup/config/permissions/dependencies/docs/hooks/skills, or lowers reproducibility.
- Do not add implicit fallback paths to scripts, skills, runners, or external-connection workflows when they hide the primary path's failure cause. If an alternate path is necessary, document its purpose, trigger conditions, observability, idempotency, rerun behavior, validation impact, and whether remediation review is required.
- Promote a consistently more reliable alternate path to the primary path instead of keeping it as a fallback. Treat explicitly modeled redundant providers, such as equivalent RPC endpoints, mirrors, or replicas, as a separate design pattern when equivalence, selection rules, and failure reporting are clear.
- Allow subagents, reviewers, evaluators, or runners to investigate permanent fixes, while keeping final adoption with the parent agent after checking source-of-truth files.
- Make `~/.codex/AGENTS.md` the imported common global instruction source for Claude Code via `~/.claude/CLAUDE.md`.
- Extend `agent-orchestration-evaluator` so audits can detect silent error bypasses and missing remediation-review contracts.

# Consequences

- Agents get a clear path between "continue with a temporary workaround" and "stop to design a permanent fix".
- AI-generated operational scripts stay closer to one stable, observable, idempotent execution path instead of accumulating convenience fallbacks.
- Legitimate redundancy remains available for domains that intentionally use multiple equivalent providers, but must be represented as an explicit policy rather than an unexamined fallback.
- Claude Code avoids duplicating the common global rule block, reducing cross-agent drift.
- Claude Code imports Codex-specific text as part of `~/.codex/AGENTS.md`; `~/.claude/CLAUDE.md` therefore explicitly says the imported `# Codex 固有ルール` section is Codex-only.
- This is behavioral guidance, not hard enforcement. Hooks and validators may support artifact presence checks, but they should not try to infer whether a remediation review was semantically sufficient.
