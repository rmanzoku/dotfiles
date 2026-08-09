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

## Caller Checklist

Before running Codex, make these decisions explicitly:

- Task directory: choose `.context/<task>/`.
- Source prompt: write `.context/<task>/prompt.md` with the outcome, artifact paths, success criteria, allowed side effects, evidence rules, and stop condition. If an expected artifact path is absolute, put that same absolute path in the source prompt; `--expected-artifact` only verifies materialization.
- Working directory: pass `--cwd <project-root>` when the target repository matters.
- Expected artifacts: pass every required output with `--expected-artifact`; relative paths resolve from `--output-dir`, so use absolute paths for artifacts that must be written outside `.context/<task>/`.
- When `--output-dir .context/<task>` is used, pass `--expected-artifact result.md`, not `--expected-artifact .context/<task>/result.md`; the latter resolves under `.context/<task>/.context/<task>/`.
- Defaults: omit `--model`, `--effort`, and `--profile` unless the caller, model registry, or role explicitly requires an override.
- Timeout: rely on the 600-second wrapper default unless the task contract says otherwise.
- Prompt profile: rely on `--prompt-profile auto` when passing an explicit GPT-5.5 or GPT-5.6 model; use `--prompt-profile gpt-5-5` or `--prompt-profile gpt-5-6` only when the CLI default is that generation and `--model` is omitted.
- Extra Codex args: pass each Codex CLI token as its own `--extra-codex-arg=<token>` value, especially for leading-hyphen tokens.
- Web search: `codex exec` does not accept `--search` (it exits 2 with `unexpected argument '--search'`). For research tasks that need web access, pass `--extra-codex-arg=--config --extra-codex-arg=tools.web_search=true`.

Do not add "think hard", fixed progress-update scaffolds, or mandatory step-by-step narration to simulate effort. Use `--effort` only when the caller explicitly asks for an effort override.

## Standard Command Shape

Use this form, with `<prompt>` kept short and pointing to the generated launch prompt:

```bash
timeout 600 codex exec --json -o <artifact>.last-message.md "<prompt>" > <artifact>.events.jsonl 2> <artifact>.err < /dev/null
```

Keep `< /dev/null` on raw `codex exec` commands: with an open non-TTY stdin (typical in background shells), `codex exec` blocks on `Reading additional input from stdin...` until timeout. The bundled wrapper already forces stdin from `/dev/null`.

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
- `summary.json`: command, resolved `cwd`, exit code, elapsed time, byte counts, parsed errors, prompt profile, `failure_reasons`, `nonfatal_reasons`, `recommended_next_action`, and `expected_artifacts`
- `failure.md`: only when the wrapper run fails

## Prompt Profiles

The wrapper writes `.context/<task>/run.prompt.md`, then passes only a file-reference prompt to `codex exec`.

Default behavior:

- `--prompt-profile auto` is the default.
- When `--model` explicitly looks like GPT-5.5 (`gpt-5.5`, `gpt-5-5`, or similar), `auto` applies the GPT-5.5 adapter to `run.prompt.md`.
- When `--model` explicitly looks like GPT-5.6 (`gpt-5.6`, `gpt-5-6`, `gpt-5.6-sol`, `gpt-5.6-terra`, `gpt-5.6-luna`, or similar), `auto` applies the GPT-5.6 adapter to `run.prompt.md`.
- When `--model` is omitted, `auto` cannot know the Codex configured default. If the configured default is GPT-5.5 or GPT-5.6, pass `--prompt-profile gpt-5-5` or `--prompt-profile gpt-5-6` explicitly.
- Pass `--prompt-profile none` to suppress model-specific prompt adaptation.

The GPT-5.5 adapter is short and outcome-first. It tells Codex to honor the source prompt's outcome, success criteria, allowed side effects, evidence rules, output shape, and completion rule while relying on CLI/config effort rather than prompt magic words.

The GPT-5.6 adapter is short, lean, and outcome-first. In addition to the GPT-5.5 contract it tells Codex to state each instruction once without boilerplate, handle routine local actions within the allowed side effects without asking, and treat external writes, destructive actions, and scope expansion as out of contract unless the source prompt explicitly authorizes them. Generation doctrine is maintained in the `gpt-5-6-tuning` skill.

## Default Response Format

Every launch prompt supplies a default AI-to-AI handoff shape when `prompt.md` does not explicitly require another format:

- `## Result`: outcome or direct answer.
- `## Evidence`: verified facts, sources, or reasoning.
- `## Changes`: files or actions changed; omit for no-change tasks.
- `## Blockers`: missing input, failure, or next action; omit when none.

Use only applicable sections, keep the response concise, and do not wrap the whole response in JSON or a Markdown code fence. An explicit source-prompt output format always overrides this default.

## Success Criteria

Require all applicable checks:

- Process exit code is `0`.
- `run.events.jsonl` exists and is non-empty.
- `last-message.md` exists and is non-empty.
- Every expected artifact exists and is non-empty.
- JSONL events do not contain obvious error records.
- `summary.json.success` is `true`, `summary.json.failure_reasons` is empty, and every item in `summary.json.expected_artifacts` has `exists=true` and `non_empty=true`.

These checks prove runner execution and non-empty artifact materialization only. The caller must still evaluate task-specific artifact quality against the source prompt.

## Image Generation Route

Codex exposes image generation as an **agent tool (`imggen`), not a CLI subcommand.** `codex imggen` is not a command; passing it only prints help. Request images through the normal prompt path.

### Contract

- **`--sandbox workspace-write`** is required. The agent writes the image file
- **`--cd <output-dir>`** sets where the run happens. Pair it with an absolute destination path in the prompt
- **`--skip-git-repo-check`** is required when the output directory is not inside a trusted git repository. Without it the run aborts with `Not inside a trusted directory`
- **The image is not `last-message.md`.** The final message only reports the path. Track the image as an expected artifact and verify it yourself

Run:

```bash
python3 <skill-dir>/scripts/run_codex_cli.py \
  --prompt-file .context/<task>/prompt.md \
  --output-dir .context/<task> \
  --expected-artifact <name>.jpg
```

Raw form when the wrapper's flags do not cover the sandbox and repo-check needs:

```bash
timeout 600 codex exec --sandbox workspace-write --skip-git-repo-check --cd <output-dir> \
  "imggen で <subject, composition, palette, mood>。<absolute-path>/<name>.jpg に保存してください。" < /dev/null
```

Prompt shape: purpose, subject and composition, palette and mood, aspect ratio, what must not appear, and the absolute destination path.

### Success Criteria (additional)

The normal runner checks prove the call ran, not that an image exists. Also require:

- The named file exists at the stated path and is non-empty
- It is actually an image (`file`, or a decode check) — a text file with an image name is a failure
- The caller **looks at the image** before accepting it. Prompt adherence is not guaranteed and the runner cannot judge it

### Cautions

- **Generation is non-deterministic.** The same prompt produces a different image each run. Keep the accepted file; do not expect to regenerate it
- Do not use generated images to depict real, identifiable places, facilities, people, or products. When the image stands in for something real, label it as an illustration where it is used
- Do not ask for logos, brand marks, or text inside the image; render those as vector or live text instead
- For diagrams, prefer authoring SVG directly over generating raster images. Vector output stays editable and does not degrade when scaled for print

## Failure Criteria

Treat any of these as failure:

- Timeout exit, normally exit code `124`.
- Non-zero process exit.
- stderr contains authentication, model, permission, trust, policy, quota, or rate-limit error signatures. When every other success check passes, such stderr matches are recorded in `summary.json.nonfatal_reasons` instead of failing the run.
- JSONL events contain obvious error records.
- `last-message.md` is missing or empty.
- Expected artifacts are missing or empty.

On failure, inspect `.context/<task>/summary.json` first:

- `command`
- `cwd`
- `exit_code`
- `elapsed_seconds`
- `events_bytes`, `stderr_bytes`, and `last_message_bytes`
- `failure_reasons`
- `nonfatal_reasons`
- `last_error_event` or `last_event`
- `expected_artifacts`
- `recommended_next_action`

Stdin-hang signature: when `run.err` contains only `Reading additional input from stdin...` and `run.events.jsonl` is 0 bytes with a timeout exit, `codex exec` blocked reading an open stdin instead of running. This should not occur through the wrapper (it forces stdin from `/dev/null`); if seen on a raw `codex exec` run, rerun with `< /dev/null`.

If a higher-level workflow needs a downstream blocked artifact, create it in the caller using that workflow's schema or template. Do not invent a downstream schema in this runner and do not modify runner evidence artifacts. If no caller schema was supplied, report the runner as blocked with links to `summary.json` and `failure.md` instead of fabricating an artifact format.

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
- Minimal fake behavior: exit `0`, print one non-error JSON object such as `{"type":"event","status":"ok"}`, parse `-o <path>` and write a non-empty final message there, then write the requested expected artifact such as `result.md`.
- Prefer an absolute `--codex-bin` path for fake CLIs unless you have verified the relative path resolves from `--cwd`.
- Keep fake CLIs under `.context/<task>/bin/` and use them only in validation. Do not use `--codex-bin` for real Codex delegation.
- Do not hand-edit `summary.json`, `run.events.jsonl`, `run.err`, `last-message.md`, or `failure.md`. If a controlled test needs explanation, write a separate `notes.md`.

## Wrapper Notes

- Resolve `<skill-dir>` from the location of this `SKILL.md`.
- Pass `--cwd <project-root>` when Codex should run from a specific repository.
- `summary.json.cwd` records the resolved `--cwd`; the shell directory that launched the wrapper is not recorded as a separate field.
- Omit `--model`, `--effort`, and `--profile` by default so Codex CLI uses its configured defaults.
- Pass `--model <model>` and `--effort <level>` from the caller when a model registry, role, or task explicitly requires overrides.
- Use `--prompt-profile gpt-5-5` or `--prompt-profile gpt-5-6` when the caller knows the CLI default model is that generation but does not pass `--model`.
- Pass each expected output as `--expected-artifact`; use an absolute path or a path relative to the wrapper output directory.
- Use `--extra-codex-arg` for narrow additions when explicitly required. Pass one Codex CLI token per wrapper argument, for example `--extra-codex-arg=--sandbox --extra-codex-arg=read-only`, `--extra-codex-arg=--ask-for-approval --extra-codex-arg=never`, or `--extra-codex-arg=--config --extra-codex-arg=key=value`.
- Keep final orchestration in the caller. This skill only runs Codex and records observable artifacts.

## Validation

Validate the skill and wrapper after changes:

```bash
scripts/skill-quick-validate skills/codex-cli-runner
python3 <skill-dir>/scripts/run_codex_cli.py --help
```

For runtime validation, run:

- no-API command construction
- no-API fake Codex success
- no-API fake Codex success with the caller's stdin held open (stdin-hang regression)
- real short smoke prompt
- real file read/write prompt
- forced timeout failure
