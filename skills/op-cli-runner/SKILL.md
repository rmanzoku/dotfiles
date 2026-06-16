---
name: op-cli-runner
description: Run 1Password CLI (`op`) and `opmaterialize` commands through one direct, observable subprocess path with bounded timeouts, redacted command metadata, and failure classification. Use when Codex needs to execute `op`, `opmaterialize`, `op signin`, restore 1Password-backed files, debug `account is not signed in`, `promptError`, `authorization prompt dismissed`, `authorization timeout`, or avoid silent hangs around 1Password CLI authentication without introducing alternate fallback execution paths.
---

# OP CLI Runner

Use this skill for the execution mechanics of 1Password CLI commands. Keep higher-level secret workflows in their owning skill, for example `$onepassword-secret-materialize` for `Secrets Manifest` and file restore policy.

## Core Rule

Run `op` through one direct wrapper path and let failures remain visible. Do not add Terminal, AppleScript, GUI, or shell-session fallback paths inside this skill; they obscure the real failure mode.

If `op whoami`, `op vault list`, or `opmaterialize diff` fails with `account is not signed in`, `promptError`, `authorization prompt dismissed`, `authorization timeout`, or a timeout, stop and report the classified failure from `summary.json`.

## Safety

- Do not print secret values.
- Do not run `op read`, `op item get --reveal`, or commands expected to write secret values to stdout. The wrapper rejects known stdout-secret forms before execution.
- Prefer commands that write secrets directly to files, such as `op document get --out-file ...`, or workflows like `opmaterialize` that avoid printing secret contents.
- Treat `op://...` references as sensitive operational material. The wrapper redacts them from metadata, but avoid passing them through command lines when a file or env-file handoff is available.
- Save logs under `.context/<task>/`, not `/tmp`. The wrapper rejects `--output-dir` outside the command `--cwd` repository's `.context/` directory.

## Wrapper

Use the bundled wrapper instead of raw `op` for non-trivial work:

```bash
python3 skills/op-cli-runner/scripts/run_op_cli.py \
  --output-dir .context/<task>/op \
  --cwd /path/to/repo \
  -- opmaterialize diff
```

The wrapper writes:

- `command.redacted.json`: command arguments with `op://...` references redacted
- `run.log`: timestamped runner log and redacted subprocess output
- `summary.json`: mode, cwd, command metadata, exit code, elapsed time, and failure classification

Relative `--output-dir` values are resolved under `--cwd`, so `--cwd /repo --output-dir .context/task/op` writes to `/repo/.context/task/op`.

## Direct Execution

Use the wrapper for direct execution:

```bash
python3 skills/op-cli-runner/scripts/run_op_cli.py \
  --output-dir .context/<task>/op-whoami \
  -- op whoami --account my.1password.com
```

If the wrapper returns `auth_required`, `prompt_error`, `authorization_dismissed`, `auth_timeout`, or `timeout`, do not retry the same command repeatedly. Preserve the artifacts and fix the underlying 1Password CLI/session/app-integration issue outside this skill.

When the command is `op signin`, the wrapper verifies success with `op whoami --account <account>`. Treat `op signin` exit 0 as insufficient unless `whoami` confirms the session.

## Restore Pattern

For 1Password-backed dotfiles:

1. Use `$onepassword-secret-materialize` for restore policy.
2. Use this skill's wrapper for execution:

   ```bash
   python3 skills/op-cli-runner/scripts/run_op_cli.py \
     --output-dir .context/<task>/op-diff \
     --cwd /Users/rmanzoku/.local/share/chezmoi \
     --timeout-seconds 900 \
     -- opmaterialize diff
   ```

3. If `diff` exits `1`, that means missing or changed files exist. Run restore:

   ```bash
   python3 skills/op-cli-runner/scripts/run_op_cli.py \
     --output-dir .context/<task>/op-restore \
     --cwd /Users/rmanzoku/.local/share/chezmoi \
     --timeout-seconds 900 \
     -- opmaterialize restore
   ```

4. If restore reports target conflicts, do not force overwrite silently. Ask for explicit confirmation before `opmaterialize restore --force`.
5. After restore, run `chezmoi apply` and drift checks through the owning dotfile workflow.

## Wrapper Availability

Treat a missing `opmaterialize` wrapper separately from 1Password authentication failures. If `opmaterialize` is not found or exits 127 before contacting 1Password, use the bundled script path from the installed skill:

```bash
OP_ACCOUNT=my.1password.com \
OP_DOTFILES_MATERIALIZE_VAULT="Dotfiles Secrets" \
sh ~/.codex/skills/onepassword-secret-materialize/scripts/opmaterialize diff
```

Use this only for wrapper availability. Do not use it as an authentication fallback.

## Failure Handling

Classify failures from `summary.json.failure_kind`:

- `auth_required`: CLI is not signed in for the selected account.
- `prompt_error`: 1Password app integration prompt could not be displayed or completed from the current process.
- `authorization_dismissed`: the auth prompt was dismissed or not completed.
- `auth_timeout`: the auth prompt did not complete before 1Password CLI timed out.
- `signin_unverified`: `op signin` exited without error, but `op whoami` did not confirm a usable session.
- `timeout`: command exceeded the wrapper timeout.
- `rejected_secret_stdout`: command was not executed because it is known to print secret values to stdout.
- `command_failed`: command exited non-zero without a known auth signature.
- exit 127 from `opmaterialize`: wrapper missing or not on `PATH`; check wrapper availability before auth troubleshooting.

For recurring `prompt_error`, `auth_timeout`, or silent waits, do not add another fallback inside this skill. Report the failure and update the environment, 1Password app integration, or caller workflow so the direct command can succeed or fail deterministically.

## Validation

After changing this skill, run:

```bash
python3 skills/op-cli-runner/scripts/run_op_cli.py --help
python3 -m py_compile skills/op-cli-runner/scripts/run_op_cli.py
scripts/skill-quick-validate skills/op-cli-runner
```
