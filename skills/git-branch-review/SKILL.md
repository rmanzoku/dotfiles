---
name: git-branch-review
description: Inspect fresh local and remote Git branch and GitHub pull request state across machines and collaborators. Use when Claude Code or Codex needs to fetch recent remote refs, detect open PRs without local branches, classify origin branches as deletion candidates, decide whether a clean local branch can be fast-forwarded, compare branches with upstream/default branches, check whether branches are merged, or correlate branches with GitHub PR state.
---

# Git Branch Review

## Overview

Build a current, conservative view of local and remote Git branch state before deciding what to update, merge, delete, or hand off. Prefer CLI inspection over assumptions, and never hide dirty worktree state.

## Workflow

1. Confirm the target repository path and run all commands from that repository root.
2. Inspect current state before changing anything:
   - `git status --short --branch`
   - `git remote -v`
   - `git branch --show-current`
3. Refresh remote knowledge with `git fetch --all --prune` for a normal or read-only remote review because it does not mutate the server. It may update or remove stale local remote-tracking refs. Use `--no-fetch` only when the user explicitly asks for offline inspection or prohibits local ref updates; do not infer that prohibition from “read-only” alone.
4. If the user wants the current branch updated from origin, fast-forward only when all conditions are true:
   - worktree is clean by `git status --porcelain`
   - the current branch has an upstream
   - local ahead count is `0`
   - remote behind count is greater than `0`
   - `git pull --ff-only` succeeds
5. Summarize local branches with upstream, ahead/behind counts, merge status relative to `origin/HEAD` or `origin/main`, and latest commit subject.
6. When GitHub context is available, list repository-wide open PRs before correlating local and `origin` branch names with same-repository PRs. Do not treat a same-named fork PR as belonging to an `origin` branch.
7. Classify each `origin` branch conservatively:
   - `keep`: default branch, protected branch, or branch with an open/draft PR
   - `safe deletion candidate`: no open/draft PR, not protected, and either merged into the default branch or its current tip matches a merged same-repository PR targeting the default branch
   - `needs confirmation`: not merged and has no open PR
   - `unknown`: PR, protection, default-ref, or ancestry information is unavailable
   Treat age or naming alone as context, never as evidence that deletion is safe.
8. Report recommended next actions separately from facts. Never delete a local or remote branch unless the user explicitly asks after seeing the review.

## Script

Use the bundled script for the standard report:

```bash
python3 skills/git-branch-review/scripts/executable_git_branch_review.py /path/to/repo
```

For this repository when the skill is installed outside the target repo, resolve the script path from the skill folder first.

Useful options:

- `--fast-forward-clean`: update only the current branch, and only when the safety conditions above hold.
- `--no-fetch`: inspect without refreshing remotes.
- `--no-pr`: skip GitHub PR and protected-branch lookups; remote deletion classification becomes `unknown` except for the default branch.

The script prints progress before network-sensitive work and emits a Markdown report with facts separated from recommended next actions. It uses only `git`, optional `gh`, and the Python standard library.

## Output Contract

Include:

- current branch, upstream, worktree cleanliness, ahead/behind counts, and whether a fast-forward ran or was skipped
- repository-wide open PR table, including PRs whose head branch does not exist locally
- `origin` remote branch table with deletion classification, reason, protection status, tracking local branches, last update, tip SHA, and subject
- local branch table with upstream, ahead/behind, merged/not merged relative to default remote ref, PR status, last update, tip SHA, and subject
- explicit gaps such as `gh unavailable`, fetch failure, no upstream, detached HEAD, or ambiguous default branch
- a separate recommended-next-actions section; list deletion candidates without executing `git push origin --delete`, surface confirmation and information gaps, and mention a dirty worktree when present

Do not present inferred PR or deletion safety as certain when `gh` could not query GitHub. In this skill, remote branch deletion means a server-side operation such as `git push origin --delete`; fetch/prune maintenance of local remote-tracking refs is reported separately. Treat the classification as a review result, not authorization to delete.
