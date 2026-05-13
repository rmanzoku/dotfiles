---
name: skill-manager
description: "Manage external and local agent skills across Claude Code, Codex, and other supported agents. Use when the user wants to find, install, remove, update, audit, adopt, or inventory skills, especially with `gh skill`, Codex `.system/skill-installer`, agent-specific installs, vendored skills, or cross-agent differences."
---

# Skill Manager

External skill management workflow centered on `gh skill`, with Codex `.system/skill-installer` recognized as a Codex-only helper.
This skill no longer assumes that Claude Code and Codex must have the same skill set.
Treat agent differences as normal, and track why each skill exists where it does.
When a repository has its own skill policy in `AGENTS.md`, ADRs, or equivalent docs, follow that local policy instead of hard-coding repo-specific rules into this skill.

## Core model

Manage skills with three concepts:

1. **Provenance**: where the skill came from
   - `codex-installer`: installed into Codex by the Codex `.system/skill-installer` helper
   - `vendored`: copied into a git-managed repo and managed by git
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

When `gh` is version `2.90.0` or newer, `gh skill` is available in public preview as an official GitHub CLI subcommand.

Treat the tools like this:

- `gh skill`: GitHub-native preview/install/update/publish flow with provenance metadata and agent-host aware placement
- Codex `.system/skill-installer`: Codex-only helper for listing OpenAI curated/experimental skills or copying a GitHub repo path into `$CODEX_HOME/skills`

Prefer `gh skill` when the user wants:
- install provenance recorded into `SKILL.md`
- pinning and update checks tied to GitHub refs and tree SHA
- `gh skill publish` validation against agentskills.io and GitHub release-based publishing
- a new install path going forward

Use Codex `.system/skill-installer` only when the user specifically wants the Codex curated/experimental skill list or a quick Codex-only install from `openai/skills` or a GitHub path.
After such an install, inventory it as a Codex direct install and document stable external dependencies in the repository manifest when the install should be reproducible.
Do not treat `skill-installer` as the long-term cross-agent lifecycle backend.

## What this skill manages

- external skills installed via `gh skill`
- Codex direct installs created by `.system/skill-installer`, as inventory entries and reproducibility follow-up
- git-managed original skills stored in a repository
- agent-specific differences between Claude Code, Codex, Gemini CLI, Cursor, etc.
- inventory and policy decisions about whether a skill is repo-original, external, or out of scope
- Claude marketplace plugin inventory and health checks when plugin-provided skills matter
- Codex plugin inventory and health checks based on `~/.codex/config.toml`, marketplace metadata, and local plugin cache

## What this skill does not treat as the same thing

- MCP servers
- Codex `.system` skills

These can still be inventoried when useful, but they are not the primary package model for this skill.
Plugins are managed as a separate layer from `gh skill` installs and should not be flattened into the same lifecycle.

## Command routing

Parse `$ARGUMENTS` and choose one of the flows below.
If the user intent is ambiguous, default to `list`.

### `find [query]`

Search external skills.

Steps:
1. Prefer `gh skill search [query]`
2. Summarize the candidate skills
3. If the user is choosing between candidates, call out supported agents and likely fit

### `list [--global] [--json]`

Inventory installed skills, grouped by agent and provenance.

Preferred steps:
1. Scan vendored/manual and directly installed skill directories
   - global: `~/.claude/skills/*/SKILL.md`
   - project: `<git-root>/.claude/skills/*/SKILL.md`
   - codex global: `~/.codex/skills/*/SKILL.md` and `~/.codex/skills/*`
   - codex project: `<git-root>/.agents/skills/*`
2. Scan plugin inventories separately
   - Claude marketplace: `~/.claude/plugins/installed_plugins.json`, `known_marketplaces.json`, marketplace manifest
   - Codex plugin config: `~/.codex/config.toml`
   - Codex plugin cache: `~/.codex/plugins/cache/*/*/*/.codex-plugin/plugin.json`
   - Codex bundled marketplace manifest: `~/.codex/.tmp/bundled-marketplaces/*/.agents/plugins/marketplace.json`
3. Merge the results into one inventory

Output should show:
- skill name
- bare skill name and display name when they differ
- scope
- installed agents
- provenance
- path
- source-aware identity fields such as `source_type`, `source_id`, and stable `identity`
- Codex status such as `installed`, `missing`, `broken`, `system-preferred`
- source identity without flattening plugin / user / project / system origins into one unnamed bucket
- explicit collision records when the same bare skill name appears in multiple sources
- Codex plugin status such as `enabled`, `configured`, `cached`, `available`

Important:
- If a skill exists in Claude but not Codex, report that as inventory data, not as an error by default.
- If a skill name collides with Codex `.system`, mark it `system-preferred`.
- Treat valid direct installs in Codex as healthy even if no mirror manifest entry exists.
- Aggregate skills in a source-aware way. Preserve plugin namespace and origin metadata instead of merging entries by bare skill name.
- Treat Codex plugin-provided skills as their own source type, separate from direct installs under `~/.codex/skills`.

### `gh install <repo-or-skill> [--pin <ref>]`

Install an external skill via `gh skill install`.

Use this when the user has `gh >= 2.90.0` and wants GitHub-native skill management.

Steps:
1. Confirm `gh` version supports `gh skill`
2. Run `gh skill preview <repo-or-skill>` before installation when practical
3. Run `gh skill install <repo-or-skill> [--pin <ref>]`
4. Re-run `list` or inspect the target agent directory to confirm placement
5. Report recorded provenance metadata and whether the install remains an external skill managed outside the current repository

Guidance:
- Prefer `gh skill install` when the user values provenance, pinning, and GitHub-native update/publish behavior
- If the current repository keeps original skills in git and external skills outside the repo, preserve that boundary

### `codex install <skill-or-github-path>`

Install into Codex through the Codex `.system/skill-installer` helper only when the user explicitly wants that path.

Use this when:
- the target is Codex only
- the source is `openai/skills` curated or experimental skills
- the user provides a GitHub repo/path and does not need `gh skill` provenance or cross-agent lifecycle

Guidance:
- Prefer `gh skill install` for durable external installs, pinning, update checks, and multi-agent installs.
- Treat installed results as Codex direct installs under `$CODEX_HOME/skills`, not as `gh skill`-managed installs.
- If the skill becomes part of the user's reproducible setup, record the repo, path, ref, and reason in the local install manifest instead of relying on Codex state alone.
- Do not use `skill-installer` for Codex `.system` skills; they are preinstalled system capabilities.

### `remove <skill> [--agent <agent...>] [--global]`

Remove a `gh skill`-managed installation.

Steps:
1. Run `gh skill remove <skill> ...`
2. Re-run `list`
3. If the skill still appears because it is vendored/manual, explain that the external install was removed but a git-managed copy remains

### `check`

Check for updates to external skills.

Steps:
1. Run `gh skill update --dry-run`
2. Summarize available updates
3. If a skill is vendored in the current repository, treat upstream updates as advisory and do not overwrite the vendored copy automatically

### `update`

Update `gh skill`-managed external skills.

Steps:
1. Run `gh skill update`
2. Re-run `list`
3. Report which installs changed
4. If the updated skill is also vendored here, explicitly note that the repo copy did not change

### `publish`

Publish a skill with `gh skill publish`.

Use this when the user wants to publish a skill to GitHub in a way that validates against agentskills.io and records GitHub-native release metadata.

Guidance:
- Prefer `gh skill publish` for GitHub-hosted public distribution
- Call out that GitHub recommends inspecting skills before install and that `gh skill` does not verify prompt safety for the user
- Treat repository security checks such as tag protection, secret scanning, and code scanning as part of the release-readiness review

### `adopt <skill>`

Adopt an external skill into a git-managed repository copy when the user explicitly wants that lifecycle.

Use this flow only when the repository policy permits git-managed adoption or when the skill is confirmed to be repo-original rather than external.

Steps:
1. Confirm whether the skill is `repo-original` or `external`
2. If it is external, check whether the current repository allows adoption into git-managed copies
3. If the repository forbids adoption, stop and point back to `gh skill install` / `gh skill update` plus the local policy docs
4. If it is repo-original, manage it in the appropriate git-managed location and update docs as needed

Important:
- Do not mirror upstream content into a repository just to make an install persistent unless the user wants a git-managed fork or local derivative

### `doctor`

Audit installed skills for drift, broken references, and policy mismatches.

Check:
- broken installed paths
- broken symlinks
- stale mirror metadata
- vendored skills missing from expected agent directories
- agent-specific installs that appear accidental
- broken Codex plugin cache or config entries
- Codex plugin declarations whose `skills`, `apps`, or `mcpServers` payload is missing
- collisions with Codex `.system`
- deprecated command-format skills still present

Detection-first only.
Do not rewrite state unless the user asks.

### `sync codex`

Compatibility command for repo-managed mirroring into Codex.
Do not use this as the default way to understand whether a skill is healthy in Codex.
The standard Codex path is a valid install under `~/.codex/skills` or `.agents/skills`, including direct copies created by `gh skill install`.

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
- `trial`: installed directly for evaluation but not promoted into repo management
- `installed`: valid install exists in the target agent directory
- `missing`: no install exists in the target agent directory
- `broken`: installed path or metadata is invalid
- `system-preferred`: Codex has a `.system` skill with the same name

When multiple entries share the same bare skill name:

- keep them as separate inventory entries if their sources differ
- preserve plugin namespacing where the host exposes it
- report the collision instead of silently collapsing entries into one
- only apply hard preference automatically for Codex `.system`
- Codex plugin-provided skills count as a separate source from Codex direct installs

## Prompting guidance

When helping the user choose a management path:

- Prefer `gh skill install` for new installs
- Use Codex `.system/skill-installer` only as a Codex-only convenience path for curated/experimental OpenAI skills or one-off GitHub-path installs
- Follow repository-local policy docs for the boundary between external installs and git-managed copies
- Prefer reporting agent differences instead of automatically syncing them away
- Keep plugin management separate from skill installs, but include Claude and Codex plugins when the user is auditing actual availability
- For Codex plugins, treat `~/.codex/config.toml` plus marketplace metadata as the control plane and `~/.codex/plugins/cache` as the local realized state

## Validation

After updating this skill:

1. Run `scripts/skill-quick-validate <skill-dir>` from this repository
2. If helper scripts were changed, run their simplest smoke checks
3. Re-read the whole `SKILL.md` and remove contradictions with current tooling
4. If the repo-local validator is unavailable, use the `skill-creator` validator as a fallback and record any runtime dependency issue

For this repository's publisher source, use:

```bash
scripts/skill-quick-validate skills/skill-manager
```
