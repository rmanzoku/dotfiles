---
name: grok
description: Call Grok through a file-based request and response wrapper. Use when the orchestrator wants a reproducible Grok handoff artifact now, with room to swap the backend from xAI Responses API to a future Grok CLI later.
---

# Grok

Use this skill to call Grok through a thin file-based wrapper.
Keep request and response handoffs in `.context/` so the payload can be re-read across tools and sessions.
This skill does not impose an X-research workflow. It forwards a request artifact to Grok and stores the response artifact.
The current backend is xAI Responses API. If an official Grok CLI becomes usable later, replace the backend while keeping the file-based contract stable.

## Workflow

1. Read [references/schema.md](./references/schema.md) and create a request artifact at `.context/<task>/grok-request.json`.
2. Resolve the installed skill directory from this `SKILL.md`, then run its bundled script: `python3 <skill-dir>/scripts/executable_grok --request <request-path> --response <response-path>`.
3. Read the response artifact and integrate the result in the orchestrator.
4. Keep final judgment, editing, and side effects outside this wrapper. The wrapper only makes the API call and records the response.
5. Do not bypass `.context/` by inlining large JSON blobs into shell arguments.

## Request Rules

- Put the actual xAI Responses API body under the `request` key.
- Prefer `request.input` as a string or a messages array that Grok can consume directly.
- For schema-constrained JSON, put the schema under `request.response_format` and validate the returned `output_text` in the orchestrator.
- Set `request.model` only when the default model is not enough.
- Add tools such as `web_search` or `x_search` only when the task actually needs them.
- Keep one API job per artifact.

## Execution Rules

- Require `XAI_API_KEY` in the environment. Premium+ access alone is not enough for API-driven delegation.
- Use `--dry-run` first when checking a new request shape or debugging schema changes. The CLI still requires `--response`, but dry-run prints the outbound payload and does not write a response artifact.
- The script defaults to `GROK_MODEL`, then `GROK_X_RESEARCH_MODEL`, then `grok-4.20-reasoning` when `request.model` is omitted.
- The bundled script currently calls xAI's `/responses` endpoint and should avoid adding orchestration logic beyond minimal validation and artifact handling.
- If the backend is later swapped to a Grok CLI, preserve the request and response artifact contract unless there is a compelling migration reason.

## Output Rules

- Expect the response artifact to preserve the outbound payload, the raw API response, and extracted convenience fields such as `output_text` when available.
- If you need structured JSON from Grok, request it with `request.response_format` and validate the returned `output_text` in the orchestrator.
- Verify high-stakes claims separately when they affect reputation, compliance, or irreversible actions.

## Boundaries

- Do not use this skill for direct posting or other irreversible side effects.
- Do not expand this flow into MCP unless the file-based workflow becomes a clear bottleneck.

## Resources

- [references/schema.md](./references/schema.md): request and response artifact contract
- bundled script `scripts/executable_grok`: current thin backend wrapper that validates artifacts, sends the request, and writes the raw response artifact

## Validation

```bash
scripts/skill-quick-validate skills/grok
```
