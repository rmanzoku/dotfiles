# Teacher Patterns v0

Use these patterns to turn low-scoring axes into concrete next actions.

## Pattern: Assumption Ledger

Use when: `Intent`, `Scope`, or `Context` is weak.

Move:

1. List assumptions.
2. Separate known facts from guesses.
3. Mark durable decisions that require source-of-truth support or user confirmation.

Prompt snippet:

```text
Assumptions:
- Known from repo/docs: ...
- Inferred: ...
- Needs confirmation before durable change: ...
```

## Pattern: Artifact Gate

Use when: `Decomposition` or `Recovery` is weak.

Move:

1. Define phases.
2. Assign one artifact per phase.
3. Do not advance until the artifact exists.

Prompt snippet:

```text
Phase 1 output: .context/<task>/01-scope.md
Phase 2 output: .context/<task>/02-findings.md
Proceed only after the phase artifact exists.
```

## Pattern: Failure Promotion

Use when: `Recovery` or `Learning Loop` is weak because the same failure, dead end, or workaround has recurred.

Move:

1. Name the repeated failure or waste pattern.
2. Record the failed path and the working path.
3. Decide the durable home: docs, skill, script, test, rubric, or local machine state.
4. Add a prevention rule or checklist item before retrying the same work.

Prompt snippet:

```text
Repeated waste:
- Failed path:
- Working path:
- Durable home:
- Prevention rule:
- Verification that the rule works:
```

## Pattern: Verification Before Implementation

Use when: `Verification` is weak.

Move:

1. State observed failure or target behavior.
2. Name the smallest reproduction or input.
3. Name the verification command, diff, or review check.

Prompt snippet:

```text
Success condition:
Reproduction:
Verification command:
Expected evidence:
```

## Pattern: Shareability Gate

Use when: `Privacy` is weak.

Move:

1. Pick `trusted-local`, `shareable`, or `teacher-pack`.
2. Decide whether raw excerpts are allowed.
3. Run privacy scan before delivery.

Prompt snippet:

```text
Mode: shareable
Raw excerpts: prohibited
Evidence style: behavior-level only
Privacy scan must pass before final output.
```

## Pattern: Skillization Trigger

Use when: `Skill Use` or `Learning Loop` is weak.

Move:

1. Ask whether the workflow will recur.
2. Extract stable steps and validation.
3. Put details in references, not the skill body, when large.

Prompt snippet:

```text
If this workflow recurs, propose:
- skill name
- trigger description
- reusable references/scripts
- validation command
```

## Pattern: Waste Ledger

Use when: a session contains repeated retries, tool dead ends, or bypasses that may recur.

Move:

1. Write a short ledger entry before final output.
2. Include what was tried, why it failed, what worked, and where to codify it.
3. Do not rely on conversation memory as the only storage.

Prompt snippet:

```text
Waste ledger:
- Repeated issue:
- Cost:
- Cause:
- Durable fix candidate:
- Owner/home:
```

## Pattern: Delegation Contract

Use when: `Tool / Agent Use` is weak.

Move:

1. Define delegated role.
2. Bound the scope.
3. Specify expected artifact and prohibited orchestration behavior.

Prompt snippet:

```text
Role:
Scope:
Allowed side effects:
Expected artifact:
Do not synthesize final answer; return findings only.
```

## Pattern: Minimal Diff

Use when: `Scope` or `Learning Loop` is weak because the agent over-edits.

Move:

1. State the exact files or sections in scope.
2. State adjacent things that must not change.
3. Verify with diff review.

Prompt snippet:

```text
Edit only:
Do not change:
Verify with:
```
