---
name: grok-x-research
description: Delegate X-focused research, discourse analysis, post-angle discovery, and draft-post generation to Grok through file-based artifacts and the xAI API. Use when the orchestrator should stay in control but needs a dedicated Grok pass over recent X context, specific handles, date windows, or pre-post risk checks. This skill is for research delegation only and does not post to X.
---

# Grok X Research

Use this skill to run a bounded Grok research pass through the xAI Responses API and return structured output to the orchestrator.
This skill delegates to a Grok model first; X search is only the built-in evidence-gathering tool that Grok may use during that run.
Keep all handoffs in `.context/` artifacts so the request and response can be re-read across tools and sessions.

## Workflow

1. Read [references/schema.md](./references/schema.md) and create a request artifact at `.context/<task>/grok-request.json`.
2. Resolve the installed skill directory from this `SKILL.md`, then run its bundled script: `python3 <skill-dir>/scripts/executable_grok_x_research --request <request-path> --response <response-path>`.
3. Read the response artifact, inspect `risks` and `sources`, and integrate the result into the main analysis.
4. Keep final judgment, editing, and any posting decision in the orchestrator. Treat Grok as a specialized X researcher, not the final decider.
5. Do not replace this flow with direct `web`/CLI X search unless the bundled script is unavailable and you explicitly report that fallback.

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
- The bundled script must call a Grok model through xAI's Responses API. `x_search` is a tool inside that Grok run, not a substitute for the model call itself.
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
- bundled script `scripts/executable_grok_x_research`: xAI Responses API caller that invokes a Grok model, enables `x_search` as a tool, validates artifacts, and parses structured output

## Validation

```bash
python3 /Users/rmanzoku/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
  skills/grok-x-research
```
