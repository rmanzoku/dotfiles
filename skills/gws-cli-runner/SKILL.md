---
name: gws-cli-runner
description: Run Google Workspace CLI (`gws`) through the repository-managed account-scoped wrapper. Use when Claude Code or Codex needs to execute, configure, debug, or propose `gws` commands, especially where OAuth profile selection, credential paths, Personal-owned account mapping, `.env` account cache, 1Password restore, fallback policy, or avoidance of wrong Google principals matters.
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
2. If no profile is available, ask Personal before asking the user. Personal owns the mapping from repository org or directory to profile, and each profile's account and granted scopes. Require an answer in one of three shapes, and treat them differently:
   - **recorded** — a stored mapping. This is a lookup, not a guess; use it directly.
   - **candidate** — derived rather than recorded. Personal must return the basis alongside it and mark it unconfirmed. Confirm with the user before running any command against it.
   - **unknown** — ask the user.

   Never promote a candidate to the selected profile without user confirmation. Running against the wrong Google principal is the failure this Skill exists to prevent, and a plausible-looking directory match is not evidence.
3. If a working repository defines how to load `.env`, use that repository's rule. Do not invent a new `.env` contract from this Skill; if no rule is available, ask the user.
4. Ask Personal only for the non-secret profile/path decision. Do not pass secret values, secret references, tokens, or authenticated session data to Personal. If a Personal agent/tool is unavailable, ask the user instead of simulating Personal.
5. Before running an unfamiliar command, confirm the command surface with `gws schema <service.resource.method>` or `gws <service> <resource> --help`. Do not guess flags or subcommands; observed 400 `validationError` failures came from invented arguments and subcommands such as `--spreadsheet-id`, `sheets values get`, and `drive ls`.
6. Run `gws-account <profile> <gws args...>`.
7. If credentials are missing or expired, recover only within the same profile using the Login Flow below.
8. Record any persistent workflow change in the working repository docs or the relevant Skill, not in ad hoc memory.

## Login Flow

`auth login` requests the scope set you name; it does not merge with whatever the profile held before. The profile's `token_cache.json` is encrypted, so the previous scopes cannot be read back once the token is invalid. Decide the scope set from the profile's intended use and name every service the profile still needs, or a service that worked yesterday starts returning `403`.

1. Confirm the OAuth client exists first. Without `client_secret.json` in the profile config dir, `auth login` fails with `401 No OAuth client configured`. `auth login` never creates one — obtain it from the Google Cloud Console, or run `gws auth setup` where `gcloud` is available.
2. Decide the scope set. Ask Personal for the profile's recorded scopes first — the encrypted token cache cannot be read back, so the record is the only way to recover the previous set without asking the user. Use `gws schema <service.resource.method>` to check what an API needs before committing to a narrower set, and have Personal record the resulting scopes afterwards.
3. Start the login for the same profile in the background and capture its output. `auth login` blocks on a local `127.0.0.1` callback server until the browser flow finishes, so a foreground run looks like a hang:

   ```bash
   gws-account <profile> auth login --services drive,gmail > .context/<task>/auth-login.log 2>&1
   ```

   `--services` grants each named service's read-write scope, not a read-only one: `calendar` becomes full calendar access including deletion, and `gmail` becomes `gmail.modify`. Name only the services the profile needs, and use `--scopes` with comma-separated scope URLs when a narrower scope such as `calendar.readonly` is enough. Avoid `--full`; it pulls in pubsub and cloud-platform.
4. Read the authorization URL from that log and open it in the browser the user intends to authenticate with. Selecting the account is safe to do on the user's behalf; entering the password and approving the consent screen are not — hand those to the user. If the browser already holds a session for the account, no password is entered at all and the flow is account selection plus consent only.

   When driving this flow through browser automation, take a full screenshot before concluding that an action failed. A native browser dialog such as a passkey prompt blocks the page while the automation tools still report success, so typed text does not land and clicks do not register. Setting a field value through the form-input path works where synthetic key events do not.
5. Confirm the result before continuing. A completed browser flow is not proof of a usable session, and `auth status` alone does not prove the new scopes work:

   ```bash
   gws-account <profile> auth status
   ```

   Require `"token_valid": true` and the expected `user`, check `scope_count` / `scopes`, then call one real API the task depends on. A profile can report `token_valid: true` and still return `403 insufficientPermissions` for an API outside its granted scopes.

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
- Re-run OAuth login for the same selected profile, including after periodic token expiry (`invalid_rapt`) or to add missing scopes after a `403` `insufficientPermissions`.
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

- Exit `66`: credentials/config are missing for the selected profile. Judge whether a profile really exists by the presence of `credentials.enc` or `credentials.json`, not by the directory listing: `gws` writes an API schema `cache/` directory under any config dir it is pointed at, so a mistyped profile name can leave a directory that looks real but holds no credentials.
- Exit `78`: unsafe ambient credential override was present.
- Exit `127`: `gws` is not installed or not in `PATH`.
- `invalid_grant` / `invalid_rapt`: the token for the profile expired. This is a known recurring operational event, not a broken setup. Recover with `gws-account <profile> auth login` for the same profile; never switch to another account.
- HTTP `403` `insufficientPermissions`: the profile's granted scopes do not cover the API (for example a drive-only profile calling Gmail). This is expected behavior, not an account problem. Resolve by re-authenticating the same profile with the additional scopes; never resolve it by switching to another principal.
- HTTP `400` `validationError`: the command shape was likely guessed. Re-check with `gws schema` or `--help` before retrying.
- `rg` exit `1` during local checks means no matches, not a command failure.
