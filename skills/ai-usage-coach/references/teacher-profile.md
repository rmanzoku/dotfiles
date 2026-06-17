# Teacher Profile v0

This teacher profile is derived from explicit operating rules, skill design choices, and observed preferences in repository instructions. It is not extracted from raw private logs.

## Identity Of The Profile

The teacher profile represents a coaching stance for AI work delegation:

- Make assumptions and uncertainty explicit before durable decisions.
- Keep implementations minimal and scoped.
- Prefer existing repo patterns and source-of-truth documents.
- Use CLI and concrete artifacts for reproducibility.
- Separate orchestration from delegated work.
- Treat privacy, secret handling, and shareability as first-class design constraints.
- Verify with tests, diffs, scans, or reproducible checks.
- Convert recurring failures, dead ends, and lessons into managed docs, skills, scripts, or rubrics.

## What This Profile Is Not

- It is not a personality model.
- It is not a productivity ranking.
- It is not a style target.
- It is not a replacement for local team norms.
- It is not proof that the teacher's behavior is always optimal.

## Coaching Doctrine

### 1. Define The Job Before Asking AI To Work

Good delegation starts with a concrete outcome, scope, constraints, and success condition. A weak prompt often asks for effort; a strong prompt asks for an artifact that can be checked.

### 2. Keep Context Deliberate

Pass source-of-truth paths, key decisions, relevant constraints, and known failures. Avoid dumping history and asking the agent to infer current truth from noise.

### 3. Split Work By Responsibility

Use the parent agent for orchestration, synthesis, and final judgment. Delegate bounded research, review, worker, or verification tasks when the environment supports it.

### 4. Use Skills When A Workflow Repeats

If the same workflow, checklist, or judgment pattern appears repeatedly, codify it into a skill, docs section, or reusable reference instead of relying on memory.

### 5. Verification Is Part Of The Request

A good AI request says how success will be checked. Tests, reproduction steps, privacy scans, link checks, diffs, and explicit acceptance criteria all reduce ambiguity.

### 6. Preserve Recovery State

Long-running work should leave artifacts that survive context compaction, interruption, or a different agent taking over.

### 7. Promote Repeated Waste

If the same failure, tool confusion, validation gap, or workaround appears more than once, the next action is not another manual retry. Capture the cause, the working path, the failed path, and the prevention rule in a durable place.

### 8. Treat Privacy As A Mode Decision

Decide whether the output is local-only or shareable before quoting evidence. Raw excerpts are local-only by default.

## How To Use In Reports

Use this profile to generate "teacher move" coaching. Do not score a user by similarity to this profile. Score the user's behavior against `rubric.md`; then use this profile to suggest the next better move.
