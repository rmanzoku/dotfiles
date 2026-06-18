# Teacher Examples v0

These are synthetic examples. They are not copied from real logs.

## Example 1: Weak Implementation Request

Scenario:

> The user asks an agent to fix a bug but gives no reproduction, no expected behavior, and no verification command.

Axis scores:

```yaml
intent: 2
scope: 2
decomposition: 2
context: 2
skill_use: 2
tool_agent_use: 2
verification: 0
recovery: 2
privacy: 7
learning_loop: 2
```

Diagnosis:

- The request has a direction, but the success condition is not testable.
- Verification is the highest-leverage improvement.

Teacher move:

```yaml
axis: verification
pattern: "Verification Before Implementation"
next_prompt_snippet: |
  Success condition:
  Reproduction:
  Verification command:
  Expected evidence:
```

## Example 2: Strong Skill Creation Request

Scenario:

> The user asks to create a new skill, identifies the target user, names related skills, separates trusted-local and shareable modes, and asks to stop at design before implementation.

Axis scores:

```yaml
intent: 10
scope: 10
decomposition: 10
context: 8
skill_use: 10
tool_agent_use: 8
verification: 8
recovery: 8
privacy: 10
learning_loop: 10
```

Diagnosis:

- The request is strong because it identifies purpose, distribution constraints, related skills, and staged implementation.
- Verification can improve by naming the exact validation commands before implementation.

Teacher move:

```yaml
axis: verification
pattern: "Verification Before Implementation"
next_prompt_snippet: |
  Validate with skill quick validation, privacy scan on generated reports, and one synthetic fixture run.
```

## Example 3: Over-Broad Agent Delegation

Scenario:

> The user asks one agent to research, implement, review, and prepare the final report without specifying role boundaries or artifacts.

Axis scores:

```yaml
intent: 7
scope: 2
decomposition: 0
context: 5
skill_use: 2
tool_agent_use: 2
verification: 2
recovery: 0
privacy: 5
learning_loop: 2
```

Diagnosis:

- The work should be split into orchestration, bounded worker/reviewer tasks, and final synthesis.
- Recovery is weak because no intermediate artifacts are required.

Teacher move:

```yaml
axis: decomposition
pattern: "Delegation Contract"
next_prompt_snippet: |
  Researcher: collect evidence only.
  Worker: edit only the named files.
  Reviewer: report findings only.
  Parent: synthesize and decide final output.
```
