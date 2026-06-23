---
name: gws-cli-runner
description: Run Google Workspace CLI (`gws`) through the repository-managed account-scoped wrapper. Use when Codex needs to execute, configure, debug, or propose `gws` commands, especially where OAuth profile selection, credential paths, Personal-owned account mapping, `.env` account cache, 1Password restore, fallback policy, or avoidance of wrong Google principals matters.
---

# GWS CLI Runner

Use `gws-account <profile> ...` as the normal execution path for Google Workspace CLI work.
Do not call `gws` directly for account-scoped work unless the user explicitly asks for raw `gws` behavior or the task is only inspecting local help/version output.

## Responsibilities

This Skill owns the agent workflow around account-scoped `gws` use.
The wrapper owns final local enforcement.

This Skill exists because a thin wrapper can reject unsafe local execution, but it cannot make the agent choose the account source, consult repository-local cache rules, or recover through the same-profile restore/login path before execution.

- Preserve explicit profile selection.
- Avoid silent fallback to another Google principal.
- Respect caller-provided environment such as repository-local `.env`.
- Restore or relogin only for the same selected profile.
- Keep concrete account identifiers, profile names, responsibility labels, credential paths, and real 1Password references out of git-managed files.

## Workflow

1. Determine the intended local profile from the user's request, the working repository's docs, or environment already provided by the caller.
2. If no profile is available, ask the user instead of guessing.
3. If a working repository defines how to load `.env`, use that repository's rule. Do not invent a new `.env` contract from this Skill; if no rule is available, ask the user.
4. If Personal is the source of account mapping or credential location, ask Personal for the non-secret profile/path decision only. Do not pass secret values, secret references, tokens, or authenticated session data to Personal. If a Personal agent/tool is unavailable, ask the user instead of simulating Personal.
5. Run `gws-account <profile> <gws args...>`.
6. If credentials are missing or expired, recover only within the same profile:
   - Use the repository's existing 1Password materialization flow when it exists.
   - Otherwise run `gws-account <profile> auth login` when interactive login is appropriate.
7. Record any persistent workflow change in the working repository docs or the relevant Skill, not in ad hoc memory.

## Environment Contract

The wrapper uses these inputs when present:

- `GWS_ACCOUNT_CONFIG_DIR`: override the selected profile config directory.
- `GWS_ACCOUNT_CREDENTIALS_FILE`: explicitly provide a portable credentials file for the selected profile.

The wrapper refuses these unsafe ambient overrides:

- `GOOGLE_WORKSPACE_CLI_TOKEN`
- ambient `GOOGLE_WORKSPACE_CLI_CREDENTIALS_FILE` when `GWS_ACCOUNT_CREDENTIALS_FILE` was not explicitly set

## Fallback Policy

Allowed recovery paths:

- Restore credentials for the same selected profile.
- Re-run OAuth login for the same selected profile.
- Inspect `auth status`, `auth login`, `schema`, or help commands when credentials are not yet present.

Forbidden recovery paths:

- Switching to another Google account or local profile.
- Retrying with raw `gws` after `gws-account` rejects the environment.
- Treating another account's successful command as a fallback.
- Writing account names, profile names, credential paths, or secret references into git-managed docs unless the working repository explicitly owns that data.

## Command Patterns

Use file-backed prompts or `.context/` artifacts for complex handoffs and long command plans.
For simple commands, run the wrapper directly:

```bash
gws-account <profile> auth status
gws-account <profile> auth login
gws-account <profile> drive files list --params '{"pageSize": 5}'
```

When a command fails, classify the failure before continuing:

- Exit `66`: credentials/config are missing for the selected profile.
- Exit `78`: unsafe ambient credential override was present.
- Exit `127`: `gws` is not installed or not in `PATH`.
- `rg` exit `1` during local checks means no matches, not a command failure.
