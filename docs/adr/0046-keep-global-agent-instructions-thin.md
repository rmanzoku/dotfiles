---
title: "Keep Global Agent Instructions Thin"
date: 2026-06-22
agent: "OpenAI Codex GPT-5.5"
---

# ADR 0046: Keep Global Agent Instructions Thin

## Context

This repository manages both repository-local governance and globally deployed AI instruction files.
Runner and Skill governance can become detailed because runners encode repeated failure patterns, credential boundaries, long-running execution, and observability.

Putting all of that detail into global instruction files would make every repository carry dotfiles-specific policy weight.

## Decision

Keep globally deployed instruction files thin.

- Global files state only that repository-local docs and Skills should be preferred when they exist.
- Global files ask agents to check existing docs, Skills, wrappers, and runner adapters before adding persistent Skills, runners, or wrappers.
- Detailed runner and Skill creation governance lives in `docs/runner-skill-governance.md` and the repository-local `AGENTS.md`.
- New long-term runner governance changes use docs or ADRs rather than expanding global instruction files.

## Consequences

Global instructions stay portable across repositories.
The dotfiles repository still has enough local policy to govern global Skill and runner maintenance.

Agents must follow repository-local docs when a working repository provides more specific runner or Skill rules.
