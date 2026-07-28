---
title: "Materialize GWS Profiles and Classify Runner Failures"
date: 2026-07-28
agent: "Claude Fable 5 (initial draft), Claude Opus 5 (verification, login flow, 1Password runner findings)"
---

# ADR 0059: Materialize GWS Profiles and Classify Runner Failures

This ADR covers both CLI runners that a scan of this machine's AI execution logs
flagged as unstable: the Google Workspace runner and the 1Password runner. For
the Google Workspace side it complements ADR 0045 without changing the
multi-account profile model or the fallback policy defined there. Profile
identity records live in the private fact store of ADR 0039.

## Context

A full scan of this machine's AI execution logs (Claude and Codex sessions,
2026-03-23 to 2026-07-28) classified 170 `gws` executions:

- 140 succeeded (82.4%).
- 8 failed with token expiry (`invalid_grant: invalid_rapt`), clustered on
  three separate days over a three-week span.
- 6 failed with missing credentials (exit 66 or "No credentials found").
- 5 failed with HTTP 400 `validationError` caused by guessed flags and
  subcommands that do not exist in the CLI.
- 3 failed with HTTP 403 `insufficientPermissions` because the profile's
  granted scopes did not cover the called API.
- The rest were missing-command/PATH issues and one token cache decryption
  failure.

Only 22% of executions went through the `gws-account` wrapper; the rest used
raw `gws`, often with ambient environment overrides. The root cause of the
bypass was that the local profile directories under `~/.config/gws/accounts/`
were effectively empty, so the wrapper always failed with exit 66 or 401 and
agents routed around it.

The wrapper also created the profile config directory unconditionally after
the credential check, so a mistyped profile name left an empty directory
behind that later looked like a real profile.

## Decision

- Materialize real credentials into the local profile directories (local
  state, outside git) so that `gws-account <profile> ...` is the working
  execution path, not a path agents must bypass.
- Keep raw `gws` plus ambient overrides (`GOOGLE_WORKSPACE_CLI_TOKEN`,
  ambient `GOOGLE_WORKSPACE_CLI_CREDENTIALS_FILE`,
  `GOOGLE_WORKSPACE_CLI_CONFIG_DIR`) forbidden as a bypass, per ADR 0045.
- Treat periodic token expiry (`invalid_rapt`) as a known operational event.
  Recovery is `gws-account <profile> auth login` for the same profile only.
- Treat HTTP 403 `insufficientPermissions` as a scope issue. Recovery is
  re-authenticating the same profile with additional scopes, never switching
  to another principal.
- Require confirming the command surface with `gws schema` or `--help` before
  running unfamiliar commands, instead of guessing flags and subcommands.
- The wrapper creates the profile config directory only when credentials
  already exist for the profile or the command is `auth login` / `auth setup`,
  so unknown profile names no longer leave empty directory residue. This does
  not cover residue `gws` itself writes: it creates an API schema `cache/`
  directory under whatever config dir it is given, so profile existence is
  judged by `credentials.enc` / `credentials.json`, not by the directory.

- Record the org-to-profile mapping, and each profile's account and granted
  scopes, in the private fact store owned by the Personal agent (ADR 0039), so
  profile selection is a lookup rather than a question asked every time. The
  fact store answers in three shapes — recorded, candidate, unknown — and only
  a recorded mapping may be used without user confirmation. Derived candidates
  stay unconfirmed, which keeps the no-guessing rule intact for the failure it
  guards against: executing as the wrong Google principal.

Concrete account identifiers, profile names, project ids, credential paths,
and 1Password references stay out of git, per ADR 0045. The fact store is
git-ignored and 1Password-backed, so it is a valid home for them.

## Considered: Password-Manager Autofill for Login

Agentic autofill through the browser-integrated password manager was evaluated
for the `auth login` step across two live runs — one profile whose account the
browser already held a session for, and one it did not.

- The browser extension must be on the released channel. On a pre-release
  channel the credential request fails with a transport error. Switching to the
  released build made the request return an approved grant, and also made the
  fill-side tooling appear, which had looked absent until then. Both halves of
  the integration hinge on that one setting.
- Where the browser already holds a session for the account, no password field
  appears at all; the flow is account selection plus consent. The integration
  adds nothing to that case.
- It cannot cover the step that actually needs a human: approving the consent
  screen. Granting OAuth scopes stays a user action.
- Whether it materially helps a login into an account the browser has no
  session for is untested. The one such run here was finished by the user
  entering the password manually, because the fill-side tooling only became
  available after that run had completed.

Not written into the documented flow yet. Test it on the next login into an
account with no existing browser session before adding it to the procedure.

## 1Password Runner: Authorization Cost and Two Misclassifications

The same log scan flagged the 1Password runner as unstable. Measurement showed
the instability was mostly in how results were classified, plus one real
ergonomic problem.

Authorization is not per file and not per process. One `opmaterialize diff`
spanning 21 separate `op` processes over 61 seconds required a single approval;
three consecutive calls required one. What multiplies prompts is elapsed time
between calls: scattering `op` work across a long session lets the password
manager lock in between, and each prompt that appears while the user is away
from the keyboard expires into a failure. The fix is to batch `op` work into one
contiguous stretch, announce the prompt before starting, and size timeouts for
an absent human rather than for the command's runtime. This was demonstrated
during the work itself: an unannounced `op` call, issued after twenty minutes of
unrelated work, timed out waiting for an approval nobody was watching.

Two classifications were wrong and are corrected in the runner:

- `opmaterialize diff` exits `1` when it finds differences, following the
  `diff(1)` convention. The runner reported this as `command_failed`. It is now
  `differences_found`, which is a result rather than a failure.
- A command can report "account is not signed in" while the session is in fact
  usable, seen immediately after `op signin` where the state takes a moment to
  propagate. The runner now probes with a read-only `op whoami` before
  concluding, and reports `auth_transient` when the session works. It does not
  re-run the original command, since re-running a write would not be safe.

## Browser Automation Caveat

When driving the consent flow through browser automation, a native browser
dialog — a passkey prompt is the common case — blocks the page while the
automation tools still report success. Typed text does not land and clicks do
not register, which is easy to misread as anti-automation defenses. Check a
full screenshot before concluding the site is blocking automation. Setting a
field value through the form-input path works where synthetic key events do
not.

## Consequences

The wrapper becomes the observed-working default path, so bypass pressure
drops. Token expiry every few weeks remains and is handled as routine
same-profile relogin rather than an incident. Scope-limited profiles will
still return 403 on out-of-scope APIs by design.
