---
name: codex-runner
description: "Run Codex through app-server with goals, JSON-RPC logs, timeouts, and artifact checks, or explicitly select legacy exec. Use for CodexをCLIで呼ぶ or delegated Codex research, review, generation, and file work."
---

# Codex Runner

Use this skill when an orchestrating agent delegates work to Codex. The default transport is a dedicated stdio `codex app-server` with a goal. Keep the source prompt, launch prompt, JSONL events, final message, stderr, summary, and failure notes under `.context/<task>/`.

Frame each delegation as an outcome-first contract: source prompt, expected artifacts, timeout, success criteria, allowed side effects, and failure handling. Let caller-provided model, effort, and Codex config do model selection and permission policy. Named config profiles require explicit exec transport.

## Core Rules

- Use the bundled wrapper; it starts a dedicated stdio app-server by default. `--app-server-daemon` connects to an existing daemon without starting or stopping it. `--transport exec` explicitly selects the legacy route. Never fall back between transports on failure.
- A goal is set by default: complete the first message's request and all Success criteria; stop as blocked only under its Stop only if conditions. Override with `--goal-objective` or `--goal-objective-file`, or explicitly disable with `--no-goal`.
- Put every run under `.context/<task>/`.
- Save the real assignment as `.context/<task>/prompt.md`.
- Do not pass a large prompt body as an inline shell argument. Pass a short instruction that tells Codex to read `.context/<task>/run.prompt.md`.
- Use the wrapper's 600-second timeout default, or pass an explicit timeout override when the task needs a shorter or longer limit.
- Do not force sandbox or approval policy. App-server inherits config (the daemon owns its startup configuration); server requests, including approvals, are logged and rejected. Exec inherits config/profile and accepts explicit caller overrides via extra args.
- Do not treat 0-byte `run.events.jsonl` or `run.err` as a hang by itself.

## Caller Checklist

Before running Codex, settle these items. Use the stated default when the task does not specify one; ask only when an item without a default (the source prompt's outcome) cannot be inferred from the task.

- Task directory: choose `.context/<task>/`.
- Source prompt: write `.context/<task>/prompt.md` with the outcome, artifact paths, success criteria, allowed side effects, evidence rules, and stop condition. If an expected artifact path is absolute, put that same absolute path in the source prompt; `--expected-artifact` only verifies materialization.
- Working directory: pass `--cwd <project-root>` when the target repository matters.
- Expected artifacts: pass every required output with `--expected-artifact`; relative paths resolve from `--output-dir`, so use absolute paths for artifacts that must be written outside `.context/<task>/`.
- When `--output-dir .context/<task>` is used, pass `--expected-artifact result.md`, not `--expected-artifact .context/<task>/result.md`; the latter resolves under `.context/<task>/.context/<task>/`.
- Defaults: omit `--model`, `--effort`, and `--profile` unless the caller, model registry, or role explicitly requires an override.
- Timeout: rely on the 600-second wrapper default unless the task contract says otherwise.
- Transport: stdio is the default; daemon is an explicit option sharing the desktop server and can be interrupted by daemon updates. Exec is explicit and has no goal lifecycle.
- Config profile: use `--profile` only with `--transport exec`. With either app-server route it fails before any Codex process, including the version probe, with `profile_unsupported_app_server` in `summary.json`. Remove the profile or select exec; it is never ignored.
- Goal: use the default objective unless the task needs its own; store a multiline objective in a file and use `--goal-objective-file`. Goal options and daemon selection cannot be combined with exec (except `--no-goal`, which is redundant for exec).
- Prompt profile: when `--model` is passed, rely on `--prompt-profile auto`. When `--model` is omitted, read the non-secret `model` setting from the effective config (or the exec profile) and pass the matching adapter: `gpt-6` for `gpt-6.1-sol` / `gpt-6.1-terra` / `gpt-6-astra` / `gpt-6-sol`, `gpt-6-luna` for `gpt-6-luna`. For daemon runs, confirm its model or explicitly pass `--model`. Older generations get no adapter. Omitting both leaves the run without a generation adapter.
- Extra Codex args and `--timeout-bin`: exec only; app-server rejects them rather than ignoring them. Pass each exec token as its own `--extra-codex-arg=<token>` value.

Do not add "think hard", fixed progress-update scaffolds, or mandatory step-by-step narration to simulate effort. Use `--effort` only when the caller explicitly asks for an effort override.

## Standard Command Shape

Use the bundled wrapper for the default stdio app-server and goal:

```bash
python3 <skill-dir>/scripts/run_codex.py \
  --prompt-file .context/<task>/prompt.md \
  --output-dir .context/<task> \
  --expected-artifact <expected-file>
```

Add `--model <model>` or `--effort <low|medium|high|xhigh>` only when overriding Codex defaults. Add `--app-server-daemon` to connect to the existing Unix WebSocket at `$CODEX_HOME/app-server-control/app-server-control.sock` (default home: `~/.codex`).
Add `--transport exec` for legacy exec, and only there `--profile <profile>` if required.
Add `--timeout-seconds <seconds>` only when overriding the 600-second default.

The wrapper writes:

- `run.prompt.md`: launch prompt sent to Codex, including any prompt profile adapter
- `run.events.jsonl`: all sent/received app-server JSON-RPC messages, each wrapped as `direction` and `message`; exec retains its stdout JSONL format
- `run.err`: stderr
- `last-message.md`: last completed agent message (exec uses `--output-last-message`)
- `summary.json`: command, resolved `cwd`, exit code, elapsed time, byte counts, parsed errors, prompt profile, `failure_reasons`, `nonfatal_reasons`, `recommended_next_action`, `expected_artifacts`, `transport`, `thread_id`, `goal` (status, tokens, time), and `turn_count`; also `codex_bin_path`, `codex_version`, and `codex_version_error`
- `failure.md`: only when the wrapper run fails

## Prompt Profiles

The wrapper writes `.context/<task>/run.prompt.md`, then sends only a file-reference prompt through app-server `turn/start` or explicit exec. Prompt profiles adapt the assignment text; they are separate from `--profile`, the exec-only config profile.

Default behavior:

- `--prompt-profile auto` is the default.
- When `--model` explicitly looks like GPT-6 (`gpt-6.1-sol`, `gpt-6.1-terra`, `gpt-6-astra`, `gpt-6-sol`, or similar), `auto` applies the GPT-6 adapter; for `gpt-6-luna` it applies `gpt-6-luna`, which adds a verification line.
- When `--model` is omitted, `auto` resolves to `none` because the wrapper cannot read the Codex configured default. Check the configured `model` and pass the matching `--prompt-profile` (see Caller Checklist).
- Pass `--prompt-profile none` to suppress model-specific prompt adaptation.

The GPT-6 adapter compensates for GPT-6's documented tendencies to ask for clarification too readily, pause on conflicting skill or AGENTS.md guidance, stop after a first implementation, and over-test. It tells Codex to infer intent and keep working, let the source prompt override skill guidance (quoting any instruction that causes a pause), finish every completion criterion, and scale verification to risk. Codex's built-in GPT-6 instructions already cover general autonomy, so the adapter stays short. The Luna base instructions skip tests unless asked, so `gpt-6-luna` adds one line to run the verification listed in the success criteria. Generation doctrine is maintained in the `gpt-6-tuning` skill; rationale is in ADR 0076.

## Default Response Format

Every launch prompt supplies a default AI-to-AI handoff shape when `prompt.md` does not explicitly require another format:

- `## Result`: outcome or direct answer.
- `## Evidence`: verified facts, sources, or reasoning.
- `## Changes`: files or actions changed; omit for no-change tasks.
- `## Blockers`: missing input, failure, or next action; omit when none.

Use only applicable sections, keep the response concise, and do not wrap the whole response in JSON or a Markdown code fence. An explicit source-prompt output format always overrides this default.

## Success Criteria

Require all applicable checks:

- `summary.json.exit_code` is `0` (the app-server client outcome, or the exec process exit).
- With an app-server goal enabled, its final status is `complete`; a completed turn alone is insufficient. Without a goal, require a completed turn. Exec does not set a goal.
- `run.events.jsonl` exists and is non-empty.
- `last-message.md` exists and is non-empty.
- Every expected artifact exists and is non-empty.
- Exec JSONL events do not contain error records; app-server has no fatal RPC, turn, server, or goal failure. Logged rejection responses to server requests can be nonfatal when all other checks pass.
- `summary.json.success` is `true`, `summary.json.failure_reasons` is empty, and every item in `summary.json.expected_artifacts` has `exists=true` and `non_empty=true`.

These checks prove runner execution and non-empty artifact materialization only. The caller must still evaluate task-specific artifact quality against the source prompt.

## Image Generation Route

Codex exposes image generation as an **agent tool (`imggen`), not a CLI subcommand.** `codex imggen` is not a command; passing it only prints help. Request images through the normal prompt path.

### Contract

- **`--sandbox workspace-write`** is required. The agent writes the image file
- **`--cd <output-dir>`** sets where the run happens. Pair it with an absolute destination path in the prompt
- **`--skip-git-repo-check`** is required when the output directory is not inside a trusted git repository. Without it the run aborts with `Not inside a trusted directory`
- **The image is not `last-message.md`.** The final message only reports the path. Track the image as an expected artifact and verify it yourself

This legacy exec recipe uses explicit extra CLI arguments (an image request is itself the caller's explicit sandbox decision under Core Rules; the wrapper's `--cwd` becomes Codex `-C`):

```bash
python3 <skill-dir>/scripts/run_codex.py \
  --transport exec \
  --prompt-file .context/<task>/prompt.md \
  --output-dir .context/<task> \
  --cwd <output-dir> \
  --expected-artifact <absolute-path>/<name>.jpg \
  --extra-codex-arg=--sandbox --extra-codex-arg=workspace-write \
  --extra-codex-arg=--skip-git-repo-check
```

The raw form below is equivalent and only for debugging outside the wrapper:

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

- **Generation is non-deterministic.** The same input produces a different image each run. Keep the accepted file; do not expect to regenerate it

## Failure Criteria

Treat any of these as failure:

- Timeout exit, normally exit code `124`.
- Goal `blocked`, `budgetLimited`, `usageLimited`, or `paused` (recorded as `goal_<status>`); timeout sends `turn/interrupt` before cleanup.
- Server exit (`server_exited`), RPC rejection (`rpc_error:<method>`), or client/protocol error (`client_error`). No transport fallback is attempted.
- App-server with `--profile`: pre-launch error, exit code `2` in the summary and a non-zero wrapper exit; choose exec or remove the profile.
- Non-zero process exit.
- stderr contains authentication, model, permission, trust, policy, quota, or rate-limit error signatures. When every other success check passes, such stderr matches are recorded in `summary.json.nonfatal_reasons` instead of failing the run.
- Exec JSONL contains error records, or app-server records a fatal RPC, turn, server, or goal failure. Rejected server requests are recorded in `nonfatal_reasons` and do not alone imply failure.
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

See Explicit Exec Route below for its stdin-hang signature. App-server has a dedicated protocol pipe; it does not read the caller's stdin. Progress on wrapper stderr includes start, turn start/completion, goal updates, a 120-second waiting heartbeat, and completion/failure. `run.err` captures server stderr or a client error classification.

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

Run `python3 <skill-dir>/scripts/test_run_codex.py`. It creates fake binaries and scratch files under the working tree's `.context/` and exercises the real subprocess/stdio boundary without inference calls.

- Fake app-server handles `--version`, initialize/initialized, thread/start, goal set/get, turn/start, and interrupt; it emits turn, agent-message, and goal notifications. Cases cover success, multiple turns, rejected server requests, terminal goal failures, timeout/interrupt, server exit, malformed protocol, no-goal, missing artifacts, and open caller stdin.
- Profile rejection checks both app-server routes and verifies that no Codex process (even `--version`) starts. Binary path/version and exec profile compatibility are checked separately.
- Unix WebSocket checks cover upgrade, fragmented frames, ping/pong, and masked client frames.
- For exec-only command construction, use `--transport exec --timeout-bin /usr/bin/true`; success checks should fail because events and final message are missing. A fake exec binary must handle `--version`, print JSONL, and honor `-o <last-message>`.
- Prefer an absolute fake `--codex-bin` path; relative paths resolve from `--cwd`. Keep fake binaries under `.context/`.
- Do not hand-edit `summary.json`, `run.events.jsonl`, `run.err`, `last-message.md`, or `failure.md`. If a controlled test needs explanation, write a separate `notes.md`.

## Explicit Exec Route

Use `--transport exec` when named config profiles or CLI-specific flags are required. This route has no goal lifecycle. Pass each token separately, for example `--extra-codex-arg=--config --extra-codex-arg=tools.web_search=true` for web search; exec rejects `--search`.

For raw debugging commands:

```bash
timeout 600 codex exec --json -o <artifact>.last-message.md "<short-file-reference-prompt>" > <artifact>.events.jsonl 2> <artifact>.err < /dev/null
```

Keep `< /dev/null`: with open non-TTY stdin, exec can block on `Reading additional input from stdin...`. That stderr line plus empty events and timeout identifies the stdin hang. The wrapper already forces exec stdin from `/dev/null`.

## Wrapper Notes

- Resolve `<skill-dir>` from the location of this `SKILL.md`.
- The wrapper runs `--codex-bin` (default `codex`) from `PATH`. On macOS the ChatGPT app bundles Codex at `/Applications/ChatGPT.app/Contents/Resources/codex-cli/bin/codex`. If `codex` is not on `PATH`, pass that path with `--codex-bin` or link it into a directory on `PATH`; do not conclude that Codex is not installed.
- `summary.json.cwd` records the resolved `--cwd`; the shell directory that launched the wrapper is not recorded as a separate field.
- `codex_bin` retains the requested value. `codex_bin_path` records the executable selected using that value and PATH, and the same executable is used for `--version` and execution. No new binary preference or automatic reselection is introduced. `codex_version_error` identifies a failed bounded version probe, also recorded as nonfatal `codex_version_unavailable`. Pre-launch profile rejection leaves version null.
- For daemon transport, binary metadata describes the local CLI, not the independently running daemon; `command` is empty because the runner launches no server.
- See Caller Checklist for when to pass `--cwd`, `--model`, `--effort`, `--profile`, `--prompt-profile`, and `--expected-artifact`.
- Use `--extra-codex-arg` with explicit exec for narrow additions when required. App-server does not accept arbitrary CLI overrides.
- Keep final orchestration in the caller. This skill only runs Codex and records observable artifacts.
- Transport and compatibility rationale: [ADR 0080](../../docs/adr/0080-codex-runner-app-server-goals.md) in the publisher repository.

## Validation

Validate the skill and wrapper after changes:

```bash
scripts/skill-quick-validate skills/codex-runner
python3 <skill-dir>/scripts/test_run_codex.py
python3 <skill-dir>/scripts/run_codex.py --help
```

Run the runtime checks the change touches: documentation-only edits need only `skill-quick-validate`; wrapper changes need the no-API checks; run real-backend smokes only when command construction, output parsing, or timeout handling changed. The checks are:

- no-API protocol, failure, binary metadata, profile, exec, and WebSocket checks above
- real file read/write smoke with `gpt-6.1-sol` and `gpt-6.1-terra`, each through stdio and an existing daemon; require goal `complete` and inspect file contents
- one explicit exec smoke
- forced timeout and interrupt via the fake server
