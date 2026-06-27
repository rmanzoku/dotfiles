---
name: copilot-cli-runner
description: Run GitHub Copilot CLI subprocesses with observable JSONL logs, timeouts, config-preserving model, effort, agent, and permission controls, prompt profiles, and artifact-based failure handling. Use when Claude Code or Codex needs to invoke `copilot -p`, call Copilot from the CLI, CopilotをCLIで呼ぶ, Copilot CLIをサブプロセス実行する, or delegate long-running research, review, generation, or file work to Copilot while distinguishing real hangs from silent execution.
---

# Copilot CLI Runner

Use this skill when delegating work to GitHub Copilot CLI through non-interactive `copilot -p`. Keep the source prompt, launch prompt, JSONL output, stderr, summary, and failure notes under `.context/<task>/`.

Frame each delegation as an outcome-first contract: source prompt, expected artifacts, timeout, success criteria, allowed side effects, evidence rules, output shape, and failure handling. Let caller-provided model, effort, agent, permissions, and Copilot config/profile control model selection and tool policy.

## Core Rules

- Use `copilot -p <prompt> --output-format json` for observable non-interactive runs.
- Put every run under `.context/<task>/`.
- Save the real assignment as `.context/<task>/prompt.md`.
- Do not pass a large prompt body as an inline shell argument. Pass a short instruction that tells Copilot to read `.context/<task>/run.prompt.md`.
- Use the wrapper's 600-second timeout default, or pass an explicit timeout override when the task needs a shorter or longer limit.
- Do not force `--allow-all`, `--allow-all-tools`, `--allow-all-paths`, `--allow-all-urls`, `--yolo`, or permission grants by default. The caller owns gate enforcement; this runner preserves observability and lets Copilot config/profile decide unless the caller explicitly requests an override.
- Do not treat 0-byte `run.events.jsonl` or `run.err` as a hang by itself.

## Caller Checklist

Before running Copilot, make these decisions explicitly:

- Task directory: choose `.context/<task>/`.
- Source prompt: write `.context/<task>/prompt.md` with the outcome, artifact paths, success criteria, allowed side effects, evidence rules, and stop condition.
- Working directory: pass `--cwd <project-root>` when the target repository matters.
- Expected artifacts: pass every required output with `--expected-artifact`; relative paths resolve from `--output-dir`, so use absolute paths for artifacts that must be written outside `.context/<task>/`.
- When `--output-dir .context/<task>` is used, pass `--expected-artifact result.md`, not `--expected-artifact .context/<task>/result.md`; the latter resolves under `.context/<task>/.context/<task>/`.
- Defaults: omit `--model`, `--effort`, and `--agent` unless the caller, model registry, role, or task explicitly requires an override.
- Permission overrides: add `--allow-tool`, `--allow-url`, `--add-dir`, or broader flags only when explicitly supplied by the caller. Do not infer grants inside this runner.
- Timeout: rely on the 600-second wrapper default unless the task contract says otherwise.
- Prompt profile: use `--prompt-profile auto` by default; pass `--prompt-profile none` only when the source prompt already contains a complete Copilot-specific launch contract.
- Extra Copilot args: pass each Copilot CLI token as its own `--extra-copilot-arg=<token>` value, especially for leading-hyphen tokens.

Do not add "think hard", fixed progress-update scaffolds, or mandatory step-by-step narration to simulate reasoning. Use `--effort` only when the caller explicitly asks for an effort override.

## Standard Command Shape

Use this form, with `<prompt>` kept short and pointing to the generated launch prompt:

```bash
timeout 600 copilot -p "<prompt>" --output-format json > <artifact>.events.jsonl 2> <artifact>.err
```

For repeatable runs, prefer the bundled wrapper:

```bash
python3 <skill-dir>/scripts/run_copilot_cli.py \
  --prompt-file .context/<task>/prompt.md \
  --output-dir .context/<task> \
  --expected-artifact <expected-file>
```

Add `--model <model>`, `--effort <low|medium|high|xhigh>`, or `--agent <agent>` only when overriding Copilot CLI defaults.
Add `--timeout-seconds <seconds>` only when overriding the 600-second default.

The wrapper writes:

- `run.prompt.md`: launch prompt sent to Copilot, including any prompt profile adapter
- `run.events.jsonl`: Copilot JSONL stdout events
- `run.err`: stderr
- `summary.json`: command, exit code, elapsed time, byte counts, parsed errors, prompt profile, `failure_reasons`, `recommended_next_action`, and `expected_artifacts`
- `failure.md`: only when the wrapper run fails

## Prompt Profiles

The wrapper writes `.context/<task>/run.prompt.md`, then passes only a file-reference prompt to `copilot -p`.

Default behavior:

- `--prompt-profile auto` is the default and applies the Copilot adapter.
- `--prompt-profile copilot` forces the Copilot adapter.
- `--prompt-profile none` suppresses prompt adaptation.

The Copilot adapter is short and outcome-first. It tells Copilot to execute the source prompt literally, write requested artifacts exactly where specified, respect allowed side effects, keep output concise unless the source prompt asks otherwise, and stop when the source contract is complete or blocked.

## Success Criteria

Require all applicable checks:

- Process exit code is `0`.
- `run.events.jsonl` exists and is non-empty.
- Every expected artifact exists and is non-empty.
- Parsed JSONL records do not contain obvious error records.
- `summary.json.success` is `true`, `summary.json.failure_reasons` is empty, and every item in `summary.json.expected_artifacts` has `exists=true` and `non_empty=true`.

## Failure Criteria

Treat any of these as failure:

- Timeout exit, normally exit code `124`.
- Non-zero process exit.
- stderr contains authentication, login, model, permission, quota, policy, path, tool, URL, or rate-limit errors.
- Copilot exits because a required non-interactive tool, path, or URL permission was not granted.
- Parsed JSONL records contain obvious error records.
- `run.events.jsonl` is missing or empty.
- Expected artifacts are missing or empty.

On failure, inspect `.context/<task>/summary.json` first:

- `command`
- `exit_code`
- `elapsed_seconds`
- `events_bytes` and `stderr_bytes`
- `failure_reasons`
- `last_error_event` or `last_event`
- `expected_artifacts`
- `recommended_next_action`

The wrapper also writes `.context/<task>/failure.md` with:

- executed command
- exit code
- elapsed time
- events/stderr sizes
- last error or event
- expected artifact status
- recommended next action

## No-API Validation

Use these patterns when testing the wrapper itself without spending Copilot API budget:

- For command-construction checks only, pass `--timeout-bin /usr/bin/true`. This bypasses Copilot entirely and should fail wrapper success checks because no JSONL output or expected artifact is produced.
- For end-to-end wrapper success without API spend, create a small fake Copilot executable under `.context/<task>/bin/` and pass it with `--copilot-bin <path-to-fake-copilot>`. The fake CLI must write JSONL stdout and create the expected artifact.
- Keep fake CLIs under `.context/<task>/bin/` and use them only in validation. Do not use `--copilot-bin` for real Copilot delegation.
- Do not hand-edit `summary.json`, `run.events.jsonl`, `run.err`, or `failure.md`. If a controlled test needs explanation, write a separate `notes.md`.

## Wrapper Notes

- Resolve `<skill-dir>` from the location of this `SKILL.md`.
- Pass `--cwd <project-root>` when Copilot should run from a specific repository.
- Omit `--model`, `--effort`, and `--agent` by default so Copilot CLI uses its configured defaults.
- Pass `--model <model>`, `--effort <level>`, and `--agent <agent>` from the caller when a model registry, role, or task explicitly requires overrides.
- Pass each expected output as `--expected-artifact`; use an absolute path or a path relative to the wrapper output directory. If the artifact is directly inside `.context/<task>/`, pass only the filename.
- Use `--extra-copilot-arg` only to pass caller-supplied Copilot CLI overrides. Pass one Copilot CLI token per wrapper argument, for example `--extra-copilot-arg=--allow-tool --extra-copilot-arg=shell(git)`, `--extra-copilot-arg=--add-dir --extra-copilot-arg=/path/to/dir`, or `--extra-copilot-arg=--allow-url --extra-copilot-arg=github.com`.
- Keep final orchestration in the caller. This skill only runs Copilot and records observable artifacts.

## Validation

Validate the skill and wrapper after changes:

```bash
scripts/skill-quick-validate skills/copilot-cli-runner
python3 <skill-dir>/scripts/run_copilot_cli.py --help
```

For runtime validation, run:

- no-API command construction
- no-API fake Copilot success
- optional real short smoke prompt when auth/cost is acceptable
- forced timeout failure
