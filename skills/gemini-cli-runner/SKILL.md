---
name: gemini-cli-runner
description: Run Gemini CLI subprocesses with observable stream-json logs, timeouts, config-preserving model and approval controls, prompt profiles, and artifact-based failure handling. Use when Claude Code or Codex needs to invoke `gemini -p`, call Gemini from the CLI, GeminiをCLIで呼ぶ, Gemini CLIをサブプロセス実行する, or delegate long-running research, review, generation, or file work to Gemini while distinguishing real hangs from silent execution.
---

# Gemini CLI Runner

Use this skill when delegating work to Gemini CLI through non-interactive `gemini -p`. Keep the source prompt, launch prompt, stream-json output, stderr, summary, and failure notes under `.context/<task>/`.

Frame each delegation as an outcome-first contract: source prompt, expected artifacts, timeout, success criteria, allowed side effects, evidence rules, output shape, and failure handling. Let caller-provided model, approval mode, Gemini config/profile, and explicit extra args control model selection and permission policy.

## Core Rules

- Use `gemini -p <prompt> --output-format stream-json` for observable non-interactive runs.
- Put every run under `.context/<task>/`.
- Save the real assignment as `.context/<task>/prompt.md`.
- Do not pass a large prompt body as an inline shell argument. The wrapper embeds the source prompt inside `.context/<task>/run.prompt.md`, starts Gemini from that output directory, and passes only a short instruction to read `./run.prompt.md`.
- Use the wrapper's 600-second timeout default, or pass an explicit timeout override when the task needs a shorter or longer limit.
- Do not force `--sandbox`, `--yolo`, `--approval-mode`, trust, policy, or tool flags by default. The caller owns gate enforcement; this runner preserves observability and lets Gemini config/profile decide unless the caller explicitly requests an override.
- Do not treat 0-byte `run.stream.jsonl` or `run.err` as a hang by itself.

## Caller Checklist

Before running Gemini, make these decisions explicitly:

- Task directory: choose `.context/<task>/`.
- Source prompt: write `.context/<task>/prompt.md` with the outcome, artifact paths, success criteria, allowed side effects, evidence rules, and stop condition. If an expected artifact path is absolute, put that same absolute path in the source prompt; `--expected-artifact` only verifies materialization.
- Working directory: pass `--cwd <project-root>` when the target repository matters. The wrapper records this as `target_cwd`, starts the Gemini process from the run output directory so hidden `.context` artifacts are readable by relative path, and includes the target directory with `--include-directories` unless the caller already supplied that flag.
- Expected artifacts: pass every required output with `--expected-artifact`; relative paths resolve from `--output-dir`, so use absolute paths for artifacts that must be written outside `.context/<task>/`.
- When `--output-dir .context/<task>` is used, pass `--expected-artifact result.md`, not `--expected-artifact .context/<task>/result.md`; the latter resolves under `.context/<task>/.context/<task>/`.
- Defaults: omit `--model` and `--approval-mode` unless the caller, model registry, role, or task explicitly requires an override.
- Timeout: rely on the 600-second wrapper default unless the task contract says otherwise.
- Prompt profile: use `--prompt-profile auto` by default; pass `--prompt-profile none` only when the source prompt already contains a complete Gemini-specific launch contract.
- Extra Gemini args: pass each Gemini CLI token as its own `--extra-gemini-arg=<token>` value, especially for leading-hyphen tokens.

Do not add "think hard", fixed progress-update scaffolds, or mandatory step-by-step narration to simulate model effort. If the Gemini CLI later exposes an effort or thinking control, pass it as an explicit CLI/config override rather than prompt magic words.

## Standard Command Shape

Use this form, with `<prompt>` kept short and pointing to the generated launch prompt:

```bash
timeout 600 gemini -p "<prompt>" --output-format stream-json > <artifact>.stream.jsonl 2> <artifact>.err
```

For repeatable runs, prefer the bundled wrapper:

```bash
python3 <skill-dir>/scripts/run_gemini_cli.py \
  --prompt-file .context/<task>/prompt.md \
  --output-dir .context/<task> \
  --expected-artifact <expected-file>
```

Add `--model <model>` or `--approval-mode <default|auto_edit|yolo|plan>` only when overriding Gemini CLI defaults.
Add `--timeout-seconds <seconds>` only when overriding the 600-second default.

The wrapper writes:

- `run.prompt.md`: launch prompt sent to Gemini, including any prompt profile adapter
- `run.stream.jsonl`: Gemini stream-json stdout
- `run.err`: stderr
- `summary.json`: command, `target_cwd`, `process_cwd`, exit code, elapsed time, byte counts, parsed errors, prompt profile, `final_stream_success`, `failure_reasons`, `nonfatal_reasons`, `recommended_next_action`, and `expected_artifacts`
- `failure.md`: only when the wrapper run fails

## Prompt Profiles

The wrapper writes `.context/<task>/run.prompt.md`, embeds the complete source prompt in that launch file, then starts Gemini from the run output directory and passes only a relative file-reference prompt to `gemini -p`.

This cwd relocation is intentional: Gemini may reject absolute paths under hidden directories such as `.context` as ignored files, while it can read `./run.prompt.md` when the process cwd is the run directory.

Default behavior:

- `--prompt-profile auto` is the default and applies the Gemini adapter.
- `--prompt-profile gemini` forces the Gemini adapter.
- `--prompt-profile none` suppresses prompt adaptation.

The Gemini adapter is short and outcome-first. It tells Gemini to execute the embedded source prompt literally, write requested artifacts exactly where specified, preserve absolute artifact paths, avoid side effects outside those artifacts unless explicitly allowed, use tools available under the caller's Gemini CLI config/profile when needed, keep output concise unless the source prompt asks otherwise, and stop when the source contract is complete or blocked.

## Success Criteria

Require all applicable checks:

- Process exit code is `0`.
- `run.stream.jsonl` exists and is non-empty.
- The last parsed stream-json record is a final success result: `type=result` and `status=success`.
- Every expected artifact exists and is non-empty.
- Parsed stream-json records contain no obvious error records, or only intermediate error records followed by a final success result with all expected artifacts materialized. Intermediate recovered errors are recorded in `summary.json.nonfatal_reasons`.
- `summary.json.success` is `true`, `summary.json.failure_reasons` is empty, and every item in `summary.json.expected_artifacts` has `exists=true` and `non_empty=true`.

These checks prove runner execution and non-empty artifact materialization only. The caller must still evaluate task-specific artifact quality against the source prompt.

## Failure Criteria

Treat any of these as failure:

- Timeout exit, normally exit code `124`.
- Non-zero process exit.
- `run.stream.jsonl` or `run.err` contains `setRawMode EIO` or `setRawMode EBADF`; treat this as `raw_mode_tty_error`, a noninteractive TTY failure, not as task output.
- stderr contains fatal authentication, model resolution, permission, quota, trust, policy, or rate-limit errors that do not recover into exit `0`, a final success result, and non-empty expected artifacts. Non-empty stderr and recovered CLI warnings alone are not failures when the process exits `0`, stream output is present, the final stream result is successful, and expected artifacts are non-empty.
- Parsed stream-json records contain obvious error records that do not recover into a final success result with non-empty expected artifacts.
- `run.stream.jsonl` is missing or empty.
- The final stream-json record is not a success result.
- Expected artifacts are missing or empty.

On failure, inspect `.context/<task>/summary.json` first:

- `command`
- `exit_code`
- `target_cwd` and `process_cwd`
- `elapsed_seconds`
- `stream_bytes` and `stderr_bytes`
- `failure_reasons`
- `nonfatal_reasons`
- `raw_mode_tty_error`
- `final_stream_success`
- `last_error_record` or `last_stream_record`
- `expected_artifacts`
- `recommended_next_action`

If a higher-level workflow needs a downstream blocked artifact, create it in the caller using that workflow's schema or template. Do not invent a downstream schema in this runner and do not modify runner evidence artifacts. If no caller schema was supplied, report the runner as blocked with links to `summary.json` and `failure.md` instead of fabricating an artifact format.

The wrapper also writes `.context/<task>/failure.md` with:

- executed command
- exit code
- elapsed time
- stream/stderr sizes
- last error or stream record
- expected artifact status
- recommended next action

## No-API Validation

Use these patterns when testing the wrapper itself without spending Gemini API budget:

- For command-construction checks only, pass `--timeout-bin /usr/bin/true`. This bypasses Gemini entirely and should fail wrapper success checks because no stream-json output or expected artifact is produced.
- For end-to-end wrapper success without API spend, create a small fake Gemini executable under `.context/<task>/bin/` and pass it with `--gemini-bin <path-to-fake-gemini>`. The fake CLI must write JSONL stdout and create the expected artifact.
- Minimal fake behavior: exit `0`, print one final success JSON object such as `{"type":"result","status":"success"}`, and write the requested expected artifact such as `result.md`.
- Fake Gemini executables run with `process_cwd=--output-dir`, so a relative expected artifact such as `--expected-artifact result.md` can be created by writing `result.md` in the fake script. For wrapper-only validation, the source `prompt.md` may be a minimal valid task contract such as "Write result.md."
- Use an absolute `--gemini-bin` path for fake CLIs unless you have verified the relative path resolves from the wrapper output directory; real Gemini runs execute with `process_cwd=--output-dir`.
- Keep fake CLIs under `.context/<task>/bin/` and use them only in validation. Do not use `--gemini-bin` for real Gemini delegation.
- Do not hand-edit `summary.json`, `run.stream.jsonl`, `run.err`, or `failure.md`. If a controlled test needs explanation, write a separate `notes.md`.

## Wrapper Notes

- Resolve `<skill-dir>` from the location of this `SKILL.md`.
- The wrapper passes `stdin=DEVNULL` to keep `gemini -p` on a noninteractive subprocess path.
- Pass `--cwd <project-root>` when Gemini should work against a specific repository. The wrapper uses that as `target_cwd` and runs the process from the output directory for reliable `.context` prompt access.
- Omit `--model` and `--approval-mode` by default so Gemini CLI uses its configured defaults.
- Pass `--model <model>` and `--approval-mode <mode>` from the caller when a model registry, role, or task explicitly requires overrides.
- Pass each expected output as `--expected-artifact`; use an absolute path or a path relative to the wrapper output directory. If the artifact is directly inside `.context/<task>/`, pass only the filename.
- Use `--extra-gemini-arg` for narrow additions when explicitly required. Pass one Gemini CLI token per wrapper argument, for example `--extra-gemini-arg=--sandbox`, `--extra-gemini-arg=--include-directories --extra-gemini-arg=/path/to/dir`, or `--extra-gemini-arg=--policy --extra-gemini-arg=/path/to/policy.md`. If you pass `--include-directories` yourself, include every directory Gemini should access because the wrapper will not add its default target directory include.
- Keep final orchestration in the caller. This skill only runs Gemini and records observable artifacts.

## Validation

Validate the skill and wrapper after changes:

```bash
scripts/skill-quick-validate skills/gemini-cli-runner
python3 <skill-dir>/scripts/run_gemini_cli.py --help
```

For runtime validation, run:

- no-API command construction
- no-API fake Gemini success
- optional real short smoke prompt when API/auth cost is acceptable
- forced timeout failure
