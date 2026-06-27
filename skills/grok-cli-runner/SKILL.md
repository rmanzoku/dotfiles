---
name: grok-cli-runner
description: Run Grok Build CLI headless handoffs through a file-based runner contract with observable request, response, summary, stderr, timeout, dry-run, and failure artifacts. Use when Codex or Claude needs to call Grok Build, GrokをCLIで呼ぶ, delegate coding/review/research work to `grok -p`, retrieve or inspect public X/Twitter post URLs through Grok Build, run Grok Build in scripts or automations, validate a Grok Build request shape without calling the backend, or preserve reproducible `.context/task/` artifacts around a Grok Build CLI invocation.
---

# Grok CLI Runner

Use this skill when delegating work to Grok Build through a file-based runner contract. The runner calls the official `grok` CLI in headless mode (`grok -p`) and records the request, response, summary, stderr, and failure notes under `.context/<task>/` so the call can be audited and replayed.

Frame each delegation as an outcome-first contract: request artifact, expected response artifact, timeout, model, permission mode, session policy, success criteria, and failure handling. Keep final judgment, editing, and irreversible side effects in the caller.

## Core Rules

- Put every run under `.context/<task>/`.
- Save the request as `.context/<task>/grok-request.json`.
- Do not inline JSON request bodies into shell commands. Write the request artifact first and pass it with `--request-file`.
- Use `--dry-run` for request-shape and command validation; it does not call Grok Build and intentionally does not create a response artifact.
- In `--dry-run`, success is checked through `summary.json.dry_run_payload`; do not require `grok-response.json` to exist.
- Use the wrapper's 600-second process timeout default, or pass `--timeout-seconds` when the task needs a shorter or longer limit.
- Use `--permission-mode auto --no-plan` by default. Pass `--plan` only when Grok Build plan mode is explicitly desired.
- The wrapper passes `--verbatim` by default so Grok receives the derived prompt directly. Use `--no-verbatim` only when Grok Build's default prompt shaping is explicitly needed.
- Pass `--always-approve` only when the caller explicitly accepts tool side effects.
- Pass session flags only when session state is part of the task contract. Default to a stateless one-shot headless run.
- Do not treat 0-byte `run.err` or a missing response artifact alone as a hang; use exit code, timeout, `summary.json`, and failure reasons.
- Do not add fallback backends. If Grok Build CLI is missing, unauthenticated, or rejected by model/permission state, report that failure from the artifacts.

## Grok Build Setup

Install the official Grok Build CLI:

```bash
curl -fsSL https://x.ai/cli/install.sh | bash
```

Authenticate with one of the official headless-compatible methods:

```bash
grok login
grok login --device-auth
```

For script-only API-key auth, provide `XAI_API_KEY` through the caller environment or an approved secret-reference flow. Do not write secret values into request artifacts, repo files, or `.context/`.

Useful checks:

```bash
grok inspect
grok --no-auto-update -p "Say ok." --output-format json
```

## Caller Checklist

Before running Grok, make these decisions explicitly:

- Task directory: choose `.context/<task>/`.
- Request artifact: write `.context/<task>/grok-request.json` with top-level `task` and `request`.
- Response artifact: pass `--response-artifact grok-response.json` when the response belongs inside `--output-dir`; use an absolute path only when the response must be written outside `--output-dir`.
- Model: omit `--model` unless the caller or model registry requires an override. The wrapper resolves `--model`, then `request.model`, then `GROK_BUILD_MODEL`, then `GROK_MODEL`, then `grok-build`.
- Timeout: rely on the 600-second wrapper default unless the task contract says otherwise.
- Permission mode: rely on `--permission-mode auto --no-plan` unless the caller explicitly chooses another Grok Build permission mode.
- Verbatim mode: keep the default `--verbatim`; use `--no-verbatim` only for compatibility testing.
- Output format: rely on `--output-format json`; use `streaming-json` only when incremental event capture matters, and `plain` only for compatibility.
- Session state: omit `--session-id`, `--resume`, and `--continue-session` unless continuity is required and documented in the request.
- Working directory: `--cwd` controls both the subprocess working directory and Grok Build `--cwd`.
- Expected artifacts: if the target artifact is the Grok response itself, make it `--response-artifact`; if other files must be created after reading Grok output, track those outside this wrapper.

Do not add "think hard", fixed progress-update scaffolds, or mandatory step-by-step narration to simulate model effort. Use model selection, request fields, permission mode, and explicit success criteria instead.

## Standard Command Shape

For a normal Grok Build headless run:

```bash
python3 <skill-dir>/scripts/run_grok_cli.py \
  --request-file .context/<task>/grok-request.json \
  --output-dir .context/<task> \
  --response-artifact grok-response.json
```

The wrapper calls:

```bash
grok --no-auto-update -p "<prompt derived from request artifact>" \
  --output-format json \
  --cwd <resolved-cwd> \
  -m <resolved-model> \
  --permission-mode auto \
  --no-plan \
  --verbatim
```

Add these only when needed:

- `--model <model>` to override model defaulting.
- `--timeout-seconds <seconds>` to override the 600-second process timeout.
- `--grok-bin <path>` when the `grok` executable is not on `PATH`.
- `--permission-mode <mode>` when the caller explicitly chooses a Grok Build permission mode.
- `--plan` only when Grok Build plan mode is explicitly desired.
- `--no-verbatim` only when the caller explicitly wants Grok Build's default prompt shaping.
- `--always-approve` only when tool side effects are explicitly accepted.
- `--session-id <id>`, `--resume <id>`, or `--continue-session` only when session continuity is part of the task.
- `--output-format streaming-json` only when event capture matters.

For request-shape validation without a backend call:

```bash
python3 <skill-dir>/scripts/run_grok_cli.py \
  --request-file .context/<task>/grok-request.json \
  --output-dir .context/<task> \
  --response-artifact grok-response.json \
  --dry-run
```

The wrapper writes:

- `grok-request.json`: caller-authored request artifact.
- stdout progress lines: Grok Build start, completion, and failure status.
- resolved response artifact, normally `grok-response.json`: normalized response artifact for successful real calls.
- `run.err`: Grok Build stderr and local wrapper diagnostics.
- `summary.json`: redacted command, resolved `cwd`, exit code, elapsed time, byte counts, model, output format, permission mode, session flags, dry-run payload, response artifact path/status, `failure_reasons`, and `recommended_next_action`.
- `summary.json.no_plan` and `summary.json.verbatim`: whether `--no-plan` and `--verbatim` were used.
- `failure.md`: only when the wrapper run fails.

## Request Contract

Read `references/schema.md` when creating or validating request/response artifacts.

Required request artifact fields:

- `task`: stable task identifier.
- `request`: object normalized by the wrapper into a Grok Build headless prompt.

Important request rules:

- `request.input` is required.
- `request.model` is optional; wrapper model defaulting fills it when omitted.
- `request.instructions` is rejected; put instruction text into `request.input`.
- `meta` is optional and stays local; it is not sent to Grok Build as a structured field.
- Keep one backend job per request artifact.

## Success Criteria

Require all applicable checks:

- Process exit code is `0`.
- For real runs, the resolved response artifact exists and is non-empty.
- Response artifact contains `request`, `response`, `model`, `backend`, and `output_text` or parsed stdout sufficient for the caller to inspect.
- `summary.json.success` is `true`, `summary.json.failure_reasons` is empty, and `summary.json.response_non_empty` is `true`.
- For `--dry-run`, success means the request validated and `summary.json.dry_run_payload` was written; no response artifact is expected.

These checks prove runner execution and non-empty response materialization only. The caller must still evaluate task-specific response quality against the request artifact.

## Failure Criteria

Treat any of these as failure:

- Timeout exit, normally exit code `124`.
- Non-zero process exit.
- Missing or invalid request artifact.
- Missing `request.input`.
- Missing `grok` executable.
- Grok Build auth, model, permission, policy, update, or rate-limit errors.
- Real run response artifact is missing or empty.

On failure, inspect `.context/<task>/summary.json` first:

- `command`
- `cwd`
- `exit_code`
- `elapsed_seconds`
- `request_bytes`, `prompt_bytes`, `response_bytes`, and `stderr_bytes`
- `model`
- `grok_bin`
- `output_format`
- `permission_mode`
- `no_plan` and `verbatim`
- `session_id`, `resume`, `continue_session`, and `always_approve`
- `dry_run`
- `failure_reasons`
- `api_error`
- `response_artifact`
- `response_non_empty`
- `recommended_next_action`

If a higher-level workflow needs a downstream blocked artifact, create it in the caller using that workflow's schema or template. Do not invent a downstream schema in this runner and do not modify runner evidence artifacts. If no caller schema was supplied, report the runner as blocked with links to `summary.json` and `failure.md`.

## No-Call Validation

Use these patterns when testing the wrapper itself without making a backend call:

- Run `--dry-run` with a valid request artifact. It should exit `0`, write `summary.json`, and not require `grok` or `XAI_API_KEY`.
- For successful `--dry-run`, inspect `summary.json.dry_run_payload`; no `grok-response.json` is expected.
- Run with an invalid request artifact to confirm `failure.md` and `summary.json.failure_reasons` are generated.
- Run `python3 <skill-dir>/scripts/run_grok_cli.py --help` after wrapper changes.
- Run a real Grok Build smoke only when the CLI is installed and auth is available.

Do not hand-edit `summary.json`, `run.err`, the response artifact, or `failure.md`. If a controlled test needs explanation, write a separate `notes.md`.

## Wrapper Notes

- Resolve `<skill-dir>` from the location of this `SKILL.md`.
- Pass `--cwd <project-root>` when the caller wants Grok Build launched from a specific repository.
- `summary.json.command` redacts the prompt body as `<prompt from request artifact>`; the request artifact remains the source of truth.
- The wrapper passes `--no-auto-update` on every real run to avoid background update checks in automation.
- Keep final orchestration in the caller. This skill only calls Grok Build and records observable artifacts.

## Validation

Validate the skill and wrapper after changes:

```bash
scripts/skill-quick-validate skills/grok-cli-runner
python3 skills/grok-cli-runner/scripts/run_grok_cli.py --help
```

For runtime validation, run:

- no-call dry-run success
- invalid request failure
- optional real Grok Build smoke when `grok` is installed and authenticated
- optional public X URL smoke with `--permission-mode auto --no-plan`
