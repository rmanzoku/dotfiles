# Teacher Archetypes v0

Use archetypes to classify recurring AI usage patterns. A user can match multiple archetypes in one period. Archetypes are coaching handles, not identities.

## Orchestrator-First

Signals:

- Defines phases, artifacts, and stop conditions.
- Keeps final synthesis and judgment in the parent thread.
- Delegates bounded side tasks to subagents or runners.

Teacher move:

- "Name the role, expected artifact, allowed side effects, and verification method before delegation."

Common failure when missing:

- One agent performs research, implementation, review, and final synthesis with no recoverable intermediate state.

## Verification-First

Signals:

- States reproduction steps, test commands, privacy checks, or acceptance criteria early.
- Treats validation failure as a design input, not a postscript.

Teacher move:

- "Before changing code or docs, write the observed failure and the command or diff that proves the fix."

Common failure when missing:

- The work looks done but cannot be checked without reinterpreting the request.

## Skill-Codifier

Signals:

- Notices repeated workflows.
- Converts durable procedures into `SKILL.md`, references, scripts, or repo docs.
- Keeps skill bodies lean and pushes detailed material into references.

Teacher move:

- "If this workflow will recur, extract the invariant procedure and put examples in references."

Common failure when missing:

- The same prompt or checklist is rewritten manually each time.

## Privacy-Gated

Signals:

- Chooses local-only vs shareable mode before reading or quoting raw logs.
- Uses scans and redaction gates.
- Avoids raw prompt bodies in public artifacts.

Teacher move:

- "Decide shareability first; if shareable, convert raw evidence to behavior-level evidence."

Common failure when missing:

- Useful coaching includes raw prompt text that cannot safely leave the machine.

## Minimal-Scope Implementer

Signals:

- Changes only what the request requires.
- Avoids unrelated refactors, new settings, or speculative future-proofing.
- Reads existing implementation before choosing abstractions.

Teacher move:

- "State what will not change before editing, then verify only the touched behavior."

Common failure when missing:

- A simple request grows into a broad redesign without source-of-truth support.

## Artifact-Gated Planner

Signals:

- Phase transitions depend on written artifacts, not memory or verbal completion claims.
- Artifacts include task, phase, timestamp, status, and next step.

Teacher move:

- "Write the phase artifact before moving to the next step."

Common failure when missing:

- Context compaction or agent handoff loses the current state.
