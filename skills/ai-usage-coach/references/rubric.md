# Rubric

Score each axis from 0 to 10. Do not sum these into a total score. Use the score to choose improvement priorities.

| Axis | Measures | 0 | 5 | 10 |
|---|---|---|---|---|
| Intent | Purpose, desired output, done condition | Vague request | Goal present but success condition weak | Outcome and completion criteria explicit |
| Scope | Target, exclusions, constraints | Scope left implicit | Some boundaries stated | Target, non-targets, constraints clear |
| Decomposition | Task slicing and sequencing | One large ambiguous request | Partial steps | Clear phases or slices with handoff criteria |
| Context | Relevant context selection | Missing or noisy context | Enough to start, some noise | Minimal sufficient context and source paths |
| Skill Use | Existing/new skill judgment | Ignores obvious skills | Uses skills opportunistically | Selects, scopes, or proposes skillization well |
| Tool / Agent Use | CLI, MCP, subagent, runner fit | Wrong or no tools | Tools used but boundaries fuzzy | Tool/agent choice matches evidence and risk |
| Verification | Repro, tests, review, acceptance | No verification | Some check after work | Verification planned before or during work |
| Recovery | Errors, repeated waste, compaction, blocked state | Failures live only in memory/session | Ad hoc retries or one-off notes | Failure reports, waste patterns, and next steps are recoverable |
| Privacy | Secrets, paths, prompt bodies, personal data | Sensitive data exposed | Some redaction | Explicit privacy boundary and scan |
| Learning Loop | Durable learning and reusable rules | Same waste can recur unchanged | One-off note after a failure | Recurring failures update docs, skills, scripts, or rubric |

## Priority Selection

Choose the top 1-3 improvement axes using:

1. Lowest score.
2. Highest leverage for the user's next work.
3. Recurrence across sessions.
4. Safety risk, especially privacy and missing verification.
5. Repeated waste: the same failure, workaround, or investigation has happened before.

For period or cross-repository reviews, choose priorities from concrete hotspots, not from axis scores alone. A hotspot should name the repo/workflow/tool/error class and explain why it is more actionable than a general trend.

## Evidence Confidence

Use confidence separately from the 0-10 axis score:

| Confidence | Meaning |
|---|---|
| `low` | Evidence is sparse, self-reported, mostly textual, or lacks task/tool/verification outcomes. |
| `medium` | Structured aggregate evidence exists, but representative examples, artifact checks, or one important source are missing. |
| `high` | Scores are backed by multiple structured signals plus sampled representative examples or artifact-level checks such as task outcomes, tool outcomes, tests, validation logs, or explicit corrections. |

No score without evidence. If an axis cannot be supported by evidence, mark it unscored or `low` confidence instead of inferring intent, talent, seniority, or personality. Do not mark a broad period review `high` confidence from aggregate counts alone.

## Promotion Candidate Score

Score repeated waste candidates from 0 to 5 on each dimension, then use the total only to choose the recommendation path. Do not present it as a person score.

| Dimension | 0 | 3 | 5 |
|---|---|---|---|
| Recurrence | One-off | Repeated in one repo or period | Repeated across repos, tools, or periods |
| Friction | Minor annoyance | Noticeable time or token waste | Blocks work, causes repeated rework, or hides root causes |
| Risk | Low consequence | Can skip validation or confuse source of truth | Can affect secrets, safety, production behavior, or durable policy |
| Portability | Only one local incident | Useful in one repo or workflow family | Generalizable across repos or agents |
| Future Value | Unlikely to recur | Likely to recur for similar work | High leverage reusable prevention |

Recommended path:

| Total | Recommendation |
|---|---|
| 0-6 | `no-promotion`; leave as a note or ignore. |
| 7-12 | `checklist`, `docs`, or `AGENTS.md` if there is a clear durable home. |
| 13-18 | `script`, `test`, `repo-template`, or evaluator backlog when repeatability or enforcement matters. |
| 19-25 | High-priority promotion candidate. Prefer the smallest durable home first; use `skill` only when the workflow is portable, repeatedly useful, and needs procedural judgment, conditional routing, or bundled resources. |

If score inputs come from summaries rather than counts, logs, artifacts, or evaluator reports, mark the score as estimated and keep confidence below `high`.

Also mark direction:

- `personal`: useful for one user's local workflow or private preferences.
- `repo-local`: belongs in one repository's docs, scripts, tests, or agent guidance.
- `public`: likely reusable outside the local repository and safe to generalize without private context.

## Interpretation Rules

- Score observable behavior, not writing style.
- In FDE-adjacent reviews, score only observable AI usage habits: customer facts vs hypotheses, unknowns, constraints, acceptance checks, verification, privacy boundaries, and learning-loop artifacts. Do not score customer understanding, customer value, stakeholder management, commercial judgment, or FDE capability as a whole from AI logs.
- A short prompt can score high if it has enough intent, scope, and verification for the task.
- A long prompt can score low if it mixes unrelated goals or lacks a testable done condition.
- A session with eventual success can still score low on `Recovery` or `Learning Loop` if the route wasted time and left no durable prevention.
- A session can score high on coaching even when the repository itself needs a separate evaluator; this skill should identify the likely surface and route it, not complete the repository evaluation.
- For repository-lens reviews, prioritize the next evaluator or repo-local durable improvement.
- For cross-repository-lens reviews, prioritize recurring pattern clusters and reusable improvements, while preserving per-repository exceptions.
- If evidence is thin, mark confidence as `low` and recommend a smaller follow-up review.
- Treat underused capabilities as improvement candidates only when evidence shows they would have reduced repeated work, improved verification, or avoided unnecessary fallback paths.
- A report with plausible scores but no concrete hotspot, owner/review path, and verification is low actionability even if its evidence confidence is medium or high.
- A report with only aggregate counts should usually stay at `medium` confidence. Raise to `high` only after sampling representative examples or checking artifacts behind the count.
