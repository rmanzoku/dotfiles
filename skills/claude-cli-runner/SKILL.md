---
name: claude-cli-runner
description: Run Claude Code CLI subprocesses with observable stream-json logs, timeouts, optional budget guards, and artifact-based failure handling. Use when Codex needs to invoke `claude -p`, call Claude from the CLI, ClaudeをCLIで呼ぶ, Claude CLIをサブプロセス実行する, or run long-running research, review, generation, or delegated CLI work while distinguishing real hangs from silent execution.
---

# Claude CLI Runner

Use this skill to invoke Claude Code CLI from Codex without losing observability during long-running work. Treat it as the standard wrapper for Claude researcher roles or model-registry calls that delegate research, review, generation, or other CLI work to `claude -p`.

## Execution Policy

- Treat this skill as a reusable Claude CLI wrapper, not as the owner of higher-level orchestration policy.
- Treat model resolver outputs as role/model metadata, not as permission to hand-build raw `claude -p` commands.
- When a workflow previously said "run Claude via resolver", resolve the requested Claude model/effort if needed, then execute Claude through this skill and its wrapper.
- Let the calling workflow decide whether this skill is run directly or through a subagent. For example, the `research` skill may require Codex to delegate researcher roles to subagents; that policy belongs to `research`, not here.

Frame each delegation as an outcome-first contract: source prompt, expected artifacts, timeout, success criteria, allowed side effects, and failure handling. Let caller-provided model and effort settings do model selection; do not encode model behavior with magic words in the source prompt.

## Core Rules

- Do not use normal text output for long-running `claude -p` tasks. It can keep stdout/stderr empty until completion and look hung.
- Put every run under `.context/<task>/`.
- Save the prompt before execution as `.context/<task>/prompt.md`.
- Do not pass a large prompt body as an inline shell argument. Pass a short instruction that tells Claude to read the prompt file.
- Use the wrapper's 600-second timeout default, or pass an explicit timeout override when the task needs a shorter or longer limit.
- For research tasks, explicitly limit WebSearch/WebFetch counts, timeout, and output lines in the prompt.
- Do not treat `stdout` or `stderr` being 0 bytes as a hang by itself.

## Standard Command Shape

Use this form, with `<prompt>` kept short and pointing to the prompt file:

```bash
timeout 600 claude -p --permission-mode bypassPermissions --verbose --output-format stream-json --include-partial-messages "<prompt>" > <artifact>.stream.jsonl 2> <artifact>.err
```

Add `--model <model>` and/or `--effort <level>` only when the caller wants to override the Claude CLI configured defaults.

For repeatable runs, prefer the bundled wrapper:

```bash
python3 <skill-dir>/scripts/run_claude_cli.py \
  --prompt-file .context/<task>/prompt.md \
  --output-dir .context/<task> \
  --expected-artifact <expected-file>
```

Add `--model <model>` or `--effort <low|medium|high|xhigh|max>` to the wrapper only when overriding the CLI defaults.
Add `--timeout-seconds <seconds>` only when overriding the 600-second default.
Add `--budget-usd <amount>` only when an explicit API budget guard is required. Omit it for subscription-based Claude CLI usage.

The wrapper writes:

- `run.prompt.md`: launch prompt sent to Claude, including any model-specific adapter
- `run.stream.jsonl`: Claude stream-json stdout
- `run.err`: stderr
- `summary.json`: command, exit code, elapsed time, byte counts, parsed result/error status, and artifact checks
- `failure.md`: only when the run fails

## Prompt Profiles

The wrapper writes a short launch prompt at `.context/<task>/run.prompt.md`, then passes only a file-reference prompt to `claude -p`. This keeps the shell argument small and leaves the source task prompt in `.context/<task>/prompt.md`.

Default behavior:

- `--prompt-profile auto` is the default.
- When `--model` explicitly looks like Opus 4.7 (`claude-opus-4-7`, `opus-4.7`), `auto` applies the Opus 4.7 adapter to `run.prompt.md`.
- When `--model` explicitly looks like Opus 4.8 (`claude-opus-4-8`, `opus-4.8`), `auto` applies the Opus 4.8 adapter to `run.prompt.md`.
- `auto` does not treat a bare `opus` alias as either version; pass an explicit prompt profile when the CLI default is known.
- When `--model` is omitted, `auto` cannot know the Claude CLI configured default. If the configured default is Opus 4.7 or Opus 4.8, pass `--prompt-profile opus-4-7` or `--prompt-profile opus-4-8` explicitly.
- Pass `--prompt-profile none` to suppress model-specific prompt adaptation.

The Opus 4.7 adapter is intentionally short and positive. It tells Claude to execute the source prompt literally, avoid fixed progress scaffolding, avoid unnecessary subagents/tool calls, respect explicit tool/output limits, and rely on the CLI `--effort` setting instead of prompt magic words.

The Opus 4.8 adapter is intentionally short and positive. It tells Claude to execute the source prompt literally, avoid fixed progress scaffolding, avoid unnecessary subagents/tool calls, preserve coverage in review/finding phases, respect explicit tool/output limits, and rely on the CLI `--effort` setting instead of prompt magic words.

## Success Criteria

Require all applicable checks:

- The stream-json log has a final JSON object with `type=result` and `subtype=success`.
- Every expected artifact file exists and is non-empty.
- The process exits without timeout or CLI-level failure.

## Failure Criteria

Treat any of these as failure:

- Timeout exit, normally exit code `124`.
- stderr contains authentication, model, permission, or rate-limit errors.
- stream-json contains a `type=result` object whose `subtype` starts with `error`, including values such as `error_max_budget_usd`.
- Expected artifact files are missing or empty.
- The process exits non-zero for any reason other than an explicitly accepted test case.

On failure, write `.context/<task>/failure.md` with:

- executed command
- exit code
- elapsed time
- stdout/stderr sizes
- last stream-json result or error
- expected artifact status
- recommended next action

## Prompt Pattern

Create `.context/<task>/prompt.md` with the real assignment, constraints, and expected artifact paths. Then invoke Claude with a short prompt like:

```text
Read and follow the prompt in /absolute/path/to/.context/<task>/prompt.md. Write the requested artifacts exactly where specified.
```

For Claude researcher roles, include:

- max WebSearch/WebFetch calls
- max output lines or words
- timeout expectation
- exact output artifact path
- instruction to stop and write findings instead of continuing if blocked

## Wrapper Notes

- Resolve `<skill-dir>` from the location of this `SKILL.md`.
- Pass `--cwd <project-root>` when Claude should run from a specific repository.
- Omit `--model` and `--effort` by default so Claude CLI uses its configured defaults.
- Pass `--model <model>` and `--effort <level>` from the caller when a model registry, role, or task explicitly requires overrides.
- Use `--prompt-profile opus-4-7` or `--prompt-profile opus-4-8` when the caller knows the CLI default model is that Opus version but does not pass `--model`.
- Pass each expected output as `--expected-artifact`; use an absolute path or a path relative to the wrapper output directory.
- Use `--extra-claude-arg` for narrow additions such as `--tools` or `--add-dir` when needed.
- Keep final orchestration in Codex. This skill only runs Claude and records observable artifacts.

## No-API Validation

Use these patterns when testing the wrapper itself without spending Claude API budget:

- For command-construction checks only, pass `--timeout-bin /usr/bin/true`. This bypasses Claude entirely and should be expected to fail wrapper success checks because no stream-json success result or expected artifact is produced.
- For end-to-end wrapper success without API spend, create a small fake Claude executable under the task directory and pass it with `--claude-bin <path-to-fake-claude>`. The fake CLI must write stream-json stdout ending with `{"type":"result","subtype":"success"}` and create the expected artifact.
- Keep fake CLIs under `.context/<task>/bin/` and use them only in validation. Do not use `--claude-bin` for real Claude delegation.
- Do not hand-edit `summary.json`, `run.stream.jsonl`, `run.err`, or `failure.md`. If a controlled test needs explanation, write a separate `notes.md` next to the wrapper artifacts.

## Validation

Validate the skill and wrapper after changes:

```bash
python3 /Users/rmanzoku/.codex/skills/.system/skill-creator/scripts/quick_validate.py <skill-dir>
python3 <skill-dir>/scripts/run_claude_cli.py --help
```

For runtime validation, run:

- a short smoke prompt
- a prompt that reads and writes a file
- a small WebSearch prompt with strict tool, timeout, and output limits
- a forced timeout prompt that must generate `failure.md`
