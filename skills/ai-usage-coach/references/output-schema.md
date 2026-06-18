# Output Schema

Use Markdown for human-facing reports. Include a YAML summary block when the user wants machine-readable output.

## Language

- Write report prose in the primary language of the reviewed session or artifact.
- If evidence spans multiple languages, use the user's latest request language.
- Keep fixed YAML keys in English; translate human-facing values, headings, summaries, diagnoses, and recommendations.
- Do not use English headings from these examples when the session language is Japanese or another language.
- In Japanese reports, translate report section headings, table labels, score explanations, action labels, and warning text into natural Japanese. Keep English only for fixed YAML keys, commands, tool names, skill names, exact repo names, and proper nouns.
- Do not write a half-translated report where headings remain English but paragraphs are Japanese.

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
  representative_examples:
    - kind: command-class|failure-shape|repo-label|short-redacted-excerpt|artifact
      example: "Concrete local-only example, redacted if needed."
  excluded:
    - raw_prompt_bodies
  confidence_reason: "Scores are based on observed outcomes and validation gaps."
scores:
  score_range: 0..10
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
    path: docs-evaluator|repo-local-docs-review|business-management-review|missing
    reason: "Documentation reachability may be blocking AI work."
field_context:
  fde_adjacent: false
  ai_usage_only: true
  customer_value_judgment: out-of-scope
  business_review_needed: false
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
  representative_examples_reviewed: 0
  evidence_depth: aggregate-only|sampled-examples|artifact-backed
  excluded:
    - raw_prompt_bodies
decision_summary:
  headline: "The one operational conclusion the user should act on."
  do_next:
    - "Concrete next action with target and verification."
  do_not_do_yet:
    - "A tempting but unsupported change to avoid."
hotspots:
  - label: "repo/workflow/tool/error class"
    observed_signal: "Counts or artifact-backed evidence."
    representative_examples:
      - "Local-only concrete example or sanitized failure shape."
    why_it_matters: "Waste, risk, recurrence, or verification impact."
    likely_surface: docs|orchestration|tooling|workflow|code|durable-instructions|local-environment
    review_path: docs-evaluator|agent-orchestration-evaluator|code-evaluator|repo-local-review|missing
    next_action: "Smallest useful action."
    verification: "How to know the action helped."
recurring_gaps:
  - verification
improvement_surfaces:
  - docs
  - orchestration
recommended_review_paths:
  - path: docs-evaluator|agent-orchestration-evaluator|code-evaluator|business-management-review|repo-local-review|missing
    reason: "Observed failures suggest repository-side review may be needed."
field_context:
  fde_adjacent: false
  ai_usage_only: true
  customer_value_judgment: out-of-scope
  business_review_needed: false
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
hotspots:
  - label: "repo/workflow/tool/error class"
    scope: single-repo|multi-repo|global
    observed_signal: "Counts or artifact-backed evidence."
    representative_examples:
      - "Local-only concrete example or sanitized failure shape."
    likely_surface: docs|orchestration|tooling|workflow|code|durable-instructions|local-environment
    recommended_home: AGENTS.md|docs|script|test|checklist|evaluator-backlog|local-state|no-promotion
    owner_or_review_path: "Who or which evaluator should inspect it next."
    verification: "Concrete follow-up check."
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
    recommended_review_path: docs-evaluator|business-management-review|repo-local-review|missing
warnings:
  - "Cross-repo pattern; verify locally before changing an individual repository."
```

## Report Sections

For session review:

1. Summary / 要約
2. Axis Scores / 軸別スコア
3. Priority Improvements / 優先改善
4. Improvement Surfaces / 改善面
5. Recommended Review Paths / 推奨レビュー経路
6. Teacher Moves / 次回の動き
7. Repeated Waste / Promotion Candidates / 繰り返しコストと昇格候補
8. Evidence Coverage / 根拠の厚み
9. Privacy / Shareability / 秘匿性と共有可否

For period review:

1. Summary / 要約
2. Decision Summary / 判断サマリー
3. Top Hotspots / 主要な詰まりどころ
4. Recurring Gaps / 繰り返し弱い点
5. Improvement Surfaces / 改善面
6. Recommended Review Paths / 推奨レビュー経路
7. Concrete Next Actions / 次にやること
8. Improved Axes / 改善した軸
9. Teacher Focus For Next Period / 次期間の重点
10. Repeated Waste / Promotion Candidates / 繰り返しコストと昇格候補
11. Representative Session Notes / 代表例
12. Privacy / Shareability / 秘匿性と共有可否

For cross-repository review:

1. Summary / 要約
2. Decision Summary / 判断サマリー
3. Top Hotspots / 主要な詰まりどころ
4. Cross-Repository Patterns / リポジトリ横断パターン
5. Reusable Improvement Candidates / 再利用できる改善候補
6. Per-Repository Followups / リポジトリ別フォロー
7. Recommended Review Paths / 推奨レビュー経路
8. What Not To Change Yet / まだ変えないこと
9. Teacher Focus For Next Period / 次期間の重点
10. Evidence Coverage / 根拠の厚み
11. Privacy / Shareability / 秘匿性と共有可否

## Report Quality Gate

For `period` and `cross-repository` reports, the report is incomplete unless it includes:

- At least one concrete hotspot label, not only aggregate percentages.
- In `trusted-local` mode, hotspot labels should use concrete repo/workflow labels when available. Avoid vague labels like "wallet app 系" if the evidence has a more concrete repo label.
- A decision summary that says what to do next.
- A `do_not_do_yet` or "What Not To Change Yet" section for tempting but unsupported changes.
- For each top recommendation: target, durable home, review path or owner, and verification.
- A confidence note that distinguishes aggregate counts, sampled examples, and artifact-backed checks.
- For `trusted-local` mode, representative examples for each top hotspot unless privacy risk blocks them.
- For FDE-adjacent work, a clear note that customer requirement, customer value, stakeholder, and commercial judgments are out of scope unless backed by a separate business/management review.
- Human-facing headings and table labels must match the report language.

Avoid reports that only say "add outcome line", "make a checklist", or "run evaluator" without naming where the signal came from and how the next action will be checked.

## Evidence Formatting

- `trusted-local`: raw excerpts may appear under a clearly labeled "Local-only evidence" section.
- `shareable`: evidence must be behavior-level and must not contain prompt bodies or raw excerpts.
- `teacher-pack`: evidence must be synthetic or generalized.
- Structured signals such as task outcomes, tool outcomes, verification commands, artifacts, and explicit corrections should be reported before softer transcript impressions.
- Aggregate counts are not enough for high-confidence coaching. Use sampled representative examples or artifact-backed checks to make the diagnosis concrete.
- Prefer short local-only examples like command class, failure shape, repo/workflow label, or paraphrased prompt intent over full raw prompt bodies.
- In `trusted-local`, prefer exact repo/workflow labels from evidence unless they contain sensitive customer information. In `shareable`, use sanitized but still specific labels.
- Keyword counts, prompt length, tone, and tool count are secondary clues; do not use them as primary evidence for scoring.
- Every scored axis and promotion candidate should have an evidence count or a confidence reason.
- Promotion score is triage evidence. It should not force `skill` when `AGENTS.md`, docs, a script, a test, or a checklist is the smaller durable home.

## Routing Semantics

- `improvement_surfaces` describe where the next improvement likely belongs, not final findings.
- `recommended_review_paths` name only public evaluators or repository-local review paths. Do not require specific unavailable agents.
- Use `business-management-review` for customer requirement, customer value, stakeholder expectation, scope/contract, pricing, or commercial-risk questions. Do not require a specific private business agent.
- Use `missing` when the repository has no visible review path for the suspected surface.
- Keep repository-side claims at hypothesis level unless a dedicated evaluator report is already available.
- `lens: repository` means optimize for one repository's next useful review or durable instruction.
- `lens: cross-repository` means cluster repeated patterns and reusable improvements across repositories; do not turn one repo's local fix into a global rule without corroborating evidence.

## Anti-Rationalization Checks

- Flag all-high scores when evidence is sparse.
- Flag action items that cannot be verified in the next session or period.
- Flag polished AI output accepted without tests, review, source checks, or explicit acceptance criteria.
- Flag repeated failures explained as one-off tool noise when they recur across sessions or repositories.
