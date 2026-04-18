---
title: "Chezmoi Semantics For This Repo"
updated_at: 2026-04-18
---

# Chezmoi Semantics For This Repo

This reference summarizes the chezmoi semantics that are easy to misread in this repository.
Use it to correct assumptions before editing or explaining behavior.

## Core Model

- chezmoi computes target state from source state and applies it into the destination directory.
- The source directory is usually `~/.local/share/chezmoi`.
- The destination directory is usually `~`.
- Files such as `dot_*` in this repository are source-state representations, not literal target filenames.

## Repo-Specific Semantics

### 1. `dot_` Is A Name Transform

- `dot_foo` becomes `.foo` in the target.
- This applies to files and directories.

### 2. `private_` Is A Permission Attribute, Not A Generic Rename Prefix

- `private_` does not mean "rename by stripping `private_`".
- It means the target file or directory is created without group/world permissions.
- Example: `dot_codex/private_config.toml` becomes `~/.codex/config.toml`, and the important semantic point is that the target is private.

### 3. Hidden Source Directories Are Usually Ignored

- In source state, leading-dot directories are ignored by default except for chezmoi special directories such as `.chezmoi*`.
- Therefore repo-local `.claude/skills/` is not deployed by `chezmoi apply`.
- Editing `.claude/skills/` changes repo-local tooling, not a chezmoi-managed target file in `$HOME`.

### 4. `.chezmoiignore` Matches Target Paths, Not Source Paths

- Write ignore patterns against final target paths such as `.claude/...`, not source names such as `dot_claude/...`.
- When in doubt, think about where the file lands in the target before writing the ignore rule.

### 5. Source / Target Mapping Must Not Be Guessed From Memory

- Naming rules are easy to misremember.
- If the distinction matters, verify the mapping instead of inferring it casually.
- The important habit is to confirm the direction of the mapping before editing or explaining behavior.

### 6. Symlinks Are Represented As Regular Source Files

- chezmoi source state consists of regular files and directories.
- A target symlink is represented by a regular source file with a `symlink_` prefix.
- The contents of that source file become the target symlink destination.
- Trailing newlines are trimmed from the symlink target.
- Valid combined prefix ordering matters: `symlink_` then `dot_`, so `symlink_dot_foo` becomes a symlink target named `.foo`.

### 7. `chezmoi add --follow` Imports The Link Target As A File

- Adding an existing symlink without `--follow` captures the symlink itself into source state.
- `chezmoi add --follow <target>` follows the symlink and imports the referent as a regular file.
- That means a future `chezmoi apply` will normally replace the original symlink with a file.
- Do not describe `--follow` as "keep the symlink managed as a symlink".

### 8. `mode = "symlink"` Is Not A Universal Symlink Mode

- It can make eligible regular files deploy as symlinks to the source directory.
- It does not apply to encrypted, executable, private, or template files.
- It does not apply to directories as a blanket rule.
- In this repository, the default mental model is still explicit `symlink_` source files, not generic symlink mode everywhere.

## Decision Checklist

Before reasoning about a file here, check:

1. Is it a chezmoi-managed source file or only a repo-local helper file?
2. Are you describing a source name or a target name?
3. Are you confusing a permission attribute with a naming transform?
4. If `.chezmoiignore` is involved, are you thinking in target paths?
5. If symlinks are involved, are you distinguishing `symlink_` representation from `add --follow` behavior?

## Errors This Reference Should Prevent

- Claiming repo-local `.claude/skills/` is applied into `$HOME`
- Treating `private_` as a plain filename rewrite rule
- Writing `.chezmoiignore` rules against source names like `dot_claude/...`
- Claiming `chezmoi add --follow` preserves symlinks as symlinks
- Speaking about source filenames as if they were already deployed target paths

## Official Documentation

- [Concepts](https://www.chezmoi.io/reference/concepts/)
- [Source state attributes](https://www.chezmoi.io/reference/source-state-attributes/)
- [Target types](https://www.chezmoi.io/reference/target-types/)
- [.chezmoiignore](https://www.chezmoi.io/reference/special-files/chezmoiignore/)
- [Special directories](https://www.chezmoi.io/reference/special-directories/)
- [add](https://www.chezmoi.io/reference/commands/add/)
- [target-path](https://www.chezmoi.io/reference/commands/target-path/)
- [Migrating from another dotfile manager](https://www.chezmoi.io/migrating-from-another-dotfile-manager/)
- [umask](https://www.chezmoi.io/reference/configuration-file/umask/)
