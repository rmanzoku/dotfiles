---
name: handoff
description: Create continuation handoffs for another agent, session, PR reviewer, or future machine. Use when the user asks to hand off work, defer work, resume later, prepare PR handoff context, transfer context across machines, summarize current state for the next agent, or preserve ignored artifacts such as `.context` without leaking secrets.
---

# Handoff

## Overview

Create a handoff packet that lets a fresh agent resume work without guessing. Choose the handoff medium from the destination, persistence needs, and whether ignored artifacts or secrets are involved.

## Workflow

1. Determine the destination, and resolve repository visibility once with `gh repo view --json visibility` when the destination involves GitHub. When it is `PRIVATE`, pushing the working branch, creating or updating the PR, and posting the handoff comment are done by this skill (each is undoable by the author and reaches only collaborators inside the boundary). When it is public, internal, or unknown (`gh` unavailable), draft instead and make that step the user's next action.
   - Same worktree or same machine: write an ignored artifact under `.context/handoff/`.
   - Cross-machine continuation: use a PR as the default carrier.
   - PR reviewer or collaborator: post a PR comment (private) or draft it (otherwise).
   - Deferred work without an open PR: write `.context/handoff/` locally, then push the branch and open the PR as the durable carrier (private) or recommend it as the next carrier (otherwise).
2. Inspect the repository instead of asking when the answer is discoverable from git status, recent diffs, tests, docs, existing `.context` artifacts, or PR metadata available in the environment.
3. Identify ignored or local-only context:
   - For same-worktree handoff, reference `.context` artifact paths directly.
   - For PR or cross-machine handoff, do not assume `.context` files travel. Summarize the necessary facts from ignored artifacts and reference only committed paths, commits, branches, PR URLs, or comments.
   - If the ignored artifact is too large or too sensitive to summarize, state the missing carrier explicitly and ask for a durable transfer choice.
4. Check for secrets:
   - Never include secret values, tokens, private keys, real `op://...` references, local account names, or sensitive manifest rows.
   - If secret-backed files must be saved, restored, diffed, or explained, use `$onepassword-secret-materialize`.
   - In the handoff, describe only the non-secret action needed, for example "restore secret-backed files with `$onepassword-secret-materialize` before running integration checks."
5. Write the handoff and deliver it through the medium chosen in step 1.

## Medium Rules

`.context/handoff/`:
- Use for local same-worktree continuation, active investigation state, or intermediate notes that should not be committed.
- Include front matter with `task`, `phase_or_step`, and `created_at` when the repository requires artifact gating.
- Make filenames stable and scannable, such as `.context/handoff/2026-06-04-topic.md`.

PR handoff:
- Use for cross-machine continuation by default.
- Prefer a concise PR comment that points to commits, files, tests, unresolved decisions, and next steps; verify the target PR with `gh pr view` before posting.
- Do not depend on local ignored files; extract the relevant facts into the PR comment.
- If the PR, branch, commit, or other durable anchor is missing, create it (push the branch, open the PR) in a private repository; otherwise state that it is missing and make creating it the next action. Do not invent anchors or treat a local branch name as cross-machine durable unless it is pushed or otherwise verified.

Durable repository docs:
- Use only when the handoff contains lasting policy, architecture decisions, or repeated operational knowledge.
- Put long-term decisions in the repository's normal docs or ADR location, following local instructions.
- Do not turn one-off session state into permanent docs.

Deferred work:
- Capture the current stopping point, the next concrete action, blockers, validation already run, and validation still needed.
- Keep the scope narrow enough that the next agent can start with one command or one file read.
- If there is no durable carrier yet and cross-machine use is likely, write a pre-PR handoff and open the PR with it as the PR body in a private repository; otherwise make PR creation the next action instead of forcing the output into PR comment form.

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
