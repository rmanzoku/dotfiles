---
name: chezmoi-knowledge
description: Repo-specific chezmoi semantics and decision rules for this dotfiles repository. Use when reasoning about `dot_*`, `private_*`, `symlink_*`, source state vs target state, `.chezmoiignore`, hidden source directories, or whether a file is actually deployed by chezmoi. Use alongside `dotfile-update` when editing chezmoi-managed files so the agent does not make source/target or ignore-rule mistakes.
---

# Chezmoi Knowledge

Use this skill as the repo-local knowledge layer for chezmoi semantics.
This skill is for avoiding incorrect assumptions, not for driving an operational command flow.

## Canonical Reference

Read [references/semantics.md](./references/semantics.md) before making or explaining non-trivial chezmoi decisions in this repository.
Treat that reference as the canonical source for repo-specific semantics.

## Use This Skill For Judgment, Not Procedure

- Correct misunderstandings before proposing edits.
- Explain source state and target state in repo terms.
- Sanity-check whether a file is managed by chezmoi at all.
- Separate semantic knowledge from the edit/apply workflow.

If the task is actually changing dotfiles, also use `dotfile-update`.
Keep this skill focused on interpretation, not step-by-step execution.

## High-Risk Misconceptions

Prioritize these checks when chezmoi is involved:

1. `dot_` is a target-name transform:
   `dot_foo` becomes `.foo` in the target.

2. `private_` is a permission attribute, not a generic rename prefix:
   it makes the target private; it does not mean "drop `private_` and treat the rest as a special source naming rule".

3. `.chezmoiignore` matches target paths, not source paths:
   reason about `.claude/...`, not `dot_claude/...`.

4. Hidden source directories are usually ignored by chezmoi:
   repo-local `.claude/skills/` is not deployed by `chezmoi apply`.

5. `symlink_` source files represent target symlinks:
   the source is still a regular file whose contents become the symlink target.

6. `chezmoi add --follow` does not preserve an existing symlink as a symlink:
   it imports the link target contents as a regular file.

7. `mode = "symlink"` is not "everything becomes a symlink":
   it has important exclusions and is not this repo's default mental model.

For the full semantic rules, examples, and official-documentation links, read [references/semantics.md](./references/semantics.md).

## Repo-Specific Decision Rules

When interpreting a file in this repository:

- First decide whether it is a chezmoi-managed source file or only a repo-local helper file.
- Do not infer target paths from naming by memory alone when the distinction matters.
- Do not explain repo-local `.claude/skills/` or other hidden helper directories as if they are user target files.
- Do not mix up naming transforms with permission attributes.
- Do not describe `.chezmoiignore` using source-path examples when user-facing clarity matters.

## What This Skill Should Prevent

This skill exists to prevent errors like:

- claiming `.claude/skills/` will be applied to `$HOME`
- treating `private_` as a filename rewrite rule
- writing `.chezmoiignore` patterns against `dot_*` source names
- assuming `--follow` keeps symlinks as symlinks
- presenting source filenames as if they were final deployed target names

## Boundary With Other Skills

- `dotfile-update`:
  use for actual edits, sync checks, apply flow, and drift checks.
- `chezmoi-knowledge`:
  use for semantic interpretation, explanation, and pre-edit mental model correction.

If both apply, use this skill first to establish the correct model, then use `dotfile-update` for execution.
