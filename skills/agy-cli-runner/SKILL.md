---
name: agy-cli-runner
description: "Run Antigravity CLI (agy) headless with observable prompt, response, summary, and failure artifacts under `.context/task/`. Use when Claude or Codex needs to call Gemini through agy, geminiをCLIで呼ぶ, run the GEO gemini engine, delegate research or web-search work to `agy -p`, or validate an agy request shape without calling the backend."
---

# agy CLI Runner

Use this skill when delegating work to Gemini through Antigravity CLI (`agy`). The runner calls `agy` in print mode and records the prompt, response, summary, stderr, and failure notes under `.context/<task>/` so the call can be audited and replayed.

This is the successor to the gemini CLI route: the personal-tier gemini CLI was discontinued, and `agy` is the supported way to reach Gemini models headlessly. Frame each delegation as an outcome-first contract: prompt artifact, expected response artifact, timeout, model, permission posture, success criteria, and failure handling. Task-scoped editing may be delegated when the caller authorizes it; keep final judgment and irreversible side effects in the caller.

## Core Rules

- Put every run under `.context/<task>/`.
- Save the prompt as a markdown file and pass it with `--prompt-file`. The file is the source of truth; the wrapper copies what it actually sent to `run.prompt.md`.
- Do not inline prompt bodies into shell commands yourself. See "Prompt transport" for why the wrapper still puts the prompt on agy's argv, and what that constrains.
- `--model` is required. agy has **no `auto`**; an invalid id fails the run with `agy_error`. Run `agy models` for current ids.
- Use `--dry-run` for command-shape validation. It does not call agy and intentionally creates no response artifact; check `summary.json.dry_run_payload`.
- Use the wrapper's 600-second process timeout default, or pass `--timeout-seconds` when the task needs a different limit. The wrapper derives agy's own `--print-timeout` to fire *before* its own kill, so failures arrive as agy's structured error rather than a signal.
- For any task that triggers a tool call — web search, file reads, file writes — pass `--skip-permissions`. Headless agy cannot answer a permission prompt: without it the run can end exit 0 with an empty response.
- Do not treat a 0-byte `run.err` alone as a hang; use exit code, `status`, `failure_reasons`, and elapsed time.
- Do not add fallback backends. If `agy` is missing, unauthenticated, or rejects the model, report that failure from the artifacts.

## Prompt transport

agy's print mode accepts the prompt **only as an argv value** (`-p <prompt>`). Verified 2026-08-08 on agy 1.1.10:

- `agy -p --model gemini-3.1-pro-low "…"` — `-p` swallows `--model` as its prompt value.
- Piping the prompt on stdin returns `status: SUCCESS` with an **empty response**; stdin is not read as context.

The global rule "pass multi-line content between CLIs through real files, not `-p` inline expansion" exists to keep handoffs auditable and to avoid quoting damage. agy offers no file or stdin interface, so this runner keeps the *auditability* half — the prompt file is canonical, the sent bytes are saved to `run.prompt.md` — and accepts argv as the only available transport. The quoting-damage half is handled by passing the prompt as a single argv element (no shell interpolation) plus a hard **128 KiB** size check that fails loudly with `invalid_prompt` instead of letting `execve` truncate or fail obscurely.

## agy Setup

`agy` ships with Antigravity. Confirm it resolves and is authenticated:

```bash
agy models
```

```bash
agy -p "Say ok." --model gemini-3.1-pro-low --output-format json
```

Do not write secret values into prompt artifacts, repo files, or `.context/`.

## Caller Checklist

Before running agy, decide explicitly:

- Task directory: choose `.context/<task>/`.
- Prompt artifact: record outcome, exact delegated paths (or `none`), allowed side effects, success and stop conditions. `--output-dir` evidence is separate; retries keep this boundary. Keep one job per file.
- Response artifact: pass `--response-artifact agy-response.json` when it belongs inside `--output-dir`; use an absolute path only when it must land elsewhere.
- Model: required. Pick from `agy models` — currently `gemini-3.6-flash-{high,medium,low}`, `gemini-3.5-flash-{high,medium,low}`, `gemini-3.1-pro-{high,low}`, plus non-Gemini ids. For registry-driven calls, resolve the id through the working repository's model registry (for example `rules/model_registry.yaml`) rather than hardcoding it in a caller script.
- Effort: `--effort low|medium|high` when the task warrants it; omit to use the model default.
- Permissions: `--skip-permissions` for anything needing web search or file access; omit for prompt-only tasks.
- Timeout: rely on the 600-second default unless the contract says otherwise.
- Working directory: `--cwd` sets the subprocess working directory. Use a per-batch sandbox directory when running independent measurements.
- Write boundary: map delegated paths to caller-selected `--sandbox` / `--add-dir` controls when needed. If the CLI cannot enforce them, verify changed paths before acceptance or retry and stop on mismatch.
- Expected artifacts: if the target artifact is agy's response itself, make it `--response-artifact`. Files that agy writes must be tracked outside this wrapper.

Do not add "think hard", fixed progress-update scaffolds, or mandatory step-by-step narration to simulate effort. Use model selection, `--effort`, and explicit success criteria instead.

## Standard Command Shape

```bash
python3 <skill-dir>/scripts/run_agy_cli.py \
  --prompt-file .context/<task>/prompt.md \
  --output-dir .context/<task> \
  --response-artifact agy-response.json \
  --model gemini-3.1-pro-high
```

The wrapper calls:

```bash
timeout 600 agy -p "<prompt from prompt-file>" \
  --model <model> --output-format json --print-timeout 570s
```

Add these only when needed:

- `--skip-permissions` for tool-using tasks (web search, file access).
- `--effort low|medium|high` to set reasoning effort.
- `--timeout-seconds <seconds>` to override the 600-second process timeout.
- `--cwd <dir>` to run from a specific directory.
- `--agy-bin <path>` when `agy` is not on `PATH`.
- `--sandbox`, `--add-dir <dir>`, `--agent <name>` to pass agy's corresponding flags.
- `--output-format text` or `stream-json` only when JSON's `status`/`usage` fields are not wanted.
- `--extra-agy-arg` (repeatable, one token per flag) for agy flags this wrapper does not model, e.g. `--extra-agy-arg=--json-schema --extra-agy-arg=schema.json`.

For command-shape validation without a backend call, add `--dry-run`.

The wrapper writes:

- `run.prompt.md`: the exact prompt bytes sent.
- stdout progress lines: start, completion, and failure status.
- resolved response artifact, normally `agy-response.json`: normalized response with `task`, `created_at`, `request`, `response.parsed_stdout`, `output_text`, `conversation_id`, `model`, `backend`.
- `run.err`: agy stderr and wrapper diagnostics.
- `summary.json`: redacted command, resolved `cwd`, prompt bytes and limit, model, effort, output format, permission/sandbox flags, exit code, `status`, `usage`, elapsed time, byte counts, `agy_error`, `setup_error`, `failure_reasons`, and `recommended_next_action`.
- `failure.md`: only when the run fails.

## Success Criteria

Require all applicable checks:

- Process exit code is `0`.
- For real runs with `json` output, `summary.json.status` is `SUCCESS`.
- The resolved response artifact exists and `output_text` is non-empty.
- `summary.json.success` is `true` and `failure_reasons` is empty.
- For `--dry-run`, success means the prompt validated and `summary.json.dry_run_payload` was written; no response artifact is expected.

These checks prove execution and non-empty materialization only. The caller must still evaluate response quality against the prompt.

## Failure Criteria

Treat any of these as failure, and read `summary.json` first:

| `failure_reasons` | Meaning | Typical fix |
|---|---|---|
| `invalid_prompt` | prompt file missing, empty, or over 128 KiB | fix or split the prompt file |
| `missing_agy` | `agy` not on `PATH` | install Antigravity CLI |
| `timeout` | exit `124` from the process timeout | raise `--timeout-seconds` or shrink the prompt |
| `agy_error` | agy returned an `error` field | read it; invalid `--model` is the common case |
| `status_not_success` | exit 0 but `status` is not `SUCCESS` | inspect `parsed_stdout` and `run.err` |
| `empty_response` | exit 0, `SUCCESS`, empty text | usually a blocked tool call — rerun with `--skip-permissions` |
| `nonzero_exit` | other non-zero exit | inspect `run.err` (auth, flags) |

If a higher-level workflow needs a downstream blocked artifact, create it in the caller using that workflow's schema. Do not invent a downstream schema here and do not modify runner evidence artifacts.

## No-Call Validation

- Run `--dry-run` with a valid prompt file. It should exit `0`, write `summary.json`, and require no backend call.
- Run with a missing prompt file to confirm `failure.md` and `failure_reasons: ["invalid_prompt"]`.
- Run with an invalid `--model` to confirm `agy_error` classification.
- Run `python3 <skill-dir>/scripts/run_agy_cli.py --help` after wrapper changes.

Do not hand-edit `summary.json`, `run.err`, the response artifact, or `failure.md`. If a controlled test needs explanation, write a separate `notes.md`.

## Wrapper Notes

- Resolve `<skill-dir>` from the location of this `SKILL.md`.
- `summary.json.command` redacts the prompt body as `<prompt from prompt-file>`; the prompt file and `run.prompt.md` remain the source of truth.
- `--print-timeout` is derived from `--timeout-seconds` (30s margin above 60s, 10% below) so agy gives up before the wrapper kills it. Override it explicitly only when agy's own limit must differ.
- Keep final orchestration in the caller. This skill only calls agy and records observable artifacts.

## Validation

```bash
scripts/skill-quick-validate skills/agy-cli-runner
python3 skills/agy-cli-runner/scripts/run_agy_cli.py --help
```
