---
name: skill-manager
description: "Manage external and local agent skills across Claude Code, Codex, and other supported agents. Use when the user wants to find, install, remove, update, migrate, audit, adopt, or inventory skills, especially with `gh skill`, `npx skills` / skills.sh, agent-specific installs, vendored skills, or cross-agent differences."
---

# Skill Manager

External skill management workflow centered on `gh skill`, with `skills.sh` retained for legacy installs and staged migration.
This skill no longer assumes that Claude Code and Codex must have the same skill set.
Treat agent differences as normal, and track why each skill exists where it does.

## Core model

Manage skills with three concepts:

1. **Provenance**: where the skill came from
   - `skills-cli`: installed by `npx skills add`
   - `vendored`: copied into this repo and managed by git
   - `manual`: hand-written local skill not tied to a remote package
   - `plugin`: bundled through another plugin system
2. **Scope**:
   - `global`: user-level install
   - `project`: repo-level install
3. **Installed agents**:
   - Claude Code only
   - Codex only
   - multiple agents

Do not assume parity across agents.
A skill may intentionally exist only in Claude, only in Codex, or in both.

## Primary backend

Use `gh skill` as the default backend for external skill discovery, installation, update, and publishing when `gh >= 2.90.0` is available.

Run commands with telemetry disabled unless the user explicitly wants default telemetry behavior:

```bash
SKILLS_TELEMETRY_DISABLED=1 npx --yes skills <subcommand> ...
```

When `gh` is version `2.90.0` or newer, `gh skill` is available in public preview as an official GitHub CLI subcommand.

Treat the tools like this:

- `gh skill`: GitHub-native preview/install/update/publish flow with provenance metadata and agent-host aware placement
- `npx --yes skills`: legacy workflow compatibility, existing trial installs, and migration source inventory

Prefer `gh skill` when the user wants:
- install provenance recorded into `SKILL.md`
- pinning and update checks tied to GitHub refs and tree SHA
- `gh skill publish` validation against agentskills.io and GitHub release-based publishing
- a new install path going forward

Prefer `npx --yes skills` when the user wants:
- compatibility with an existing `skills.sh`-based workflow
- to inspect or migrate already-installed `skills.sh` entries
- behavior on machines where `gh < 2.90.0`

## What this skill manages

- external skills installed via `npx skills`
- vendored skills in `~/.claude/skills/` and `<git-root>/.claude/skills/`
- agent-specific differences between Claude Code, Codex, Gemini CLI, Cursor, etc.
- adoption of a trialed external skill into git-managed dotfiles

## What this skill does not treat as the same thing

- Claude marketplace plugins
- MCP servers
- Codex `.system` skills

These can still be inventoried when useful, but they are not the primary package model for this skill.

## Command routing

Parse `$ARGUMENTS` and choose one of the flows below.
If the user intent is ambiguous, default to `list`.

### `find [query]`

Search external skills.

Steps:
1. Prefer `gh skill search [query]`
2. Summarize the candidate skills
3. If the user is choosing between candidates, call out supported agents and likely fit

If the user explicitly wants the old registry view or is comparing against legacy `skills.sh` results, also run `SKILLS_TELEMETRY_DISABLED=1 npx --yes skills find [query]` and note which backend each result came from.

### `list [--global] [--json]`

Inventory installed skills, grouped by agent and provenance.

Preferred steps:
1. Run `SKILLS_TELEMETRY_DISABLED=1 npx --yes skills ls --json`
2. Run `SKILLS_TELEMETRY_DISABLED=1 npx --yes skills ls -g --json`
3. Scan vendored/manual skill directories that may not have been installed by `skills.sh`
   - global: `~/.claude/skills/*/SKILL.md`
   - project: `<git-root>/.claude/skills/*/SKILL.md`
   - codex global: `~/.codex/skills/*/SKILL.md` and `~/.codex/skills/*`
   - codex project: `<git-root>/.agents/skills/*`
4. Merge the results into one inventory

Output should show:
- skill name
- scope
- installed agents
- provenance
- path
- notes such as `vendored`, `system`, `agent-specific`, `broken-link`

Important:
- If a skill exists in Claude but not Codex, report that as inventory data, not as an error by default.
- If a skill name collides with Codex `.system`, mark it `system-preferred`.

### `add <source> [--skill <name>] [--agent <agent...>] [--global]`

Install an external skill via `skills.sh`.

Steps:
1. Resolve the user’s intended source and agent targets
2. Run `SKILLS_TELEMETRY_DISABLED=1 npx --yes skills add <source> ...`
3. Re-run `list` to confirm installed paths and agent coverage
4. Report whether the install is trial-only or should be adopted into git-managed dotfiles

Guidance:
- Use agent-specific install targets when parity is not needed
- Use this flow mainly for existing `skills.sh` workflows or explicit compatibility requests
- Do not auto-copy a newly installed external skill into this repo unless the user asks to adopt or make it persistent

### `gh install <repo-or-skill> [--pin <ref>]`

Install an external skill via `gh skill install`.

Use this when the user has `gh >= 2.90.0` and wants GitHub-native skill management.

Steps:
1. Confirm `gh` version supports `gh skill`
2. Run `gh skill preview <repo-or-skill>` before installation when practical
3. Run `gh skill install <repo-or-skill> [--pin <ref>]`
4. Re-run `list` or inspect the target agent directory to confirm placement
5. Report recorded provenance metadata and whether the install should remain trial-only or be adopted into git-managed dotfiles

Guidance:
- Prefer `gh skill install` over `npx skills add` when the user values provenance, pinning, and GitHub-native update/publish behavior
- Remember that `gh skill install` copies into agent-native directories instead of using the `~/.agents` plus symlink model described by `skills.sh`
- Do not auto-copy a newly installed skill into this repo unless the user asks to adopt or make it persistent

### `migrate gh [--scope global|project|all]`

Generate staged migration commands from legacy `skills.sh` installs to `gh skill`.

Use this when the user wants to make `gh skill` the new standard but cannot migrate every existing skill or repository immediately.

Steps:
1. Run `bash scripts/executable_plan_gh_migration.sh [--scope ...]`
2. Review the generated commands and unmappable entries
3. Apply global migrations first
4. Leave project-scoped migrations as queued commands until each repository is ready
5. Only remove legacy `skills.sh` installs after the corresponding `gh skill install` has been verified

Guidance:
- The migration command must be reviewable and non-destructive by default
- Prefer emitting one `gh skill preview ...` and one `gh skill install ...` command per skill
- If the legacy metadata cannot be mapped to a GitHub repository, report it as manual follow-up instead of guessing
- Do not batch-apply project-scoped migrations across unrelated repositories automatically

### `remove <skill> [--agent <agent...>] [--global]`

Remove a `skills.sh`-managed installation.

Steps:
1. Run `SKILLS_TELEMETRY_DISABLED=1 npx --yes skills remove <skill> ...`
2. Re-run `list`
3. If the skill still appears because it is vendored/manual, explain that the external install was removed but a git-managed copy remains

### `check`

Check for updates to external skills.

Steps:
1. Run `SKILLS_TELEMETRY_DISABLED=1 npx --yes skills check`
2. Summarize available updates
3. If a skill is vendored in this repo, treat upstream updates as advisory and do not overwrite the vendored copy automatically

### `update`

Update `skills.sh`-managed external skills.

Steps:
1. Run `SKILLS_TELEMETRY_DISABLED=1 npx --yes skills update`
2. Re-run `list`
3. Report which installs changed
4. If the updated skill is also vendored here, explicitly note that the repo copy did not change

If the skill was installed through `gh skill`, use `gh skill update` instead and report whether the pinned ref or recorded provenance changed.

### `publish`

Publish a skill with `gh skill publish`.

Use this when the user wants to publish a skill to GitHub in a way that validates against agentskills.io and records GitHub-native release metadata.

Guidance:
- Prefer `gh skill publish` for GitHub-hosted public distribution
- Call out that GitHub recommends inspecting skills before install and that `gh skill` does not verify prompt safety for the user
- Treat repository security checks such as tag protection, secret scanning, and code scanning as part of the release-readiness review

### `adopt <skill>`

Promote a trialed external skill into git-managed dotfiles.

Use this when the user wants persistence, reviewability, local modification, or reproducibility through this repo.

Steps:
1. Locate the installed skill directory
2. Identify provenance and upstream source
3. Copy the skill into the appropriate git-managed location
   - global dotfiles: `dot_claude/skills/<name>/`
   - project-local skill: `<git-root>/.claude/skills/<name>/`
4. Adjust paths or instructions for local rules if needed
5. If this repo manages Codex sharing for that skill, update the relevant sync policy or docs
6. Record the decision in `docs/adr/` when the adoption changes long-lived workflow

Important:
- Adoption is a review step, not a blind mirror
- Upstream content may need local edits for `.context/`, path resolution, telemetry, or environment compatibility

### `doctor`

Audit installed skills for drift, broken references, and policy mismatches.

Check:
- broken installed paths
- broken symlinks
- vendored skills missing from expected agent directories
- agent-specific installs that appear accidental
- collisions with Codex `.system`
- legacy command-format skills still present

Detection-first only.
Do not rewrite state unless the user asks.

### `sync codex`

Legacy command for repo-managed mirroring into Codex.

Use only for skills whose policy is explicitly `mirror`.
Do not assume all Claude skills should sync into Codex.
Skip:
- agent-specific Claude-only skills
- Codex `.system` collisions
- trial installs that have not been adopted into git

## Inventory rules

When presenting inventory, classify each skill into one of these states:

- `shared`: intentionally installed in multiple agents
- `agent-specific`: intentionally installed in a subset of agents
- `vendored`: repo-managed copy exists
- `trial`: installed via `skills.sh` but not adopted
- `broken`: installed path or link is invalid
- `system-preferred`: Codex has a `.system` skill with the same name

## Prompting guidance

When helping the user choose a management path:

- Prefer `gh skill install` for new installs
- Prefer `migrate gh` to generate staged replacement commands for existing `skills.sh` installs
- Use `npx skills add` only for explicit compatibility needs or legacy workflow support
- Prefer vendoring into this repo for long-lived, modified, or policy-sensitive skills
- Prefer reporting agent differences instead of automatically syncing them away
- Keep marketplace plugin management separate unless the user explicitly asks about plugins

## Validation

After updating this skill:

1. Run `python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py <skill-dir>`
2. If helper scripts were changed, run their simplest smoke checks
3. Re-read the whole `SKILL.md` and remove contradictions with current tooling
