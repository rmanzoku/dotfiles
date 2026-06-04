---
title: Separate runner materialization from task quality
status: accepted
date: 2026-06-04
agent_model: Codex GPT-5
---

# Separate runner materialization from task quality

## Context

The CLI runner skills for Codex, Claude, Gemini, and Grok are used as observable subprocess wrappers. Empirical prompt tuning on 2026-06-04 showed repeated ambiguity around three boundaries:

- whether a successful wrapper run proves the delegated task's content quality;
- how to pass artifact paths when a caller writes runner artifacts in one directory but expects output in another repository;
- how callers should inspect cwd and artifact materialization details after failures.

## Decision

- Runner success means process execution and non-empty artifact materialization only. The caller must still evaluate artifact quality against the source prompt or request artifact.
- For Codex, Claude, and Gemini, `--expected-artifact` is a verification input. If the expected artifact path is absolute, the same absolute path must also be written into the source prompt.
- For Grok, the response artifact itself belongs in `--response-artifact`; downstream files created after reading Grok output stay caller-owned.
- Artifacts outside `--output-dir` use absolute paths.
- Runner summaries must document cwd semantics:
  - Codex and Claude record resolved `--cwd` as `summary.json.cwd`.
  - Gemini records `target_cwd` and `process_cwd`.
  - Grok records resolved backend cwd as `summary.json.cwd`; `summary.json.command` does not include `--cwd`.
- Higher-level blocked artifacts are created by the caller using that workflow's schema or template. Runner evidence artifacts are not hand-edited.

## Consequences

- Callers can distinguish runner availability/materialization failures from delegated task quality failures.
- Cross-repository runner calls no longer rely on implicit relative path interpretation.
- Failure triage starts from `summary.json`, then uses `failure.md` and raw logs as evidence.
- Grok failure notes now include response artifact path and non-empty status directly.

## Verification

```bash
scripts/skill-quick-validate skills/codex-cli-runner
scripts/skill-quick-validate skills/claude-cli-runner
scripts/skill-quick-validate skills/gemini-cli-runner
scripts/skill-quick-validate skills/grok-cli-runner
python3 -m py_compile skills/codex-cli-runner/scripts/run_codex_cli.py skills/claude-cli-runner/scripts/run_claude_cli.py skills/gemini-cli-runner/scripts/run_gemini_cli.py skills/grok-cli-runner/scripts/run_grok_cli.py
```
