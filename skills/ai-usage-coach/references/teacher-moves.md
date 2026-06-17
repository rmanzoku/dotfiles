# Teacher Moves

Teacher moves are coaching interventions derived from the teacher's practice. They are not scoring criteria and should not make "similar to teacher" the goal.

## Move Catalog

### Intent

- Pattern: state the outcome before the task details.
- Use when: the prompt starts with implementation details before explaining why the work matters.
- Example move: "First name the deliverable, then list acceptance criteria."

### Scope

- Pattern: separate target, non-targets, and constraints.
- Use when: the agent may edit adjacent files or invent extra behavior.
- Example move: "Add a Scope block with `in`, `out`, and `must preserve` bullets."

### Decomposition

- Pattern: split by responsibility and artifact gates.
- Use when: the task mixes research, implementation, review, and reporting.
- Example move: "Make Phase 1 produce a findings artifact before Phase 2 edits files."

### Context

- Pattern: pass source paths and decisions, not raw history.
- Use when: the user pasted long background or omitted source-of-truth files.
- Example move: "Name the canonical file and the exact section the agent should trust."

### Skill Use

- Pattern: invoke a skill when the task repeats or has a known contract.
- Use when: the user manually restates a workflow that already belongs in a skill.
- Example move: "Use the existing skill, then note what should be codified if the workflow recurs."

### Tool / Agent Use

- Pattern: delegate bounded sidecar work and keep orchestration local.
- Use when: the user asks one agent to do research, implementation, and review in a single pass.
- Example move: "Give the reviewer only the target files, constraints, and expected finding format."

### Verification

- Pattern: pin the observed failure before asking for implementation.
- Use when: there is no reproduction, test command, or pass/fail criterion.
- Example move: "State failing behavior, smallest reproduction, and the exact verification command."

### Recovery

- Pattern: leave restartable artifacts for long work.
- Use when: progress lives only in conversation.
- Example move: "Write `.context/<task>/status.md` with current state, blockers, and next command."

### Privacy

- Pattern: decide shareability before reading or writing evidence.
- Use when: raw logs, prompt bodies, paths, emails, or tokens may appear.
- Example move: "Use `trusted-local` for raw excerpts and switch to behavior-only evidence before sharing."

### Learning Loop

- Pattern: codify recurring mistakes into docs or skills.
- Use when: the same correction appears across sessions.
- Example move: "If this happens twice, update the relevant skill or AGENTS rule instead of relying on memory."

## Output Shape

```yaml
teacher_move:
  axis: verification
  pattern: "Pin the observed failure before asking for implementation."
  example: "State failing behavior, smallest reproduction, and verification command."
  next_prompt_snippet: "Success condition: ...; Repro: ...; Verify with: ..."
```
