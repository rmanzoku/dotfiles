---
title: "Separate Owner-Specific Dotfiles State"
date: 2026-06-23
agent_model: "OpenAI Codex GPT-5.5"
status: "accepted"
---

# ADR 0047: Separate Owner-Specific Dotfiles State

## Context

This repository is primarily used by its original maintainer as a live dotfiles source.
It is also increasingly used by others as an initial setup reference or as a model for AI-assisted operations.

Some useful parts are generic, while other parts depend on the original maintainer's private environment:

- workspace repository defaults;
- 1Password account / vault defaults;
- private role agents such as `tech`, `biz`, and `personal`;
- private secretary facts and assets;
- account profile mappings and credential paths.

If these layers are not documented, another user or AI agent can accidentally treat owner-specific state as a portable contract.

## Decision

Document the repository as a layered system:

- generic dotfiles and AI policy that can be reused;
- owner-specific defaults that must be overridden by adopters;
- private state that must remain outside git.

Add adopter-facing documentation in `docs/adopting-this-dotfiles.md` and link it from `README.md`.

Keep role agent names visible in public docs, but state that their definitions and facts are private and must be recreated by adopters.
Agents must not simulate unavailable private role agents from assumptions about the original maintainer.

Future changes must avoid hard-coding personal, company, project, machine, account, profile, credential path, or secret reference values into the generic git-managed layer.
When such values are needed, use environment variables, ignored private files, 1Password-backed restore, or working-repository-local ownership.

## Consequences

Adopters get a clearer path for reusing this repository without inheriting private assumptions.
The original maintainer can keep using the repository as a live environment source.

AI agents working in this repository have a documented rule for separating generic policy from owner-specific state.
Some setup commands remain owner-default examples, so adopters must still review and override them before running bootstrap steps.
