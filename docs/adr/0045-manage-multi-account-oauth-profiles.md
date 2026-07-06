---
title: "Manage Multi-Account OAuth Profiles"
date: 2026-06-22
updated_at: 2026-06-28
agent: "OpenAI Codex GPT-5.5"
---

# ADR 0045: Manage Multi-Account OAuth Profiles

## Context

Google Workspace operations span multiple legal and business contexts.
Using default CLI OAuth state risks executing with the wrong principal.

Concrete account identifiers, local profile names, responsibility labels, and repository-local `.env` cache policy are account information.
They are owned outside this repository, for example by Personal or by the individual working repository.

Freee MCP was previously managed through local account-scoped wrapper state.
The current policy is to use Remote MCP for Freee and to stop managing local `freee-mcp` / `freee-sign-mcp` servers in this dotfiles repository.

## Decision

Use explicit account profile wrappers for Google Workspace instead of default OAuth state.
Use Remote MCP for Freee instead of repository-managed local MCP state.

- `gws-account <profile> ...` sets `GOOGLE_WORKSPACE_CLI_CONFIG_DIR` to `~/.config/gws/accounts/<profile>`.
- Freee MCP is Remote MCP-only for this repository, with Codex using `https://mcp.freee.co.jp/mcp`.
- The repository does not define profile names or responsibility labels.
- The repository does not decide whether another repository stores account pointers in README, `.env`, or another local cache.
- The repository does not deploy local `freee-mcp` / `freee-sign-mcp` wrappers or profile-specific Freee MCP server names in managed config.
- OAuth files, token files, client secrets, refresh tokens, concrete account identifiers, concrete profile names, responsibility labels, and real 1Password references remain out of git.
- Profile files that must be reproducible are restored through the existing `opmaterialize` / `Secrets Manifest` workflow.
- For `gws`, portable restore uses `credentials.json` or `client_secret.json`; `credentials.enc` remains same-machine encrypted state unless its encryption contract is explicitly reviewed.
- Token refresh, relogin, and 1Password write-back are tool-specific credential lifecycle concerns and belong in the relevant runner or adapter.

## Fallback Policy

Fallback means only a recovery path that preserves the same principal, scope, profile, and, for Freee, company.

Allowed:

- Re-authenticate the same local `gws-account` profile after missing or expired credentials.
- Use the bundled `opmaterialize` script only when the deployed wrapper is missing.

Forbidden:

- Automatically switch to another Google account, Freee account, company, or profile.
- Let `GOOGLE_WORKSPACE_CLI_TOKEN` or `GOOGLE_WORKSPACE_CLI_CREDENTIALS_FILE` override the selected `gws` profile.
- Start or configure local Freee MCP as a fallback for Remote MCP.
- Switch between CLI and MCP as a silent recovery path.
- Retry tool credential updates through multiple independent paths without a tool-specific lifecycle contract.

## Consequences

Google account selection becomes visible in command lines.
Setup requires one OAuth/login flow per Google profile, but accidental cross-account execution is less likely.

Tool-specific credential automation remains deferred until each tool's token persistence and 1Password write-back contract can be verified end to end.
