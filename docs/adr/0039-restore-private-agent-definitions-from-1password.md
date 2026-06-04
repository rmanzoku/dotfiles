---
title: "Restore Private Agent Definitions From 1Password"
date: 2026-06-01
agent_model: "GPT-5 Codex"
updated_at: 2026-06-03
updated_by_agent_model: "GPT-5 Codex"
---

# ADR 0039: Restore Private Agent Definitions From 1Password

## Context

Private cross-repository assistant agents may contain personal knowledge, private repository context, durable operating preferences, or fact indexes used across projects. These files should still be edited as chezmoi source files so that `chezmoi apply` can deploy them consistently, but their content should not be committed to git.

Claude Code personal agents are deployed from `~/.claude/agents/`.
Codex personal agents are deployed from `~/.codex/agents/`.
In this repository, those targets correspond to source paths under `dot_claude/agents/` and `dot_codex/agents/`.

## Decision

Private agent definitions under `dot_claude/agents/` and `dot_codex/agents/` are git-ignored source files. Files that may contain private content should use chezmoi's `private_` source attribute so their deployed targets are not group/world-readable.

Private secretary facts are stored as an AI-optimized JSONL file under `dot_config/private_private-secretary/private_facts.jsonl`, deployed to `~/.config/private-secretary/facts.jsonl`. This file is also git-ignored and 1Password-backed.

The files are restored through the existing 1Password-backed `opmaterialize` workflow:

- edit the source files in this repository;
- register or update each file with `opmaterialize add <path>`;
- restore them on another machine with `opmaterialize restore`;
- deploy them to the target home directories with `chezmoi apply`.

The 1Password `Secrets Manifest` owns the concrete file list and document item names. Git only stores the generic workflow, ignore rules, and this rationale.

## Update Procedure

Update private agent-related files from the chezmoi source tree, not from their deployed home-directory targets.

Primary source and target pairs:

| Purpose | Source | Target |
|---|---|---|
| Claude Code private agents | `dot_claude/agents/private_<agent>.md` | `~/.claude/agents/<agent>.md` |
| Codex private agents | `dot_codex/agents/private_<agent>.toml` | `~/.codex/agents/<agent>.toml` |
| Private secretary facts | `dot_config/private_private-secretary/private_facts.jsonl` | `~/.config/private-secretary/facts.jsonl` |
| Private secretary bank facts | `dot_config/private_private-secretary/private_bank-accounts.jsonl` | `~/.config/private-secretary/bank-accounts.jsonl` |
| Private secretary assets | `dot_config/private_private-secretary/private_assets/private_<name>` | `~/.config/private-secretary/assets/<name>` |

For a normal update:

1. Edit the source file in this repository.
2. If the same agent exists for multiple AI tools, check whether the corresponding source file needs the same semantic update.
3. Validate structured files before saving them. For JSONL fact stores, parse every non-empty line as JSON and check duplicate IDs.
4. Register each changed private source file with `opmaterialize add <source-path>`.
5. Run `scripts/chezmoi-drift --check-ignore`.
6. Apply only the changed target paths with `chezmoi apply`. Use `--parent-dirs` when adding a new nested target path.
7. Confirm the changed source and target files match, and run the relevant drift check.

Do not print private agent definitions, private secretary facts, bank-account facts, or profile assets in command output or review notes. Report only paths, record counts, IDs, validation status, and 1Password manifest status.

When updating private secretary facts, treat the current user instruction as an approved save boundary only for durable, reusable facts. Keep secrets, credentials, tokens, raw confidential documents, detailed customer financials, and bank-account details out of the general fact store.

## Consequences

- Private agent definitions can be edited in the chezmoi source tree without becoming git content.
- Private secretary facts can be updated by AI agents as JSONL records while remaining outside git history.
- `chezmoi apply` remains the deployment step for Claude Code and Codex agent files.
- A new machine must run `opmaterialize restore` before `chezmoi apply` if these ignored source files are not present locally.
- The repository cannot review or diff the private agent or fact-store content from git history, by design.
