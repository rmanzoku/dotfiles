---
name: handoff
description: Create continuation handoffs for another agent, session, PR reviewer, or future machine. Use when the user asks to hand off work, defer work, resume later, prepare PR handoff context, transfer context across machines, summarize current state for the next agent, or preserve ignored artifacts such as `.context` without leaking secrets.
---

# Handoff

## Overview

Create a handoff packet that lets a fresh agent resume work without guessing. Choose the handoff medium from the destination, persistence needs, and whether ignored artifacts or secrets are involved.

## Workflow

1. Determine the destination:
   - Same worktree or same machine: write an ignored artifact under `.context/handoff/`.
   - Cross-machine continuation: use a PR as the default carrier.
   - PR reviewer or collaborator: draft a PR comment unless the user explicitly asks to post it.
   - Deferred work without an open PR: write `.context/handoff/` locally and recommend the smallest durable next carrier, usually a branch or PR.
2. Inspect the repository instead of asking when the answer is discoverable from git status, recent diffs, tests, docs, existing `.context` artifacts, or PR metadata available in the environment.
3. Identify ignored or local-only context:
   - For same-worktree handoff, reference `.context` artifact paths directly.
   - For PR or cross-machine handoff, do not assume `.context` files travel. Summarize the necessary facts from ignored artifacts and reference only committed paths, commits, branches, PR URLs, or comments.
   - If the ignored artifact is too large or too sensitive to summarize, state the missing carrier explicitly and ask for a durable transfer choice.
4. Check for secrets:
   - Never include secret values, tokens, private keys, real `op://...` references, local account names, or sensitive manifest rows.
   - If secret-backed files must be saved, restored, diffed, or explained, use `$onepassword-secret-materialize`.
   - In the handoff, describe only the non-secret action needed, for example "restore secret-backed files with `$onepassword-secret-materialize` before running integration checks."
5. Write or draft the handoff. External writes such as posting PR comments, creating issues, or editing durable docs require explicit user instruction.

## Medium Rules

`.context/handoff/`:
- Use for local same-worktree continuation, active investigation state, or intermediate notes that should not be committed.
- Include front matter with `task`, `phase_or_step`, and `created_at` when the repository requires artifact gating.
- Make filenames stable and scannable, such as `.context/handoff/2026-06-04-topic.md`.

PR handoff:
- Use for cross-machine continuation by default.
- Prefer a concise PR comment draft that points to commits, files, tests, unresolved decisions, and next steps.
- If the user asks to post the comment, use the available GitHub workflow or CLI after verifying the target PR.
- Do not depend on local ignored files; extract the relevant facts into the PR comment draft.
- If the PR, branch, commit, or other durable anchor is unknown, state that it is missing and make confirming or creating it the next action. Do not invent anchors or treat a local branch name as cross-machine durable unless it is pushed or otherwise verified.

Durable repository docs:
- Use only when the handoff contains lasting policy, architecture decisions, or repeated operational knowledge.
- Put long-term decisions in the repository's normal docs or ADR location, following local instructions.
- Do not turn one-off session state into permanent docs.

Deferred work:
- Capture the current stopping point, the next concrete action, blockers, validation already run, and validation still needed.
- Keep the scope narrow enough that the next agent can start with one command or one file read.
- If there is no durable carrier yet and cross-machine use is likely, recommend creating or updating a PR.
- If no PR exists yet, write a pre-PR handoff and make PR creation or update the next action instead of forcing the output into PR comment form.

## Handoff Content

Include only information that changes the next agent's behavior:

- Goal and current status.
- Branch, PR, commit, or workspace path.
- Available durable anchors, and any required anchors that are still missing.
- Relevant changed files and why they matter.
- Decisions already made and their source.
- Open decisions, blockers, and the recommended next question when needed.
- Commands already run and their results.
- Commands not yet run and why.
- Ignored artifact summaries when the receiver cannot access the files.
- Suggested skills for the next agent, including `$onepassword-secret-materialize` when secret-backed files are part of the workflow.

Do not duplicate committed plans, ADRs, PR descriptions, test logs, or issue text. Link or reference them by path, commit, PR URL, or artifact path instead.

## Template

Use this structure unless the target medium has a stronger local convention. Keep the front matter for `.context/` handoff files when the repository requires artifact gating (see Medium Rules); for PR comments and other non-file media, drop the front matter block:

```markdown
---
task: <task-or-topic>
phase_or_step: handoff
created_at: <ISO-8601 timestamp>
---

# Handoff

## Destination
[same worktree | PR | cross-machine via PR | deferred work | other]

## Current State
[goal, status, branch/PR/workspace]

## What Changed
[changed files, commits, or PR context]

## Decisions
[confirmed decisions with sources]

## Local Or Ignored Context
[artifact paths for same-worktree use, or summaries for PR/cross-machine use]

## Validation
[commands run, results, gaps]

## Next Actions
[ordered, concrete steps]

## Suggested Skills
[skills the next agent should invoke]
```

## Redaction Rules

Before finalizing, scan the handoff for secrets, credentials, private URLs, personal data, and unnecessary local machine details. Replace sensitive material with a safe description of how to obtain or restore it. When the workflow depends on secret-backed local files, invoke or recommend `$onepassword-secret-materialize` instead of documenting the secret material.
