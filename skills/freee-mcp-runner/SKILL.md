---
name: freee-mcp-runner
description: Run or configure Freee MCP servers through the repository-managed account-scoped wrapper. Use when Codex needs to start, configure, debug, or document `freee-mcp` / `freee-sign-mcp`, especially where OAuth profile selection, Freee company/account boundaries, Personal-owned account mapping, `.env` account cache, 1Password restore, token refresh, or avoidance of wrong Freee principals matters.
---

# Freee MCP Runner

Use `freee-mcp-account <profile> <command>` as the normal execution path for Freee MCP work.
Do not run `npx freee-mcp` or `npx freee-sign-mcp` directly for account-scoped work unless the user explicitly asks for raw upstream behavior or the task is only inspecting package help/version output.

## Responsibilities

This Skill owns the agent workflow around account-scoped Freee MCP use.
The wrapper owns final local enforcement.

This Skill exists because a thin wrapper can isolate local MCP config, but it cannot make the agent choose the account/company source, consult repository-local cache rules, or recover through the same-profile restore/configure path before execution.

- Preserve explicit profile selection.
- Avoid silent fallback to another Freee account, company, or local profile.
- Respect caller-provided environment such as repository-local `.env`.
- Restore, configure, or relogin only for the same selected profile.
- Keep concrete account identifiers, profile names, company labels, credential paths, token files, and real 1Password references out of git-managed files.

## Workflow

1. Determine the intended local profile from the user's request, the working repository's docs, or environment already provided by the caller.
2. If no profile is available, ask the user instead of guessing.
3. If a working repository defines how to load `.env`, use that repository's rule. Do not invent a new `.env` contract from this Skill; if no rule is available, ask the user.
4. If Personal is the source of account mapping or credential location, ask Personal for the non-secret profile/path decision only. Do not pass secret values, secret references, tokens, or authenticated session data to Personal. If a Personal agent/tool is unavailable, ask the user instead of simulating Personal.
5. Run one of the wrapper commands:
   - `freee-mcp-account <profile> configure`
   - `freee-mcp-account <profile> server`
   - `freee-mcp-account <profile> sign-configure`
   - `freee-mcp-account <profile> sign-server`
   - `freee-mcp-account <profile> path`
6. If credentials are missing or expired, recover only within the same profile:
   - Use the repository's existing 1Password materialization flow when it exists.
   - Otherwise run the matching `configure` command when interactive login is appropriate.
7. Record any persistent workflow change in the working repository docs or the relevant Skill, not in ad hoc memory.

## Environment Contract

The wrapper uses these inputs when present:

- `FREEE_MCP_ACCOUNT_XDG_CONFIG_HOME`: override the selected profile XDG config root.
- `FREEE_MCP_PACKAGE`: override the npm package spec; default is pinned by the wrapper.

The wrapper maps each profile to an isolated `XDG_CONFIG_HOME`, so upstream Freee MCP state files remain profile-scoped.

## Fallback Policy

Allowed recovery paths:

- Restore config/token files for the same selected profile.
- Re-run the matching configure command for the same selected profile.
- Use `freee-mcp-account <profile> path` to inspect where the profile-local config should live.

Forbidden recovery paths:

- Switching to another Freee account, company, or local profile.
- Retrying with raw `npx freee-mcp` or `npx freee-sign-mcp` after `freee-mcp-account` rejects or cannot find config.
- Treating another company or account's successful MCP startup as a fallback.
- Writing account names, profile names, company labels, credential paths, token files, or secret references into git-managed docs unless the working repository explicitly owns that data.

## Command Patterns

Use file-backed prompts or `.context/` artifacts for complex MCP setup notes.
For simple commands, run the wrapper directly:

```bash
freee-mcp-account <profile> path
freee-mcp-account <profile> configure
freee-mcp-account <profile> server
freee-mcp-account <profile> sign-configure
freee-mcp-account <profile> sign-server
```

When a command fails, classify the failure before continuing:

- Exit `66`: config is missing for the selected profile.
- Exit `127`: `npx` is not installed or not in `PATH`.
- Upstream OAuth/token refresh errors are tool-specific lifecycle issues; do not hide them behind an implicit fallback.
