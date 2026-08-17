---
name: git-branch-review
description: "Refresh Git branch state: fetch, fast-forward tracking branches that are behind, delete merged local branches, delete merged origin branches in private repos, and report origin branches with PR correlation. Use when Claude Code or Codex needs to bring branches up to date, clean up merged branches, or classify origin branches for deletion."
---

# Git Branch Review

## Overview

Bring local and `origin` branch state up to date after work on other machines or by collaborators, then report what remains. Everything the script does by default is reversible by the executor alone and prints its rollback handle; server-side deletion outside a private repository is left as a reported next action.

## Workflow

1. Run the bundled script from the target repository root. When the skill is installed outside the target repo, resolve the script path from the installed skill folder first:

   ```bash
   python3 <skill-dir>/scripts/executable_git_branch_review.py /path/to/repo
   ```

2. By default the script:
   - runs `git fetch --all --prune` (updates and prunes local remote-tracking refs; server state is untouched). Use `--no-fetch` only when the user asks for offline inspection or prohibits local ref updates; do not infer that from "read-only" alone.
   - fast-forwards every local tracking branch that is strictly behind its upstream: the current branch via `git pull --ff-only` only when the worktree is clean, other branches via `git fetch . refs/remotes/<upstream>:refs/heads/<branch>`. Diverged branches and branches checked out in another worktree are skipped and reported. Rollback: `git reset --hard <before>` / `git branch -f <branch> <before>`.
   - deletes local branches whose tip is already contained in the default remote branch (ancestor of `origin/HEAD`, or tip equal to a merged same-repository PR targeting the default branch), except the current branch, the default branch, worktree-checked-out branches, and branches whose upstream is classified `keep`. Rollback: `git branch <branch> <tip>`.
   - lists repository-wide open PRs and classifies each `origin` branch: `keep` (default / protected / open or draft PR), `safe deletion candidate` (no open PR, not protected, merged into the default branch or tip equal to a merged same-repository PR), `needs confirmation` (not merged and no open PR), `unknown` (PR / protection / default-ref / ancestry information unavailable). Same-named fork PRs do not belong to an `origin` branch; age or naming alone is context, not evidence.
   - deletes `safe deletion candidate` origin branches only when `gh repo view` reports the repository as `private`. Rollback: `git push origin <tip>:refs/heads/<branch>` (a merged tip stays reachable from the default branch; a squash-merged tip stays fetchable as GitHub's `refs/pull/<n>/head`). For `public`, `internal`, or unknown visibility it prints the exact `git push origin --delete` command instead and does not run it.

   Opt-outs: `--no-fast-forward`, `--no-local-cleanup`, `--no-remote-cleanup`, `--no-pr` (skip `gh`; remote classification becomes `unknown` except the default branch, and remote cleanup does not run).

3. Report the script's Markdown output. It already separates facts (current branch, fast-forward table, local cleanup table, remote cleanup table, open PRs, `origin` branch table, local branch table) from remaining next actions (candidates left on origin with the exact command, `needs confirmation` and `unknown` branches, dirty worktree). Two operations stay outside the default run: deleting a `needs confirmation` branch, and `git push origin --delete` on a non-private repository (a server-side operation the branch's other readers cannot undo alone). Run either only when the user names the branch; a general "clean up" request does not.
