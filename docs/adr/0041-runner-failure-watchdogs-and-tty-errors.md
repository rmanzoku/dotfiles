---
title: Runner failures record watchdog and noninteractive TTY causes
status: accepted
date: 2026-06-04
agent_model: Codex GPT-5
---

# Runner failures record watchdog and noninteractive TTY causes

## Context

`review-manuscript` runs exposed two runner reliability failures before manuscript review quality could be evaluated:

- Gemini CLI sometimes emitted `setRawMode EIO` or `setRawMode EBADF` during noninteractive `gemini -p` runs.
- Grok through Hermes could complete direct X search and write `x-search-results.json`, then stall before materializing the final response artifact.

## Decision

- `gemini-cli-runner` classifies `setRawMode EIO` and `setRawMode EBADF` as `raw_mode_tty_error` and runs Gemini with `stdin=DEVNULL`.
- `grok-cli-runner` keeps direct X-search progress artifacts and adds a 180-second default final-response watchdog after direct X search. The watchdog can be overridden with `--response-watchdog-seconds` or disabled with `0`.
- Both runner summaries expose enough failure reason data for callers to materialize blocked downstream artifacts instead of waiting for manual process cleanup.

## Consequences

- Runner failures remain observable in `.context/<task>/summary.json` and `failure.md`.
- Callers can distinguish runner availability failures from task quality findings.
- Long Grok final synthesis after X retrieval may be cut earlier than the process timeout unless a caller explicitly opts into a longer watchdog.

## Verification

```bash
python3 -m py_compile skills/gemini-cli-runner/scripts/run_gemini_cli.py
python3 -m py_compile skills/grok-cli-runner/scripts/run_grok_cli.py
scripts/skill-quick-validate skills/gemini-cli-runner
scripts/skill-quick-validate skills/grok-cli-runner
```
