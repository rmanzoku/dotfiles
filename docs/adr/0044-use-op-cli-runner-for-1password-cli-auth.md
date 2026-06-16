---
title: "Use Direct OP CLI Runner For 1Password CLI Auth"
date: 2026-06-16
agent_model: "GPT-5 Codex"
status: accepted
---

# ADR 0044: Use Direct OP CLI Runner For 1Password CLI Auth

## Context

Codex subprocesses can fail to complete 1Password CLI app-integration prompts even when the user repeatedly approves Touch ID. Observed failure modes include `account is not signed in`, `promptError`, `authorization prompt dismissed`, `authorization timeout`, and silent waits while `opmaterialize` downloads manifest-backed documents.

Adding Terminal, AppleScript, GUI, or alternate-shell fallbacks makes the root cause harder to see because each path has different authentication and session behavior.

Local verification also separated wrapper availability from authentication:

- `opmaterialize add` is a one-file operation; multiple positional file paths are invalid before any 1Password call.
- Missing deployed `opmaterialize` wrapper exits 127 and should route to the bundled installed-skill script path.
- Missing wrapper is not an authentication failure and should not trigger auth troubleshooting.

The file-backed secret workflow still belongs to `onepassword-secret-materialize`, but raw execution of `op` from Codex's pseudo-TTY is not reliable enough as the default recovery path.

## Decision

Add a separate `op-cli-runner` skill for 1Password CLI execution mechanics.

Use it when running `op`, `opmaterialize`, or restore flows that may require app-integration authentication. The runner records redacted command metadata, bounded logs, summary JSON, and failure classification.

Keep the runner to one direct subprocess execution path. If the direct path reports authentication, prompt, authorization, or timeout failures, stop and report that classified failure instead of switching to a fallback.

Keep secret workflow policy and manifest semantics in `onepassword-secret-materialize`. Use `op-cli-runner` only as the execution layer.

Use `opmaterialize add` one file at a time. If the deployed wrapper is absent, invoke the installed skill's bundled script with explicit account and vault environment variables; keep that as a wrapper-availability recovery, not an auth workaround.

## Consequences

- Agents should stop repeatedly retrying raw `op` commands from Codex when app-integration prompts fail.
- 1Password-backed restores become observable through `.context/` artifacts.
- Failure causes remain easier to diagnose because there is only one execution path.
- Wrapper-not-found and unauthenticated-session failures remain separate operational categories.
- Commands that print secret values remain unsafe unless the caller explicitly provides a secret-safe output path and reporting plan.
