---
name: ai-usage-coach
description: Evaluate and coach a human's AI work-delegation practice across prompts, context scoping, skill use, tool/subagent selection, verification, failure/waste recovery, privacy, learning loops, structured session signals, underused capabilities, and routing from observed AI failures to prompt, docs, code, orchestration, tooling, workflow, or durable-instruction improvements. Use when asked to review Claude/Codex usage, repeated AI mistakes, prompt habits, AI session logs, skill usage patterns, repository-specific AI friction, cross-repository AI workflow patterns, reusable improvement candidates, weekly/monthly AI usage, or "how should I use AI better"; supports trusted-local raw-log review and shareable abstracted reports. Do not use for HR/personnel evaluation, personality assessment, repository-quality evaluation, final technical philosophy judgment, or ranking people against a teacher.
---

# AI Usage Coach

Evaluate how a human delegates work to AI and return axis-level coaching. Score behaviors, not people. Use the teacher profile to suggest "teacher moves"; do not score users by similarity to the teacher.

This skill is a diagnostic and routing layer. It identifies why AI collaboration struggled and where the next improvement likely belongs. It does not replace repository evaluators, code review, documentation review, orchestration review, or final technical judgment.

## Mode Decision

Choose the narrowest mode before reading inputs:

| Mode | Use when | Raw excerpts | Output |
|---|---|---|---|
| `trusted-local` | User reviews their own local raw Claude/Codex logs or transcripts on the same machine. | Allowed, minimal only. | `.context/ai-usage-coach/<task>/`, `shareable: false`. |
| `shareable` | Output may be committed, posted, sent to others, or used in a meeting. | Prohibited. | User-chosen report path after privacy scan. |
| `teacher-pack` | Creating reusable teaching material from teacher patterns. | Prohibited. | Synthetic examples, rubric, archetypes, teacher moves. |

If the user does not specify a mode and raw logs are involved, default to `trusted-local` and state that the report is not shareable. If the user wants a shareable report, do not include raw excerpts.

## Review Lens

Choose one lens in addition to the mode:

| Lens | Use when | Focus |
|---|---|---|
| `repository` | Reviewing AI work in one repository or one repo-local incident. | Repo-specific friction, missing entrypoints, local tooling gaps, evaluator routing, durable repo instructions. |
| `cross-repository` | Reviewing repeated patterns across multiple repositories, clients, workstreams, or a time period. | Portfolio-level habits, repeated waste classes, reusable skills/scripts/checklists, global instruction candidates, evaluator backlog themes. |

If both lenses apply, report them separately. Do not let cross-repository patterns override repo-specific evidence; use cross-repository observations to propose reusable improvements or review backlogs.

## Workflow

1. **Confirm scope**
   - Identify whether this is a `session_review` or `period_review`.
   - Identify whether the lens is `repository`, `cross-repository`, or both.
   - Identify input paths or pasted text.
   - Record mode, lens, source type, repositories or workstreams covered, exclusions, and shareability.

2. **Read only what the mode permits**
   - In `trusted-local`, raw logs may be read.
   - In `shareable` and `teacher-pack`, raw prompt/response excerpts must not be copied into the report.
   - Do not read ignored secret files unless explicitly needed and permitted by the user.

3. **Score axes and repeated waste**
   - Read `references/rubric.md`.
   - Score each axis 0-4.
   - Do not calculate a total score.
   - Prefer structured signals over transcript impressions: task outcome, aborted turns, tool errors, patch/apply results, repeated retries, validation commands, missing checks, artifacts created, and explicit user corrections.
   - Treat keyword counts, prompt length, tool count, and tone as secondary clues only.
   - Do not assign a score without evidence; if evidence is thin, mark confidence as `low` and narrow the recommendation.
   - Explicitly identify repeated failures, repeated dead ends, and repeated manual recovery work that only live in memory or session history.
   - Classify each important failure under one or more improvement surfaces: `prompt`, `context`, `skill`, `orchestration`, `docs`, `code`, `tooling`, `workflow`, `durable instructions`, `local environment`, or `underused capability`.
   - Mark evidence as behavior-level unless `trusted-local` raw excerpts are explicitly useful.

4. **Route repository-side concerns**
   - Treat repository-side conclusions as hypotheses, not final evaluation findings.
   - For orchestration, resolver, subagent, runner, or fallback-boundary concerns, recommend `agent-orchestration-evaluator` or the repository's equivalent orchestration review path.
   - For documentation reachability, source-of-truth, stale docs, or agent-readable guidance concerns, recommend `docs-evaluator` or the repository's equivalent docs review path.
   - For architecture, tests, dependencies, implementation quality, security hygiene, or broad code health concerns, recommend `code-evaluator` or the repository's equivalent code review path.
   - If no public evaluator or repo-local review path is available, record that as a gap instead of naming a specific unavailable agent.

5. **Synthesize cross-repository patterns when requested**
   - Cluster recurring failures across repositories by improvement surface, not by person or repository blame.
   - Separate per-repository fixes from reusable improvements such as shared skills, runner hardening, global instructions, repo templates, checklists, scripts, or evaluator backlog items.
   - Mark whether each pattern is `single-repo`, `multi-repo`, or `global`.
   - Score reusable improvement candidates with the promotion rubric in `references/rubric.md`: recurrence, friction, risk, portability, and future value.
   - Recommend the smallest durable home that matches the evidence: `skill`, `AGENTS.md`, `docs`, `script`, `test`, `checklist`, `evaluator-backlog`, `local-state`, or `no-promotion`.
   - Treat promotion score as triage evidence, not as an instruction to create a skill. Choose `skill` only when the reusable improvement needs procedural judgment, conditional workflow, or bundled resources beyond a simpler durable home.
   - If score inputs come from summaries rather than counts, logs, or artifacts, label the score as estimated and keep confidence below `high`.
   - Mark whether the candidate is `personal`, `repo-local`, or `public` before recommending where it should live.
   - Do not prescribe a universal repo standard from one repository's evidence.

6. **Apply teacher moves**
   - Read `references/teacher-moves.md`.
   - Read `references/teacher-profile.md` and `references/teacher-patterns.md` when the user asks "teacher would do what?" or when recommending next behavior.
   - Read `references/teacher-archetypes.md` for period reviews or style classification.
   - Read `references/teacher-baseline.md` when comparing a period review against the teacher's observed abstract baseline.
   - For the top 1-3 improvement axes, add "teacher would do this" guidance.
   - Make the move concrete enough to use in the next prompt or workflow.

7. **Format output**
   - Read `references/output-schema.md`.
   - Include `mode`, `lens`, `shareable`, input scope, evidence coverage, confidence, axis scores, priority improvements, improvement surfaces, promotion candidates, recommended review paths, teacher moves, and warnings.
   - In period review, include recurring gaps, improved axes, and next focus.
   - For cross-repository reviews, include cross-repo patterns, reusable improvement candidates, and per-repo follow-up candidates.

8. **Run privacy scan**
   - For any saved report, run `scripts/privacy_scan.py <path> --mode <mode>`.
   - In `shareable` and `teacher-pack`, privacy scan must pass before final delivery.
   - In `trusted-local`, still run the scan and report any warnings.

## Evidence Rules

- Prefer behavior evidence: "success condition was missing", "verification command was absent", "skill was invoked after manual exploration".
- Prefer artifact-backed and structured evidence over self-report: diffs, docs, tests, validation logs, task outcomes, tool outcomes, review comments, and redacted summaries.
- No score without evidence. If an axis has insufficient evidence, leave it unscored or mark confidence as `low` instead of filling gaps with personality or intent guesses.
- Treat repeated failures and repeated wasted work as first-class evidence. If the same failure, workaround, or investigation recurs, recommend promotion into docs, a skill, a script, or a reusable checklist.
- Do not conclude that a repository is poorly documented, poorly architected, or poorly orchestrated solely from a session log. Report the observed friction and recommend the appropriate evaluator or review path.
- In cross-repository reviews, do not flatten local context. Keep repository-specific evidence separate from cross-repo patterns.
- In `trusted-local`, raw excerpts are allowed only when they materially improve coaching and are kept short.
- Never include secrets, access tokens, emails, absolute paths, full prompt bodies, system prompts, or long JSON message bodies in final output.
- If raw excerpt evidence conflicts with privacy, drop the excerpt and keep the behavior-level diagnosis.

## Output Principles

- Do not evaluate personality, talent, seniority, or work ethic.
- Do not produce a total score or ranking.
- Do not say "closer to teacher is better".
- Do say "in this situation, the teacher move would be..."
- Prioritize the next 1-3 actionable improvements over exhaustive critique.
- Prefer routing language such as "docs review likely needed" or "orchestration review candidate" over final repository judgments.
- Watch for anti-rationalization red flags: all axes scored high without evidence, vague action items, impressive AI output accepted without verification, repeated failures explained away as one-offs, or recommendations that cannot be checked in the next session.

## Delegation Boundaries

- Do not assume a specific reviewer agent exists, and do not require delegation to non-standard agents.
- Do not make final technical philosophy or repository-quality judgments inside this skill.
- When evidence suggests a repository-side issue, classify the suspected repo-side surface: `orchestration`, `docs`, `code`, `tooling`, `workflow`, or `durable instructions`. Keep behavior-side surfaces such as `prompt`, `context`, `skill`, `privacy`, or `underused capability` in the coaching report instead of routing them as repository defects.
- Recommend the relevant public evaluator or repository-local review path when available; otherwise state the missing review path as a gap.

## References

- `references/rubric.md`: scoring axes and 0-4 anchors.
- `references/teacher-moves.md`: teacher-style interventions by weak axis.
- `references/teacher-profile.md`: teacher-pack v0 principles and non-goals.
- `references/teacher-baseline.md`: abstract local-log signal baseline; no raw excerpts.
- `references/teacher-archetypes.md`: reusable work-delegation archetypes.
- `references/teacher-patterns.md`: concrete teacher behavior patterns.
- `references/teacher-examples.md`: synthetic scored examples; no real logs.
- `references/output-schema.md`: report schemas.
- `references/modes.md`: mode contracts and shareability.
- `references/privacy-policy.md`: raw excerpt and privacy rules.
