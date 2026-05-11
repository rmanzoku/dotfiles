---
name: codex-cli-runner
description: Run Codex CLI subprocesses with observable JSONL event logs, timeouts, config-preserving model controls, prompt profiles, and artifact-based failure handling. Use when an orchestrating agent needs to invoke `codex exec`, call Codex from the CLI, CodexをCLIで呼ぶ, Codex CLIをサブプロセス実行する, or delegate long-running research, review, generation, or file work to Codex while distinguishing real hangs from silent execution.
---

# Codex CLI Runner

Use this skill when an orchestrating agent delegates work to Codex CLI through `codex exec`. Keep the source prompt, launch prompt, JSONL events, final message, stderr, summary, and failure notes under `.context/<task>/`.

Frame each delegation as an outcome-first contract: source prompt, expected artifacts, timeout, success criteria, allowed side effects, and failure handling. Let caller-provided model, effort, profile, and Codex config do model selection and permission policy.

## Core Rules

- Use `codex exec --json -o <last-message>` for observable non-interactive runs.
- Put every run under `.context/<task>/`.
- Save the real assignment as `.context/<task>/prompt.md`.
- Do not pass a large prompt body as an inline shell argument. Pass a short instruction that tells Codex to read `.context/<task>/run.prompt.md`.
- Use the wrapper's 600-second timeout default, or pass an explicit timeout override when the task needs a shorter or longer limit.
- Do not force `--sandbox`, `--ask-for-approval`, or bypass flags by default. Let Codex config/profile decide unless the caller explicitly requests an override via extra args.
- Do not treat 0-byte `run.events.jsonl` or `run.err` as a hang by itself.

## Claude Caller Checklist

Before running Codex, make these decisions explicitly:

- Task directory: choose `.context/<task>/`.
- Source prompt: write `.context/<task>/prompt.md` with the outcome, artifact paths, success criteria, allowed side effects, evidence rules, and stop condition.
- Working directory: pass `--cwd <project-root>` when the target repository matters.
- Expected artifacts: pass every required output with `--expected-artifact`; relative paths resolve from `--output-dir`, so use absolute paths for artifacts that must be written outside `.context/<task>/`.
- Defaults: omit `--model`, `--effort`, and `--profile` unless the caller, model registry, or role explicitly requires an override.
- Timeout: rely on the 600-second wrapper default unless the task contract says otherwise.
- Prompt profile: rely on `--prompt-profile auto` when passing an explicit GPT-5.5 model; use `--prompt-profile gpt-5-5` only when the CLI default is GPT-5.5 and `--model` is omitted.
- Extra Codex args: pass each Codex CLI token as its own `--extra-codex-arg=<token>` value, especially for leading-hyphen tokens.

Do not add "think hard", fixed progress-update scaffolds, or mandatory step-by-step narration to simulate effort. Use `--effort` only when the caller explicitly asks for an effort override.

## Standard Command Shape

Use this form, with `<prompt>` kept short and pointing to the generated launch prompt:

```bash
timeout 600 codex exec --json -o <artifact>.last-message.md "<prompt>" > <artifact>.events.jsonl 2> <artifact>.err
```

For repeatable runs, prefer the bundled wrapper:

```bash
python3 <skill-dir>/scripts/run_codex_cli.py \
  --prompt-file .context/<task>/prompt.md \
  --output-dir .context/<task> \
  --expected-artifact <expected-file>
```

Add `--model <model>`, `--effort <low|medium|high|xhigh>`, or `--profile <profile>` only when overriding Codex CLI defaults.
Add `--timeout-seconds <seconds>` only when overriding the 600-second default.

The wrapper writes:

- `run.prompt.md`: launch prompt sent to Codex, including any prompt profile adapter
- `run.events.jsonl`: Codex JSONL stdout events
- `run.err`: stderr
- `last-message.md`: final Codex message from `--output-last-message`
- `summary.json`: command, exit code, elapsed time, byte counts, parsed errors, prompt profile, `failure_reasons`, `recommended_next_action`, and `expected_artifacts`
- `failure.md`: only when the wrapper run fails

## Prompt Profiles

The wrapper writes `.context/<task>/run.prompt.md`, then passes only a file-reference prompt to `codex exec`.

Default behavior:

- `--prompt-profile auto` is the default.
- When `--model` explicitly looks like GPT-5.5 (`gpt-5.5`, `gpt-5-5`, or similar), `auto` applies the GPT-5.5 adapter to `run.prompt.md`.
- When `--model` is omitted, `auto` cannot know the Codex configured default. If the configured default is GPT-5.5, pass `--prompt-profile gpt-5-5` explicitly.
- Pass `--prompt-profile none` to suppress model-specific prompt adaptation.

The GPT-5.5 adapter is short and outcome-first. It tells Codex to honor the source prompt's outcome, success criteria, allowed side effects, evidence rules, output shape, and completion rule while relying on CLI/config effort rather than prompt magic words.

## Success Criteria

Require all applicable checks:

- Process exit code is `0`.
- `run.events.jsonl` exists and is non-empty.
- `last-message.md` exists and is non-empty.
- Every expected artifact exists and is non-empty.
- JSONL events do not contain obvious error records.
- `summary.json.success` is `true`, `summary.json.failure_reasons` is empty, and every item in `summary.json.expected_artifacts` has `exists=true` and `non_empty=true`.

## Failure Criteria

Treat any of these as failure:

- Timeout exit, normally exit code `124`.
- Non-zero process exit.
- stderr contains authentication, model, permission, quota, or rate-limit errors.
- JSONL events contain obvious error records.
- `last-message.md` is missing or empty.
- Expected artifacts are missing or empty.

On failure, inspect `.context/<task>/summary.json` first:

- `command`
- `exit_code`
- `elapsed_seconds`
- `events_bytes`, `stderr_bytes`, and `last_message_bytes`
- `failure_reasons`
- `last_error_event` or `last_event`
- `expected_artifacts`
- `recommended_next_action`

The wrapper also writes `.context/<task>/failure.md` with:

- executed command
- exit code
- elapsed time
- JSONL/stderr/final-message sizes
- last error or event
- expected artifact status
- recommended next action

## No-API Validation

Use these patterns when testing the wrapper itself without spending Codex API budget:

- For command-construction checks only, pass `--timeout-bin /usr/bin/true`. This bypasses Codex entirely and should fail wrapper success checks because no JSONL events, final message, or expected artifact are produced.
- For end-to-end wrapper success without API spend, create a small fake Codex executable under `.context/<task>/bin/` and pass it with `--codex-bin <path-to-fake-codex>`. The fake CLI must write JSONL stdout, honor `-o <last-message>`, and create the expected artifact.
- Keep fake CLIs under `.context/<task>/bin/` and use them only in validation. Do not use `--codex-bin` for real Codex delegation.
- Do not hand-edit `summary.json`, `run.events.jsonl`, `run.err`, `last-message.md`, or `failure.md`. If a controlled test needs explanation, write a separate `notes.md`.

## Wrapper Notes

- Resolve `<skill-dir>` from the location of this `SKILL.md`.
- Pass `--cwd <project-root>` when Codex should run from a specific repository.
- Omit `--model`, `--effort`, and `--profile` by default so Codex CLI uses its configured defaults.
- Pass `--model <model>` and `--effort <level>` from the caller when a model registry, role, or task explicitly requires overrides.
- Use `--prompt-profile gpt-5-5` when the caller knows the CLI default model is GPT-5.5 but does not pass `--model`.
- Pass each expected output as `--expected-artifact`; use an absolute path or a path relative to the wrapper output directory.
- Use `--extra-codex-arg` for narrow additions when explicitly required. Pass one Codex CLI token per wrapper argument, for example `--extra-codex-arg=--sandbox --extra-codex-arg=read-only`, `--extra-codex-arg=--ask-for-approval --extra-codex-arg=never`, or `--extra-codex-arg=--config --extra-codex-arg=key=value`.
- Keep final orchestration in Claude. This skill only runs Codex and records observable artifacts.

## Validation

Validate the skill and wrapper after changes:

```bash
scripts/skill-quick-validate skills/codex-cli-runner
python3 <skill-dir>/scripts/run_codex_cli.py --help
```

For runtime validation, run:

- no-API command construction
- no-API fake Codex success
- real short smoke prompt
- real file read/write prompt
- forced timeout failure
