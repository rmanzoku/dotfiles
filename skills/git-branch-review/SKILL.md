---
name: git-branch-review
description: Inspect fresh Git branch state across local machines and collaborators. Use when Claude Code or Codex needs to fetch recent remote refs, decide whether a clean local branch can be fast-forwarded from origin, compare local branches with upstream/default branches, check whether branches are merged, or correlate local branches with GitHub PR state.
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
3. Refresh remote knowledge with `git fetch --all --prune` unless the user explicitly asks for offline inspection.
4. If the user wants the current branch updated from origin, fast-forward only when all conditions are true:
   - worktree is clean by `git status --porcelain`
   - the current branch has an upstream
   - local ahead count is `0`
   - remote behind count is greater than `0`
   - `git pull --ff-only` succeeds
5. Summarize local branches with upstream, ahead/behind counts, merge status relative to `origin/HEAD` or `origin/main`, and latest commit subject.
6. When GitHub context is available, correlate local branch names with PRs using `gh pr list --state all --head <branch>`. Treat missing `gh` auth or missing PRs as information gaps, not proof that no review happened.
7. Report recommended next actions separately from facts. Do not delete, rebase, force-push, or merge branches unless the user explicitly asks after seeing the branch review.

## Script

Use the bundled script for the standard report:

```bash
python skills/git-branch-review/scripts/executable_git_branch_review.py /path/to/repo
```

For this repository when the skill is installed outside the target repo, resolve the script path from the skill folder first.

Useful options:

- `--fast-forward-clean`: update only the current branch, and only when the safety conditions above hold.
- `--no-fetch`: inspect without refreshing remotes.
- `--no-pr`: skip `gh pr list` calls.

The script prints progress before network-sensitive work and emits a Markdown report. It uses only `git`, optional `gh`, and the Python standard library.

## Output Contract

Include:

- current branch, upstream, worktree cleanliness, ahead/behind counts, and whether a fast-forward ran or was skipped
- local branch table with upstream, ahead/behind, merged/not merged relative to default remote ref, PR status, last update, tip SHA, and subject
- explicit gaps such as `gh unavailable`, fetch failure, no upstream, detached HEAD, or ambiguous default branch
- concrete next actions, for example `pull --ff-only`, inspect a dirty diff, push an unpublished branch, close a merged PR branch, or ask a collaborator about an unmerged branch

Do not present inferred PR state as certain when `gh` could not query GitHub.
