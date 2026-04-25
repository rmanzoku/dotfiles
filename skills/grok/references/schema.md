---
name: grok-schema
description: Request and response artifact contract for the grok publisher skill.
---

# Artifact Schema

Use UTF-8 JSON files under `.context/<task>/`.
Prefer stable field names over prompt-only conventions so orchestrators can diff and re-run requests safely.

## Request Artifact

Recommended path: `.context/<task>/grok-request.json`

Required top-level fields:

- `task`: stable task identifier
- `request`: object sent to xAI's `/responses` endpoint after minimal defaulting

Optional top-level fields:

- `meta`: object for local orchestration notes that should not be sent to xAI

### Request Example

```json
{
  "task": "grok-api-summarize-release-notes",
  "request": {
    "model": "grok-4.20-reasoning",
    "input": [
      {
        "role": "system",
        "content": "You summarize technical changes tersely."
      },
      {
        "role": "user",
        "content": "次の更新内容を 5 行で要約して: ..."
      }
    ],
    "tools": [
      {
        "type": "web_search"
      }
    ],
    "response_format": {
      "type": "json_schema",
      "json_schema": {
        "name": "summary",
        "schema": {
          "type": "object",
          "properties": {
            "summary": {
              "type": "string"
            }
          },
          "required": [
            "summary"
          ],
          "additionalProperties": false
        }
      }
    }
  },
  "meta": {
    "purpose": "release note draft"
  }
}
```

### Request Notes

- `request` is passed through almost as-is. Use official xAI Responses API fields and shapes inside it.
- If `request.model` is omitted, the wrapper fills it from `GROK_MODEL`, then `GROK_X_RESEARCH_MODEL`, then `grok-4.20-reasoning`.
- `request.input` is required by the wrapper because it is required by xAI Responses API calls.
- For schema-constrained JSON, use `request.response_format`; the wrapper passes it through and does not validate returned JSON.
- `meta` stays local in the artifact and is never sent to xAI.

## Response Artifact

Recommended path: `.context/<task>/grok-response.json`

Required fields:

- `task`: copied from the request artifact
- `created_at`: UTC timestamp for the wrapper run
- `request`: normalized payload actually sent to xAI
- `response`: raw xAI API response object
- `output_text`: extracted text when xAI returns one
- `response_id`: copied from `response.id` when present
- `model`: copied from `response.model` when present, otherwise from `request.model`

### Response Notes

- `output_text` may be `null` when the response does not contain plain text output.
- The wrapper does not attempt to coerce structured output beyond extracting `output_text`.
- If you request schema-constrained JSON with `request.response_format`, parse `output_text` in the orchestrator and handle validation there.
