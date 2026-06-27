---
name: grok-cli-runner-schema
description: Request and response artifact contract for the grok-cli-runner skill.
---

# Artifact Schema

Use UTF-8 JSON files under `.context/<task>/`.
Prefer stable field names over prompt-only conventions so orchestrators can diff and re-run requests safely.

## Request Artifact

Recommended path: `.context/<task>/grok-request.json`

Required top-level fields:

- `task`: stable task identifier
- `request`: object normalized by the wrapper into a Grok Build headless prompt

Optional top-level fields:

- `meta`: object for local orchestration notes

### Request Example

```json
{
  "task": "grok-build-review-diff",
  "request": {
    "model": "grok-build",
    "input": [
      {
        "role": "system",
        "content": "You review code changes tersely and prioritize bugs."
      },
      {
        "role": "user",
        "content": "Review the staged diff and return the top risks."
      }
    ],
    "response_format": {
      "type": "json_schema",
      "json_schema": {
        "name": "review",
        "schema": {
          "type": "object",
          "properties": {
            "findings": {
              "type": "array",
              "items": {
                "type": "string"
              }
            }
          },
          "required": [
            "findings"
          ],
          "additionalProperties": false
        }
      }
    }
  },
  "meta": {
    "purpose": "review handoff"
  }
}
```

### Request Notes

- The wrapper resolves the model from `--model`, then `request.model`, then `GROK_BUILD_MODEL`, then `GROK_MODEL`, then `grok-build`.
- `request.input` is required.
- `request.input` may be a string or a list of role/content objects.
- `request.instructions` is rejected; put instruction text in `request.input`.
- `request.response_format` is included in the prompt as an additional request field. The wrapper does not validate returned JSON.
- `meta` stays local in the artifact and is copied into the response artifact.

## Response Artifact

Recommended path: `.context/<task>/grok-response.json`

Required fields:

- `task`: copied from the request artifact
- `created_at`: UTC timestamp for the wrapper run
- `meta`: copied from the request artifact when present
- `request`: normalized payload used to build the Grok Build prompt
- `response`: normalized Grok Build CLI response metadata
- `output_text`: extracted final response text when available
- `response_id`: always `null` unless Grok Build exposes a stable response id in a future output shape
- `model`: copied from `request.model`
- `backend`: `grok-build`

### Response Notes

- The wrapper calls Grok Build with `--output-format json` by default and stores parsed stdout under `response.parsed_stdout`.
- If stdout is not valid JSON, `response.parsed_stdout.type` is `unparsed_json_stdout` and `output_text` contains the raw stdout text.
- With `--output-format streaming-json`, `response.parsed_stdout.events` contains one parsed object or `unparsed_line` object per stdout line.
- With `--output-format plain`, `response.parsed_stdout.text` and `output_text` contain the raw plain text.
- `output_text` may be `null` when Grok Build exits successfully without stdout text; callers should still treat a missing useful answer as a task-quality failure even if runner execution succeeded.
- If you request schema-constrained JSON with `request.response_format`, parse `output_text` in the orchestrator and handle validation there.

## Summary Artifact

Recommended path: `.context/<task>/summary.json`

Important fields:

- `command`: redacted command list with the prompt body replaced by `<prompt from request artifact>`
- `cwd`: resolved working directory passed to Grok Build
- `request_file`, `response_artifact`, `output_dir`
- `model`
- `backend`: `grok-build`
- `grok_bin`
- `output_format`
- `permission_mode`
- `no_plan`
- `verbatim`
- `session_id`, `resume`, `continue_session`, `always_approve`
- `dry_run`
- `dry_run_payload`: present only for dry-run success and includes the normalized request, prompt byte count, and redacted command
- `prompt_bytes`
- `exit_code`
- `elapsed_seconds`
- `request_bytes`, `response_bytes`, `stderr_bytes`
- `response_non_empty`
- `api_error`
- `success`
- `failure_reasons`
- `recommended_next_action`
