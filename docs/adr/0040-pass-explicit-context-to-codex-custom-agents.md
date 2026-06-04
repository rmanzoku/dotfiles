---
title: "Pass Explicit Context To Codex Custom Agents"
date: 2026-06-03
agent_model: "GPT-5 Codex"
---

# ADR 0040: Pass Explicit Context To Codex Custom Agents

## Context

Codex custom agents can be defined under `~/.codex/agents/` and are spawned only when explicitly requested. The current Codex manual documents custom agent files and explicit subagent spawning, but does not document `fork_context` as a public custom-agent contract.

A review observed that the current Codex runtime cannot use `agent_type="senior_engineer"` together with `fork_context=true`. If the parent agent assumes implicit context inheritance, the senior-engineer agent may review without the repository rules, ADRs, business context, file paths, or prior decisions that make the judgment meaningful.

## Decision

Do not treat Codex custom agents as implicitly inheriting the full parent thread context.

When delegating to `senior_engineer`, the parent Codex agent must explicitly pass the context required for the review:

- request and expected output;
- repository path and relevant file paths;
- applicable `AGENTS.md` excerpts and local rules;
- relevant ADRs, docs, tests, logs, and runtime observations;
- business assumptions, scale, phase, and team context;
- irreversible risk areas and known constraints;
- evaluator or skill references such as `code-evaluator`, `docs-evaluator`, or `skill-manager`.

The `senior_engineer` custom agent must treat the parent prompt as its explicit context boundary, list missing inputs when the handoff is incomplete, and keep judgments conditional until it has inspected the relevant repository code, configuration, tests, docs, or external sources.

## Consequences

- Parent Codex prompts become slightly longer when using `senior_engineer`.
- Reviews are less likely to be based on stale memory or missing repository rules.
- The senior-engineer agent remains useful in Codex even when context forking is unavailable or unsupported.
- Final responsibility stays with the parent Codex agent, which must return to the actual repository evidence before acting on delegated judgments.
