---
name: grok-cli-runner
description: Run Grok handoffs through a CLI-runner style artifact wrapper with observable request and response files, timeouts, model defaults, dry-run support, and artifact-based failure handling. Use when Claude Code or Codex needs to call Grok, GrokをCLIで呼ぶ, use Grok through Hermes/SuperGrok OAuth, inspect or summarize x.com, twitter.com, X/Twitter, tweet, post, thread, quote post, reply, or reaction URLs, invoke a future `grok` CLI, or delegate research, review, generation, or schema-constrained output to Grok while preserving reproducible context task artifacts. Default backend is Hermes Agent xAI OAuth; direct xAI Responses API is available only when explicitly requested.
---

# Grok CLI Runner

Use this skill when delegating work to Grok through a file-based runner contract. The default backend is Hermes Agent with `xai-oauth`, backed by a SuperGrok subscription. Use direct xAI Responses API only when explicitly requested or when the task specifically needs API-key behavior. Keep the request, response, summary, stderr, and failure notes under `.context/<task>/` so the call can be audited and replayed.

Frame each delegation as an outcome-first contract: request artifact, expected response artifact, timeout, success criteria, model defaulting, allowed tools, schema expectations, and failure handling. Keep final judgment, editing, and irreversible side effects in the caller.

This runner has two distinct modes:

- `--retrieval-mode x-raw`: fetch as much raw public data as possible for supplied X URLs and return it to the caller in `x-search-results.json` plus the response artifact. Use this when the caller needs source evidence, quote eligibility, Article/card data, counts, or raw context before deciding how to use it.
- `--retrieval-mode answer`: prepare a Grok final answer for the supplied task using available X and web context. This is the default for backward compatibility.

## Core Rules

- Put every run under `.context/<task>/`.
- Save the Grok request as `.context/<task>/grok-request.json`.
- Do not inline large JSON request bodies into shell arguments.
- Do not ask for per-run approval solely because the call may use API billing, subscription quota, or local Hermes auth/session state.
- Use the wrapper's 600-second process timeout default, or pass an explicit timeout override when the task needs a shorter or longer limit.
- Direct Hermes `x_search_tool` probes use a separate per-query timeout default of 120 seconds; override with `--x-search-timeout-seconds` only when a specific X retrieval needs more or less time.
- After direct X search produces `x-search-results.json`, Hermes final-answer materialization uses a response watchdog default of 180 seconds; override with `--response-watchdog-seconds` or pass `0` to disable.
- Use `--dry-run` for request-shape validation; it does not call the API and intentionally does not create a response artifact.
- In `--dry-run`, `--response-artifact` still records the intended response path, but success is checked through `summary.json.dry_run_payload`; do not require `grok-response.json` to exist for dry-run success.
- Require `XAI_API_KEY` for real direct API calls. SuperGrok access alone is not direct API access.
- Require Hermes Agent setup and `xai-oauth` login for real Hermes calls. `XAI_API_KEY` is not required for this backend.
- Do not treat 0-byte `run.err` or a missing response artifact alone as a hang; use exit code, timeout, summary fields, and failure reasons.
- When the user provides an X-related URL, this skill must be used. X-related URL includes `x.com`, `twitter.com`, `mobile.twitter.com`, X/Twitter post URLs, thread URLs, quote-post URLs, reply URLs, and common X mirrors such as Nitter URLs.
- When the caller needs raw X evidence, use `--retrieval-mode x-raw`; do not infer raw evidence from the default final-answer prose.

## Hermes Setup

Hermes is managed by Homebrew in this dotfiles repo:

```bash
brew install hermes-agent
```

Authenticate Grok through the SuperGrok-backed OAuth provider:

```bash
hermes auth add xai-oauth
```

If the browser cannot open automatically, use:

```bash
hermes auth add xai-oauth --no-browser
```

Useful checks after authentication:

```bash
hermes auth status xai-oauth
hermes --oneshot "Say ok." --provider xai-oauth -m grok-4.3
```

`hermes model` can also be used for the interactive provider/model picker, but the runner passes `--provider xai-oauth` and `-m grok-4.3` per invocation, so global Hermes defaults are not required for this skill.

## X URL Retrieval

When the request contains an X-related URL, build the request so Grok retrieves context before summarizing or answering. Do not answer from URL text alone.

Required retrieval scope:

- Original post text, author display name, handle, timestamp, visible media/alt text, linked cards, X Article/longform text, and quoted post.
- Parent posts and the surrounding thread, including earlier and later posts by the author when available.
- Visible replies, quote posts, repost/reply/like/view counts, and notable reactions or community context when available.
- Any access limitation such as login wall, deleted/protected post, rate limit, dynamic rendering failure, or missing engagement data.

Runner behavior:

- The wrapper detects X-related URLs in `request.input`.
- For Hermes runs, the wrapper calls Hermes `x_search_tool` directly before the one-shot summarization and writes `x-search-results.json` under the output directory.
- During direct X retrieval, the wrapper logs progress to stdout and updates `x-search-results.json` before and after each query with `status`, timestamps, and per-query responses. If a query hangs or times out, use the partially written artifact to identify the last running query.
- In `--retrieval-mode x-raw`, the wrapper skips final-answer synthesis and fails if no X URL is present, direct `x_search_tool` is unavailable, or every direct X query fails.
- In `--retrieval-mode answer`, the wrapper may still succeed when final-answer synthesis succeeds, but callers must not treat that prose as raw source evidence when `x-search-results.json.available=false`.
- When `x-search-results.json.available=false`, inspect `x-search-results.json.diagnostics` before retrying. It records Hermes auth status, selected site-packages path, import errors, credential provider, credential presence, `HOME`, `HERMES_HOME`, and `HERMES_PROFILE` so subprocess environment drift is visible. If `check_x_search_requirements()` is false but `hermes auth status xai-oauth` reports logged in, the runner still attempts direct `x_search_tool` calls and records that reason in diagnostics.
- Treat `x-search-results.json` as the primary artifact for post text, Article/card details, media metadata, and engagement counts because it preserves the direct `x_search_tool` JSON response instead of only the model's final prose.
- Use `x-search-results.json.representative_engagement` as the default count source when present. It is selected from the first structured `exact_url_full` result. Later `thread_context` or `reaction_search` answers may show different view counts because engagement changes over time; mention that drift when it matters.
- Treat engagement counts as a time-varying snapshot from the retrieval run, not durable truth. When reporting counts, preserve the artifact and mention snapshot drift if exactness matters.
- For reactions, prefer a compact list of the top 3-5 notable replies, quote posts, or community reactions when available, plus a limitation statement when only aggregate counts are visible.
- When count fields and surfaced items disagree, keep the count from `representative_engagement` as the primary count and report surfaced items as partial examples from the relevant query. Example: "quote_count=1, but concrete quote post details were only surfaced by `reaction_search`" or "count indicates quotes exist, but no quote post items were returned."
- In the final prose, include concrete surfaced items from any successful query (`exact_url_full`, `article_card_context`, `thread_context`, or `reaction_search`) when they are relevant. Label the source query when another query's structured list is empty, instead of discarding the item.
- Classify surrounding posts by relationship evidence: reply-to metadata is a parent, embedded quoted content is a quoted post, same-author nearby posts without reply/quote evidence are thread or surrounding author context. If Hermes output is ambiguous, say which relationship is inferred and why.
- For a generic "content and reactions" request, default to a concise report with: post summary, engagement snapshot, thread/quote/reply context, top 3-5 notable reactions when available, and retrieval limitations.
- For Hermes runs, it injects explicit X retrieval instructions into the one-shot prompt.
- For Hermes runs, it also injects a compact version of `x-search-results.json` into the one-shot prompt so final summaries can include counts reliably.
- For Hermes runs with X URLs, it automatically enables `web,browser,x_search` toolsets for that invocation unless already included.
- If Grok cannot retrieve the full post, Article/card content, thread, or reactions, the caller should report the limitation and preserve the partial evidence in the final answer.

## Caller Checklist

Before running Grok, make these decisions explicitly:

- Task directory: choose `.context/<task>/`.
- Request artifact: write `.context/<task>/grok-request.json` with top-level `task` and `request`.
- Response artifact: pass `--response-artifact grok-response.json` when the response belongs inside `--output-dir`; use an absolute `--response-artifact` path when the response must be written outside `--output-dir`, such as inside a target repository.
- Retrieval mode: use `--retrieval-mode x-raw` for source collection and `--retrieval-mode answer` for Grok-authored analysis or synthesis.
- Backend: default to `--backend hermes`; pass `--backend xai-api` only when direct API-key billing is explicitly intended.
- Model: omit `--model` unless the caller, model registry, or role explicitly requires an override. The wrapper defaults to `GROK_MODEL`, then `GROK_X_RESEARCH_MODEL`, then `grok-4.3`.
- Timeout: rely on the 600-second wrapper default unless the task contract says otherwise. The HTTP timeout defaults to the same value unless `--http-timeout-seconds` is provided.
- Direct X search timeout: rely on the 120-second per-query default unless the task specifically requires a different limit.
- Hermes final-response watchdog: rely on the 180-second default after direct X search, or pass `--response-watchdog-seconds` when a long final synthesis is explicitly worth waiting for.
- Tools: include `web_search`, `x_search`, or other xAI tools in `request.tools` only when the task needs them; set explicit limits in the prompt/request text when doing research. For Hermes backend, pass `--hermes-toolsets <csv>` only when Hermes toolsets are already configured and the task needs them.
- Structured output: put schema constraints under `request.response_format`, then validate `output_text` in the caller.
- Expected artifacts: if the target artifact is the Grok response itself, make it `--response-artifact`; if other files must be created by the caller after reading Grok output, track those outside this wrapper because this wrapper only guarantees the response artifact.
- Working directory: `--cwd` controls the backend process working directory. It is not a substitute for the shell's current directory when resolving the wrapper's `--request-file` or `--output-dir` arguments.
- Workflow validation: after model-default changes, run at least one no-call validation and, when credentials are available, a short real call before relying on the new default for long sequential tool workflows.

Do not add "think hard", fixed progress-update scaffolds, or mandatory step-by-step narration to simulate model effort. Use model selection, request fields, and explicit success criteria instead.

## Standard Command Shape

For subscription-backed runs through Hermes/SuperGrok OAuth, use:

```bash
python3 <skill-dir>/scripts/run_grok_cli.py \
  --request-file .context/<task>/grok-request.json \
  --output-dir .context/<task> \
  --response-artifact grok-response.json \
  --backend hermes
```

This calls `hermes --oneshot` with `--provider xai-oauth` by default and normalizes the final stdout into `grok-response.json`.

For raw X URL retrieval, use:

```bash
python3 <skill-dir>/scripts/run_grok_cli.py \
  --request-file .context/<task>/grok-request.json \
  --output-dir .context/<task> \
  --response-artifact grok-response.json \
  --backend hermes \
  --retrieval-mode x-raw
```

This writes `x-search-results.json`, embeds the raw retrieval object in `grok-response.json`, and does not ask Hermes for final prose.

For explicitly requested direct xAI API runs, use:

```bash
python3 <skill-dir>/scripts/run_grok_cli.py \
  --request-file .context/<task>/grok-request.json \
  --output-dir .context/<task> \
  --response-artifact grok-response.json \
  --backend xai-api
```

Add `--model <model>` only when overriding environment/config defaults.
Add `--timeout-seconds <seconds>` only when overriding the 600-second process timeout.
Add `--http-timeout-seconds <seconds>` only when the HTTP request needs a different timeout from the process guard.
Add `--x-search-timeout-seconds <seconds>` only when overriding the direct Hermes X-search per-query timeout.
Add `--response-watchdog-seconds <seconds>` only when overriding the Hermes final-response watchdog after direct X search.
Add `--hermes-provider <provider>` only when overriding the Hermes provider from `xai-oauth`.
Add `--hermes-bin <path>` only when the Hermes executable is not on `PATH`.

The wrapper writes:

- `grok-request.json`: caller-authored request artifact
- `x-search-results.json`: direct Hermes `x_search_tool` result artifact when X URLs are detected
- stdout progress lines: direct X retrieval start, each query start/finish, and completion/unavailable status
- resolved response artifact, normally `grok-response.json`: normalized response artifact for real successful calls; in `x-raw` mode this wraps the raw X retrieval instead of final prose
- `run.err`: stderr and local wrapper diagnostics
- `summary.json`: command, resolved `cwd`, exit code, elapsed time, byte counts, model, backend, dry-run flag, detected X URLs, effective Hermes toolsets, produced X search artifact path, response artifact path/status, `failure_reasons`, and `recommended_next_action`
- If Hermes final-answer synthesis exceeds the response watchdog after direct X search, `summary.json.failure_reasons` includes `hermes_response_watchdog_timeout`.
- `failure.md`: only when the wrapper run fails

For request-shape validation without API spend:

```bash
python3 <skill-dir>/scripts/run_grok_cli.py \
  --request-file .context/<task>/grok-request.json \
  --output-dir .context/<task> \
  --response-artifact grok-response.json \
  --dry-run
```

## Request Contract

Read `references/schema.md` when creating or validating request/response artifacts.

Required request artifact fields:

- `task`: stable task identifier
- `request`: Responses-style object normalized by the wrapper. The default Hermes backend converts it into a `hermes --oneshot` prompt; explicit `--backend xai-api` sends it to xAI's `/responses` endpoint.

Important request rules:

- `request.input` is required.
- `request.model` is optional; wrapper model defaulting fills it when omitted.
- `request.instructions` is rejected because xAI Responses API does not support it in this wrapper.
- `meta` is optional and stays local; it is not sent to xAI.
- Keep one backend job per request artifact.

## Success Criteria

Require all applicable checks:

- Process exit code is `0`.
- For real runs, the resolved response artifact exists and is non-empty.
- Response artifact contains `request`, `response`, `model`, and either `output_text` or a raw `response` object sufficient for the caller to inspect.
- `summary.json.success` is `true`, `summary.json.failure_reasons` is empty, and `summary.json.response_non_empty` is `true`.
- For `--retrieval-mode x-raw`, `x-search-results.json.available=true` and `summary.json.x_search_successful_query_count > 0`.
- For `--dry-run`, success means the outbound payload validated and was written to `summary.json.dry_run_payload`; no response artifact is expected.

These checks prove runner execution and non-empty response materialization only. The caller must still evaluate task-specific response quality against the request artifact.

## Failure Criteria

Treat any of these as failure:

- Timeout exit, normally exit code `124`.
- Non-zero process exit.
- Missing or invalid request artifact.
- Missing `request.input`.
- Missing `XAI_API_KEY` on a real direct API call.
- Missing `hermes` executable, missing Hermes `xai-oauth` login, or Hermes provider/model/toolset errors on a real Hermes call.
- `missing_hermes` in `summary.json.failure_reasons` means the Homebrew `hermes-agent` formula is missing or `--hermes-bin` points to the wrong executable.
- HTTP/API authentication, model, permission, policy, or rate-limit errors.
- Real run response artifact is missing or empty.
- In `--retrieval-mode x-raw`, missing X URLs, unavailable direct `x_search_tool`, or zero successful direct X queries.

On failure, inspect `.context/<task>/summary.json` first:

- `command`
- `cwd`
- `exit_code`
- `elapsed_seconds`
- `request_bytes`, `response_bytes`, and `stderr_bytes`
- `model`
- `x_urls_detected`
- `hermes_toolsets`
- `x_search_results_artifact`
- `x_search_available` and `x_search_successful_query_count`
- `x_search_timeout_seconds`
- `response_watchdog_seconds` and `hermes_final_timeout_seconds`
- `x-search-results.json.diagnostics` when direct X search is unavailable
- `dry_run`
- `failure_reasons`
- `api_error`
- `response_artifact`
- `response_non_empty`
- `recommended_next_action`

If a higher-level workflow needs a downstream blocked artifact, create it in the caller using that workflow's schema or template. Do not invent a downstream schema in this runner and do not modify runner evidence artifacts. If no caller schema was supplied, report the runner as blocked with links to `summary.json` and `failure.md` instead of fabricating an artifact format.

The wrapper also writes `.context/<task>/failure.md` with:

- executed command
- exit code
- elapsed time
- request/response/stderr sizes
- API or validation error
- response artifact status
- recommended next action

## No-Call Validation

Use these patterns when testing the wrapper itself without making a backend call:

- Run `--dry-run` with a valid request artifact. It should exit `0`, write `summary.json`, and not require `XAI_API_KEY`.
- Run with an invalid request artifact to confirm `failure.md` and `summary.json.failure_reasons` are generated.
- Run a dry-run or direct helper-level check with an X URL request to confirm prompt conversion includes X retrieval requirements.
- Run `--retrieval-mode x-raw` with a real X URL and confirm `summary.json.x_search_successful_query_count > 0`.
- For any real X smoke, confirm stdout emits progress and `x-search-results.json` appears before the first direct query finishes.
- Run a real Hermes X URL smoke when credentials are available and confirm `x-search-results.json` is written with `credential_source: xai-oauth`, `available=true`, Article/card fields when present, and visible engagement counts when xAI returns them.
- Run with a fake backend script via `--backend-script <path>` only for controlled tests. Do not use fake backend scripts for real Grok delegation.
- Do not hand-edit `summary.json`, `run.err`, the response artifact, or `failure.md`. If a controlled test needs explanation, write a separate `notes.md`.

## Wrapper Notes

- Resolve `<skill-dir>` from the location of this `SKILL.md`.
- Pass `--cwd <project-root>` when the caller wants the backend process launched from a specific repository.
- `summary.json.cwd` records the resolved `--cwd`; inspect that field for backend cwd because `summary.json.command` does not include `--cwd`, and the shell directory that launched the wrapper is not recorded as a separate field.
- Omit `--model` by default so environment/model registry defaults apply.
- Pass `--base-url` only when targeting a non-default xAI-compatible endpoint.
- Pass `--backend hermes` or omit `--backend` to use Hermes Agent's `xai-oauth` provider and SuperGrok subscription quota.
- Pass `--backend xai-api` only to force direct xAI Responses API behavior.
- If Hermes is missing, install the Homebrew formula `hermes-agent`; do not install the unrelated `hermes` cask.
- Keep final orchestration in the caller. This skill only calls Grok and records observable artifacts.
- If an official Grok CLI becomes available later, preserve this `.context/<task>/` contract unless there is a compelling migration reason.

## Validation

Validate the skill and wrapper after changes:

```bash
scripts/skill-quick-validate skills/grok-cli-runner
python3 <skill-dir>/scripts/run_grok_cli.py --help
```

For runtime validation, run:

- no-call dry-run success
- invalid request failure
- X URL prompt conversion and automatic `web,browser,x_search` toolset behavior
- X URL direct `x-search-results.json` artifact behavior
- optional real Hermes smoke when Hermes is logged in
- optional real API smoke when direct API behavior is needed
- representative long-tool workflow smoke before using a new default model for production-like delegation
