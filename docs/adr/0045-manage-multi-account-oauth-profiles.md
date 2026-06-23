---
title: "Manage Multi-Account OAuth Profiles"
date: 2026-06-22
agent: "OpenAI Codex GPT-5.5"
---

# ADR 0045: Manage Multi-Account OAuth Profiles

## Context

Google Workspace and Freee operations span multiple legal and business contexts.
Using default CLI or MCP OAuth state risks executing with the wrong principal.

Concrete account identifiers, local profile names, responsibility labels, and repository-local `.env` cache policy are account information.
They are owned outside this repository, for example by Personal or by the individual working repository.

## Decision

Use explicit account profile wrappers instead of default OAuth state.

- `gws-account <profile> ...` sets `GOOGLE_WORKSPACE_CLI_CONFIG_DIR` to `~/.config/gws/accounts/<profile>`.
- `freee-mcp-account <profile> <command>` sets `XDG_CONFIG_HOME` to `~/.config/freee-mcp/accounts/<profile>/xdg`.
- The repository does not define profile names or responsibility labels.
- The repository does not decide whether another repository stores account pointers in README, `.env`, or another local cache.
- Codex does not register profile-specific Freee MCP server names in managed config.
- OAuth files, token files, client secrets, refresh tokens, concrete account identifiers, concrete profile names, responsibility labels, and real 1Password references remain out of git.
- Profile files that must be reproducible are restored through the existing `opmaterialize` / `Secrets Manifest` workflow.
- For `gws`, portable restore uses `credentials.json` or `client_secret.json`; `credentials.enc` remains same-machine encrypted state unless its encryption contract is explicitly reviewed.
- Token refresh, relogin, and 1Password write-back are tool-specific credential lifecycle concerns and belong in the relevant runner or adapter.

## Fallback Policy

Fallback means only a recovery path that preserves the same principal, scope, profile, and Freee company.

Allowed:

- Re-authenticate the same local `gws-account` profile after missing or expired credentials.
- Re-run `freee-mcp-account <profile> configure` for the same local profile.
- Use the bundled `opmaterialize` script only when the deployed wrapper is missing.

Forbidden:

- Automatically switch to another Google account, Freee account, company, or profile.
- Let `GOOGLE_WORKSPACE_CLI_TOKEN` or `GOOGLE_WORKSPACE_CLI_CREDENTIALS_FILE` override the selected `gws` profile.
- Switch between CLI and MCP as a silent recovery path.
- Retry tool credential updates through multiple independent paths without a tool-specific lifecycle contract.

## Consequences

Account selection becomes visible in command lines and MCP server names.
Setup requires one OAuth/login flow per profile, but accidental cross-account execution is less likely.

Tool-specific credential automation remains deferred until each tool's token persistence and 1Password write-back contract can be verified end to end.
