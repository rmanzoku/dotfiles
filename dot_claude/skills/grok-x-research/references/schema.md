---
name: grok-x-research-schema
description: Request and response artifact contract for the grok-x-research shared Claude and Codex skill.
---

# Artifact Schema

Use UTF-8 JSON files under `.context/<task>/`.
Prefer stable field names over prompt-only conventions so orchestrators can diff and re-run requests safely.

## Request Artifact

Recommended path: `.context/<task>/grok-request.json`

Required top-level fields:

- `task`: stable task identifier
- `question`: the actual research question for Grok

Optional top-level fields:

- `language`: output language such as `ja` or `en`
- `audience`: target readers for the output
- `context`: supporting background that Grok should consider
- `constraints`: array of limits or cautions
- `deliverable`: object describing desired sections or formatting
- `x_search`: object configuring the built-in X search tool

### Request Example

```json
{
  "task": "ai-agent-x-positioning",
  "question": "日本語圏の技術者に向けて、最近のX上の議論からAIオーケストレーションの論点を整理して。",
  "language": "ja",
  "audience": "日本語圏の技術者",
  "context": [
    "最終的には投稿案の下書きまで欲しい",
    "断定しすぎる表現は避けたい"
  ],
  "constraints": [
    "推測と事実を分ける",
    "URL付きのソースを最低3件示す"
  ],
  "deliverable": {
    "sections": [
      "summary",
      "angles",
      "draft_posts",
      "risks",
      "sources"
    ],
    "max_draft_posts": 3
  },
  "x_search": {
    "allowed_x_handles": [
      "xai",
      "OpenAI",
      "AnthropicAI"
    ],
    "from_date": "2026-04-10",
    "to_date": "2026-04-18",
    "enable_image_understanding": false,
    "enable_video_understanding": false
  }
}
```

### `x_search` Fields

These map to xAI's Responses API `x_search` tool parameters.

- `allowed_x_handles`: optional array, max 10
- `excluded_x_handles`: optional array, max 10
- `from_date`: optional ISO date `YYYY-MM-DD`
- `to_date`: optional ISO date `YYYY-MM-DD`
- `enable_image_understanding`: optional boolean
- `enable_video_understanding`: optional boolean

Do not set `allowed_x_handles` and `excluded_x_handles` together.

## Response Artifact

Recommended path: `.context/<task>/grok-response.json`

Required fields:

- `summary`: string
- `angles`: array of strings
- `draft_posts`: array of strings
- `risks`: array of strings
- `sources`: array of source objects
- `raw_model`: object with response metadata

### Source Object Shape

```json
{
  "title": "string",
  "url": "string",
  "note": "string"
}
```

### Response Notes

- `raw_model.response_id` and `raw_model.model` should be preserved for troubleshooting.
- `raw_model.usage` should be preserved when available.
- `raw_model.citations` may contain extracted annotations from xAI responses when present.
- If Grok cannot support a claim with concrete sources, represent that uncertainty in `risks`.
