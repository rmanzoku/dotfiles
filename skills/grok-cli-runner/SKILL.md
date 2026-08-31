---
name: grok-cli-runner
description: "Run Grok Build CLI headless through a file-based runner contract with observable request, response, summary, and failure artifacts. Use when Claude or Codex needs `grok -p`, GrokをCLIで呼ぶ, delegates coding, review, or research to Grok Build, fetches public X/Twitter post URLs, or validates a request shape without calling the backend."
---

# Grok CLI Runner

Use this skill when delegating work to Grok Build through a file-based runner contract. The runner calls the official `grok` CLI in headless mode (`grok -p`) and records the request, response, summary, stderr, and failure notes under `.context/<task>/` so the call can be audited and replayed.

Frame each delegation as an outcome-first contract: request artifact, expected response artifact, timeout, model, permission mode, session policy, success criteria, and failure handling. Task-scoped editing may be delegated when the caller authorizes it; keep final judgment and irreversible side effects in the caller.

## Core Rules

- Put every run under `.context/<task>/`.
- Save the request as `.context/<task>/grok-request.json`.
- Do not inline JSON request bodies into shell commands. Write the request artifact first and pass it with `--request-file`.
- Use `--dry-run` for request-shape and command validation; it does not call Grok Build and intentionally does not create a response artifact.
- In `--dry-run`, success is checked through `summary.json.dry_run_payload`; do not require `grok-response.json` to exist.
- Use the wrapper's 600-second process timeout default, or pass `--timeout-seconds` when the task needs a shorter or longer limit.
- Use `--permission-mode auto` only for prompt-only tasks that need no tool calls.
- `--no-plan` is the wrapper default; `--plan` is the opt-out and is only for when Grok Build plan mode is explicitly desired.
- For any task that triggers a tool call — shell commands, file writes, and also read-only X post or Web fetches — pass `--permission-mode bypassPermissions`. Headless Grok cannot answer permission prompts: under `auto` the first tool call that needs approval is cancelled and the run ends with exit 0 and `stopReason=Cancelled`.
- The wrapper passes `--verbatim` by default so Grok receives the derived prompt directly. Use `--no-verbatim` only when Grok Build's default prompt shaping is explicitly needed.
- Pass `--always-approve` only when the caller explicitly accepts tool side effects. The wrapper then omits `--permission-mode` entirely, because grok 0.2.112 lets an explicit `--permission-mode` override `--always-approve` (contrary to its docs) and cancels headless runs.
- `GROK_BIN`, `GROK_OUTPUT_FORMAT`, and `GROK_PERMISSION_MODE` supply defaults from the environment. `GROK_PERMISSION_MODE` silently changes the permission mode this skill otherwise makes explicit — check it before diagnosing a cancelled run.
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
- Model: omit `--model` unless the caller or model registry requires an override. See the resolution chain under Standard Command Shape.
- Timeout: rely on the 600-second wrapper default unless the task contract says otherwise.
- Permission mode: rely on `--permission-mode auto` only for prompt-only tasks with no tool calls; pass `--permission-mode bypassPermissions` when the task uses any tool, including shell commands, file writes, and read-only X post or Web fetches (for example when the expected artifact is written by Grok itself, or when the task retrieves a public X post URL).
- Verbatim mode: keep the default `--verbatim`; use `--no-verbatim` only for compatibility testing.
- Output format: rely on `--output-format json`; use `streaming-json` only when incremental event capture matters, and `plain` only for compatibility.
- Session state: omit `--session-id`, `--resume`, and `--continue-session` unless continuity is required and documented in the request.
- Working directory: `--cwd` controls both the subprocess working directory and Grok Build `--cwd`.
- Expected artifacts: if the target artifact is the Grok response itself, make it `--response-artifact`; if other files must be created after reading Grok output, track those outside this wrapper.

Do not add "think hard", fixed progress-update scaffolds, or mandatory step-by-step narration to simulate effort. Use model selection, request fields, permission mode, and explicit success criteria instead.

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
  --permission-mode auto \
  --no-plan \
  --verbatim
```

The wrapper adds `-m <resolved-model>` only when a model resolves from `--model`, `request.model`, `GROK_BUILD_MODEL`, or `GROK_MODEL`. Otherwise it omits `-m` so Grok Build CLI uses its own default model; check `grok models` for the current default and valid model ids.

Add these only when needed:

- `--model <model>` to override model defaulting.
- `--timeout-seconds <seconds>` to override the 600-second process timeout.
- `--grok-bin <path>` when the `grok` executable is not on `PATH`.
- `--permission-mode <mode>` when the caller explicitly chooses a Grok Build permission mode; use `bypassPermissions` for any task with tool calls, including read-only X post or Web fetches.
- `--plan` only when Grok Build plan mode is explicitly desired.
- `--no-verbatim` only when the caller explicitly wants Grok Build's default prompt shaping.
- `--always-approve` only when tool side effects are explicitly accepted; the wrapper then omits `--permission-mode`.
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
- resolved response artifact, normally `grok-response.json`: normalized response artifact for real calls. Written before the `stop_reason` check, so it also exists on `Cancelled` runs.
- `run.err`: Grok Build stderr and local wrapper diagnostics.
- `summary.json`: run evidence — redacted command, exit code, `stop_reason`, `failure_reasons`, `recommended_next_action`, and the resolved flag state. `references/schema.md` documents every field.
- `failure.md`: only when the wrapper run fails.

## Request Contract

Read `references/schema.md` when creating or validating request/response artifacts.

Required request artifact fields:

- `task`: stable task identifier.
- `request`: object normalized by the wrapper into a Grok Build headless prompt.

Important request rules:

- `request.input` is required.
- `request.model` is optional; when it is omitted and no `--model` or env override is set, the wrapper omits `-m` and Grok Build CLI's default model applies.
- `request.instructions` is rejected; put instruction text into `request.input`.
- `meta` is optional and stays local; it is not sent to Grok Build as a structured field.
- Keep one backend job per request artifact.

## Success Criteria

Require all applicable checks:

- Process exit code is `0`.
- For real runs with `json` or `streaming-json` output, `summary.json.stop_reason` is `EndTurn`.
- For real runs, the resolved response artifact exists and is non-empty.
- Response artifact contains `request`, `response`, `model` (`null` when the run delegated to the Grok Build CLI default model), `backend`, and `output_text` or parsed stdout sufficient for the caller to inspect.
- `summary.json.success` is `true`. The wrapper defines it as an empty `failure_reasons`.
- For `--dry-run`, success means the request validated and `summary.json.dry_run_payload` was written; no response artifact is expected.

These checks prove runner execution and non-empty response materialization only. The caller must still evaluate task-specific response quality against the request artifact.

## Image Generation Route

Grok Build exposes image generation as an **agent tool (`image_gen`, reached through its `imagine` skill), not a CLI subcommand.** `grok imagine` is not a command; passing it only prints help. Request images through the normal prompt path.

### Contract

- **Permission mode must be `bypassPermissions`.** Image generation is a tool call and the agent also writes the file. Under `auto` the run ends with exit 0 and `stopReason=Cancelled`.
- **State the absolute output path and file name in `request.input`.** The agent generates into its own session folder first and then copies; without an explicit destination the file stays where the caller cannot find it.
- **The generated image is not the response artifact.** `grok-response.json` holds the text reply. Track the image separately and verify it yourself.
- Set `--cwd` to the directory that should receive the image.

Request artifact shape:

```json
{
  "task": "<task>",
  "request": {
    "input": "画像を1枚生成し、<absolute-path>/<name>.jpg に保存してください。\n\n用途: <where it will be used>\n\n生成する画像の内容:\n<subject, composition, palette, mood, aspect ratio>\n\n避けること:\n<what must not appear>\n\n生成後、保存したファイルのパスを報告してください。"
  }
}
```

Run:

```bash
python3 <skill-dir>/scripts/run_grok_cli.py \
  --request-file .context/<task>/grok-request.json \
  --output-dir .context/<task> \
  --response-artifact grok-response.json \
  --permission-mode bypassPermissions \
  --cwd .context/<task>
```

### Success Criteria (additional)

The normal runner checks prove the call ran, not that an image exists. Also require:

- The named file exists at the stated path and is non-empty
- It is actually an image (`file`, or a decode check) — a text file with an image name is a failure
- The caller **looks at the image** before accepting it. Prompt adherence is not guaranteed and the runner cannot judge it

### Cautions

- **Generation is non-deterministic.** The same input produces a different image each run. Keep the accepted file; do not expect to regenerate it

## Failure Criteria

Treat any of these as failure:

- Timeout exit, normally exit code `124`.
- Non-zero process exit.
- Missing or invalid request artifact.
- Missing `request.input`.
- Missing `grok` executable.
- Grok Build auth, model, permission, policy, update, or rate-limit errors.
- For real `json` or `streaming-json` runs, `stop_reason` other than `EndTurn`, normally `Cancelled` from a headless permission prompt that nothing could answer (exit code stays `0`; only `stop_reason` reveals the failure). `plain` output and `--dry-run` leave `stop_reason` `null` and are not judged on it.
- Real run response artifact is missing or empty.

On failure, inspect `.context/<task>/summary.json` first. Start with `failure_reasons`,
`recommended_next_action`, `stop_reason`, `exit_code`, and `api_error`.
`references/schema.md` documents every field.

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
- optional public X URL smoke with `--permission-mode bypassPermissions` (X post fetch is a tool call; under `auto` it ends with `stopReason=Cancelled`)
