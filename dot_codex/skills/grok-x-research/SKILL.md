---
name: grok-x-research
description: Delegate X-focused research, discourse analysis, post-angle discovery, and draft-post generation to Grok through file-based artifacts and the xAI API. Use when Codex should stay as the orchestrator but needs a dedicated Grok pass over recent X context, specific handles, date windows, or pre-post risk checks. This skill is for research delegation only and does not post to X.
---

# Grok X Research

Use this skill to run a bounded Grok research pass and return structured output to the orchestrator.
Keep all handoffs in `.context/` artifacts so the request and response can be re-read across tools and sessions.

## Workflow

1. Read [references/schema.md](./references/schema.md) and create a request artifact at `.context/<task>/grok-request.json`.
2. Run `~/.local/bin/grok_x_research --request <request-path> --response <response-path>`.
3. Read the response artifact, inspect `risks` and `sources`, and integrate the result into the main analysis.
4. Keep final judgment, editing, and any posting decision in the orchestrator. Treat Grok as a specialized X researcher, not the final decider.

## Request Rules

- State the research question explicitly.
- State the intended audience and output language.
- Constrain the X scope with handles or dates when the task is narrow.
- Ask for concrete source URLs whenever the result may feed a post or recommendation.
- Prefer Japanese output unless the surrounding workflow clearly needs another language.
- Keep requests focused on one X research job at a time. Split unrelated questions into separate artifacts.

## Execution Rules

- Require `XAI_API_KEY` in the environment. Premium+ access alone is not enough for API-driven delegation.
- Use `--dry-run` first when checking a new request shape or debugging schema changes.
- Override the model only when you have a reason. The script defaults to `GROK_X_RESEARCH_MODEL` or `grok-4.20-reasoning`.
- Do not bypass `.context/` by inlining large JSON blobs into shell arguments.

## Output Rules

- Expect the response artifact to contain `summary`, `angles`, `draft_posts`, `risks`, `sources`, and `raw_model`.
- Treat `draft_posts` as candidates for review, not ready-to-post content.
- Verify high-stakes claims separately when they affect reputation, compliance, or irreversible actions.
- If Grok returns weak or missing sources, narrow the request and run another pass instead of stretching the interpretation.

## Boundaries

- Do not use this skill for direct X posting.
- Do not use this skill as a generic web research tool when X-native context is not the point.
- Do not expand this flow into MCP unless the file-based workflow becomes a clear bottleneck.

## Resources

- [references/schema.md](./references/schema.md): request and response artifact contract
- shared executable `~/.local/bin/grok_x_research`: xAI API caller with validation, dry-run support, and structured-output parsing
