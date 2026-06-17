# Output Schema

Use Markdown for human-facing reports. Include a YAML summary block when the user wants machine-readable output.

## Session Review

```yaml
mode: trusted-local
lens: repository
shareable: false
subject: session
source:
  kind: claude_jsonl|codex_jsonl|transcript|report|unknown
  scope: local-only
repository_scope:
  kind: single-repository
  repositories: 1
evidence_coverage:
  confidence: low|medium|high
  structured_signals:
    - task_outcome
    - tool_errors
    - verification_commands
  excluded:
    - raw_prompt_bodies
  confidence_reason: "Scores are based on observed outcomes and validation gaps."
scores:
  intent: 0
  scope: 0
  decomposition: 0
  context: 0
  skill_use: 0
  tool_agent_use: 0
  verification: 0
  recovery: 0
  privacy: 0
  learning_loop: 0
priority_improvements:
  - axis: verification
    reason: "High leverage and repeatedly missing."
improvement_surfaces:
  - surface: docs
    hypothesis: "The agent could not find the canonical setup or verification path."
    evidence_kind: behavior-level
recommended_review_paths:
  - surface: docs
    path: docs-evaluator|repo-local-docs-review|missing
    reason: "Documentation reachability may be blocking AI work."
repeated_waste:
  - pattern: "Same failure or workaround repeated across sessions."
    durable_home: "docs|skill|script|test|rubric|local-state"
    teacher_move: "Failure Promotion"
promotion_candidates:
  - kind: skill|AGENTS.md|docs|script|test|checklist|evaluator-backlog|local-state|no-promotion
    proposal: "Promote the repeated failure into a reusable workflow."
    score: 0
    score_basis:
      recurrence: 0
      friction: 0
      risk: 0
      portability: 0
      future_value: 0
    score_confidence: observed|estimated
    evidence_count: 0
    direction: personal|repo-local|public
    recommended_home: "Path, evaluator, or owner to review."
    validation_prompt: "How to check whether the promotion helped."
teacher_moves:
  - axis: verification
    pattern: "Pin observed failure before implementation."
evidence_policy:
  raw_excerpt_allowed: true
  shareable: false
warnings:
  - "trusted-local report; do not share or commit"
review_warnings:
  - "Score is low-confidence because evidence is sparse."
```

## Period Review

```yaml
mode: trusted-local|shareable
lens: repository|cross-repository|both
shareable: false
subject: period
period: YYYY-MM-DD..YYYY-MM-DD
sessions_reviewed: 0
repository_scope:
  kind: single-repository|multi-repository|unknown
  repositories: 0
evidence_coverage:
  confidence: low|medium|high
  sessions_with_structured_signals: 0
  sessions_with_only_textual_impressions: 0
  excluded:
    - raw_prompt_bodies
recurring_gaps:
  - verification
improvement_surfaces:
  - docs
  - orchestration
recommended_review_paths:
  - path: docs-evaluator|agent-orchestration-evaluator|code-evaluator|repo-local-review|missing
    reason: "Observed failures suggest repository-side review may be needed."
repeated_waste:
  - pattern: "Verification added after implementation in multiple sessions."
    recommended_promotion: "Add a reusable request checklist."
promotion_candidates:
  - kind: skill|AGENTS.md|docs|script|test|checklist|evaluator-backlog|local-state|no-promotion
    score: 0
    score_confidence: observed|estimated
    evidence_count: 0
    direction: personal|repo-local|public
improved_axes:
  - skill_use
teacher_focus:
  - "For the next week, require success condition and verification command in every implementation request."
trend_notes:
  - axis: skill_use
    direction: improved|flat|regressed
    evidence: "Behavior-level evidence only unless trusted-local."
```

## Cross-Repository Review

```yaml
mode: trusted-local|shareable
lens: cross-repository
shareable: false
subject: cross_repository
period: YYYY-MM-DD..YYYY-MM-DD
repository_scope:
  kind: multi-repository
  repositories: 0
cross_repo_patterns:
  - pattern: "Agents repeatedly fail to find verification entrypoints."
    scope: multi-repo|global
    affected_surfaces:
      - docs
      - workflow
    evidence_kind: behavior-level
reusable_improvement_candidates:
  - kind: skill|script|checklist|global-instruction|repo-template|evaluator-backlog
    proposal: "Create a standard verification-entrypoint checklist."
    scope: multi-repo|global
    score: 0
    score_basis:
      recurrence: 0
      friction: 0
      risk: 0
      portability: 0
      future_value: 0
    score_confidence: observed|estimated
    evidence_count: 0
    direction: personal|repo-local|public
    recommended_home: "Where this should live if accepted."
    validation_prompt: "How to test that the reusable improvement reduces repeated waste."
per_repo_followups:
  - repo_label: repo-a
    suspected_surface: docs
    recommended_review_path: docs-evaluator|repo-local-review|missing
warnings:
  - "Cross-repo pattern; verify locally before changing an individual repository."
```

## Report Sections

For session review:

1. Summary
2. Axis Scores
3. Priority Improvements
4. Improvement Surfaces
5. Recommended Review Paths
6. Teacher Moves
7. Repeated Waste / Promotion Candidates
8. Evidence Coverage
9. Privacy / Shareability

For period review:

1. Summary
2. Recurring Gaps
3. Improvement Surfaces
4. Recommended Review Paths
5. Improved Axes
6. Teacher Focus For Next Period
7. Repeated Waste / Promotion Candidates
8. Representative Session Notes
9. Privacy / Shareability

For cross-repository review:

1. Summary
2. Cross-Repository Patterns
3. Reusable Improvement Candidates
4. Per-Repository Followups
5. Recommended Review Paths
6. Teacher Focus For Next Period
7. Evidence Coverage
8. Privacy / Shareability

## Evidence Formatting

- `trusted-local`: raw excerpts may appear under a clearly labeled "Local-only evidence" section.
- `shareable`: evidence must be behavior-level and must not contain prompt bodies or raw excerpts.
- `teacher-pack`: evidence must be synthetic or generalized.
- Structured signals such as task outcomes, tool outcomes, verification commands, artifacts, and explicit corrections should be reported before softer transcript impressions.
- Keyword counts, prompt length, tone, and tool count are secondary clues; do not use them as primary evidence for scoring.
- Every scored axis and promotion candidate should have an evidence count or a confidence reason.
- Promotion score is triage evidence. It should not force `skill` when `AGENTS.md`, docs, a script, a test, or a checklist is the smaller durable home.

## Routing Semantics

- `improvement_surfaces` describe where the next improvement likely belongs, not final findings.
- `recommended_review_paths` name only public evaluators or repository-local review paths. Do not require specific unavailable agents.
- Use `missing` when the repository has no visible review path for the suspected surface.
- Keep repository-side claims at hypothesis level unless a dedicated evaluator report is already available.
- `lens: repository` means optimize for one repository's next useful review or durable instruction.
- `lens: cross-repository` means cluster repeated patterns and reusable improvements across repositories; do not turn one repo's local fix into a global rule without corroborating evidence.

## Anti-Rationalization Checks

- Flag all-high scores when evidence is sparse.
- Flag action items that cannot be verified in the next session or period.
- Flag polished AI output accepted without tests, review, source checks, or explicit acceptance criteria.
- Flag repeated failures explained as one-off tool noise when they recur across sessions or repositories.
