---
name: skill-manager
description: "Unified skill and plugin manager for Claude Code. Provides a single view of ALL skills the session recognizes: marketplace plugins, global custom skills, and project skills. Supports cross-agent skill synchronization with Codex. Use when the user wants to list all skills/plugins, install or remove a plugin, update plugins, manage custom skill sources, check skill health, sync skills to Codex, migrate from Commands to Skills format, or get an overview of what's available. Triggers on: 'list skills', 'list plugins', 'install plugin', 'update plugins', 'skill manager', 'manage skills', 'what skills are available', 'show all plugins', 'add skill source', 'remove skill', 'sync codex', 'migrate skill', or any mention of managing skills/plugins across sources."
---

# Skill Manager

Unified manager for Claude Code skills and plugins. Provides a single view across three skill sources:

1. **Marketplace Plugins** — managed by `claude plugin` CLI
2. **Global Custom Skills** — `~/.claude/skills/*/SKILL.md` (Skills format) and `~/.claude/commands/*.md` (Commands format, deprecated)
3. **Project Skills** — `<git-root>/.claude/skills/*/SKILL.md` (Skills format) and `<git-root>/.claude/commands/*.md` (Commands format, deprecated)

Parse `$ARGUMENTS` to determine which subcommand to run. If no arguments or unrecognized input, show a help summary.

## Data Sources

Plugin state is stored in JSON files under `~/.claude/plugins/`:
- **`installed_plugins.json`** — installed plugins, keyed by `<name>@<marketplace>`, with scope, installPath, version, gitCommitSha
- **`known_marketplaces.json`** — registered marketplaces, with source repo and installLocation
- **`<installLocation>/.claude-plugin/marketplace.json`** — each marketplace's plugin catalog (name, description, skills)

**Always read these files directly** rather than using `claude plugin list` CLI, which may return empty output when invoked via Bash tool. Use `claude plugin install/uninstall/update` CLI only for mutating operations (install, remove, update).

## Agent Conventions

Skill directory structures and constraints for each agent. Subcommands follow these rules.

### Claude Code (primary)

- Global skills: `~/.claude/skills/*/SKILL.md`
- Legacy format (deprecated): `~/.claude/commands/*.md`
- Project skills: `<git-root>/.claude/skills/*/SKILL.md`
- Plugins: managed via `claude plugin` CLI, state stored in `~/.claude/plugins/`
- Legacy format files trigger migration warnings

### Codex

- Global skills: `~/.codex/skills/<name>/` (symlinks from Claude)
- Project skills: `<git-root>/.agents/skills/<name>/` (relative symlinks)
- **System skills**: `~/.codex/skills/.system/` contains Codex-managed skills. When a skill name matches a `.system` entry, `.system` takes precedence — silently skip during sync, migration, clean, and health checks (no warning needed)
- Manifests: `~/.codex/skills/.skill-manager-sync.json` (global), `<git-root>/.agents/skills/.skill-manager-sync.json` (project)

### Qwen Code

- Global skills: `~/.qwen/skills/`
- Sync not yet supported

## Commands

### `list [--full]`

Show installed/active skills. With `--full`, also show uninstalled marketplace plugins.

**Fast path** (preferred):
1. Run `bash ~/.claude/skills/skill-manager/scripts/list.sh [--full]` via a single Bash tool call
2. Parse the returned JSON
3. Format as tables shown below

The script keeps the existing top-level JSON keys:

```json
{
  "marketplace_plugins": [],
  "global_skills": [],
  "project_skills": [],
  "project_root": null,
  "skill_sources": null,
  "errors": []
}
```

Additional metadata is attached inside list elements:

- `sync_state`: `system|synced|broken|unsynced`
- `format`: `skills|command`
- `deprecated`: boolean
- `hidden_duplicate`: boolean
- `warnings`: array of `{code, path, reason}`

Error objects use the fixed shape `{code, path, reason}`.
When run outside a git repository, `project_root` must be `null` and `project_skills` must be `[]`.
Only `list` is refactored to use the Python-backed fast path in this skill version; other subcommands still follow the documented manual workflows below.

**Fallback** (if script not found or fails):

Steps:
1. Read `~/.claude/plugins/installed_plugins.json` → installed plugins (with scope, version, commit info). The key format is `<plugin-name>@<marketplace-name>`.
2. Read `~/.claude/plugins/known_marketplaces.json` → registered marketplaces (name, repo, installLocation).
3. For each marketplace, read `<installLocation>/.claude-plugin/marketplace.json` → available plugins (name, description). Cross-reference with installed_plugins.json to determine install status.
4. Scan global custom skills (merge both formats, Skills format takes precedence):
   a. Glob `~/.claude/skills/*/SKILL.md` → Skills format (read `name` and `description` from YAML frontmatter)
   b. List `~/.claude/commands/*.md` → Commands format (deprecated). If a skill exists in both `.claude/skills/` and `.claude/commands/`, show only the Skills format version and mark the Commands version as `(deprecated)`.
   c. Check global Codex sync: read `~/.codex/skills/.skill-manager-sync.json` if exists, validate the current link target, and return `sync_state`.
5. Scan project skills (merge both formats, Skills format takes precedence):
   a. Run `git rev-parse --show-toplevel` to find git root. If not in a git repo, display "Project Skills: not in a git repository" and skip this section.
   b. Glob `<git-root>/.claude/skills/*/SKILL.md` → Skills format
   c. List `<git-root>/.claude/commands/*.md` → Commands format (deprecated)
   d. Check project Codex sync: read `<git-root>/.agents/skills/.skill-manager-sync.json` if exists, validate the current link target, and return `sync_state`.
6. If `~/.claude/skill-sources.json` exists, read it for custom skill source/update info.

**Important**: Do NOT use `claude plugin list` or `claude plugin marketplace list` CLI commands for the `list` subcommand — they may return empty output when run via Bash tool. Instead, always read the JSON files directly from `~/.claude/plugins/`.
**Important**: For marketplace plugins, use only the manifest's `skills` array to resolve bundled skills. Do NOT fall back to scanning `installPath`.

#### Default output (`list`)

Show only **installed/active** items. Each row includes a short description extracted from the marketplace manifest or YAML frontmatter.

```
## Marketplace Plugins (installed)

  Plugin: skill-creator (claude-plugins-official)
    Skill                Codex    Description
    ─────                ─────    ──────────
    skill-creator        ✗        Create, improve, and benchmark skills

  Plugin: document-skills (anthropic-agent-skills)
    Skill                Codex    Description
    ─────                ─────    ──────────
    xlsx                 ✓        Spreadsheet processing
    docx                 ✓        Word document processing
    pptx                 ✓        PowerPoint processing
    pdf                  ✓        PDF processing

## Global Custom Skills — Codex sync: ✓ 3 / ✗ 1

  Skill                Codex    Description
  ─────                ─────    ──────────
  skill-manager        ✗        Unified skill and plugin manager
  my-skill             ✓        Example skill in Skills format
  ...

## Project Skills (.claude/skills/) — Codex sync: ✓

  Skill                Codex    Description
  ─────                ─────    ──────────
  project              ✓        Project Document Creator
  kb                   ✓        Knowledge Base Manager
  research             ✓        Multi-model parallel investigation
  ...
```

#### Full output (`list --full`)

Show all plugins from all marketplaces (installed and available), plus all custom/project skills.

```
## Marketplace Plugins

Source: claude-plugins-official (42 plugins)

  Plugin: skill-creator (installed)
    Skill                Codex    Description
    ─────                ─────    ──────────
    skill-creator        ✗        Create, improve, and benchmark skills
  Plugin: code-review (available)
    (not installed)
  ...

Source: anthropic-agent-skills (3 plugins)

  Plugin: document-skills (installed)
    Skill                Codex    Description
    ─────                ─────    ──────────
    xlsx                 ✓        Spreadsheet processing
    docx                 ✓        Word document processing
    pptx                 ✓        PowerPoint processing
    pdf                  ✓        PDF processing
  Plugin: example-skills (available)
    (not installed)
  ...

## Global Custom Skills — Codex sync: ✓ 3 / ✗ 1

  Skill                Codex    Description
  ─────                ─────    ──────────
  skill-manager        ✗        Unified skill and plugin manager
  my-skill             ✓        Example skill in Skills format
  ...

## Project Skills (.claude/skills/) — Codex sync: ✓

  Skill                Codex    Description
  ─────                ─────    ──────────
  project              ✓        Project Document Creator
  kb                   ✓        Knowledge Base Manager
  research             ✓        Multi-model parallel investigation
  ...
```

Descriptions come from:
- **Marketplace plugins**: `description` field in `marketplace.json`
- **Global/Project skills**: `description` field in YAML frontmatter of the `.md` file

### `install <name> [--source <src>]`

Install a skill or plugin.

Routing logic:
1. Build a resolution table:
   - Read `~/.claude/plugins/installed_plugins.json` and marketplace manifest files → marketplace plugins
   - `~/.claude/skill-sources.json` → custom source skills
2. If found in marketplace: `claude plugin install <name>` (installs at user scope)
3. If found in custom source: copy SKILL.md with path rewrites + update registry. Reject if source `trusted == false`.
4. If found in both marketplace AND custom source: require `--source marketplace` or `--source <custom-source-name>` to disambiguate. Show both options and ask user to choose.
5. If not found: report error and suggest `list` to see available options.

For marketplace plugins, the `name` format supports `plugin@marketplace` syntax (e.g., `document-skills@anthropic-agent-skills`).

### `update [--dry-run]`

Check for updates and apply them.

Steps:
1. Run `claude plugin marketplace update` to refresh all marketplace metadata.
2. **Marketplace plugins**: For each installed plugin, run `claude plugin update <name>` to update. On `--dry-run`, just report which plugins have updates available.
3. **Custom skills**: For each source in registry, run `git -C <local_path> fetch origin`. Compare `installed_commit` with FETCH_HEAD. Show diff summary for changed skill directories. On `--dry-run`, stop here. Otherwise, ask user to confirm, then `git -C <local_path> pull` and re-install affected skills.
4. Report results.

For same-name conflicts between marketplace and custom, require `--source` to disambiguate.

### `remove <name>`

Remove a skill or plugin.

Routing logic:
1. Check `~/.claude/plugins/installed_plugins.json` for installed plugins matching `<name>`.
2. Check `~/.claude/skill-sources.json` for installed custom skills matching `<name>`.
3. If marketplace plugin: `claude plugin uninstall <name>`
4. If custom skill: delete the file at `installed_as`, remove from registry.
5. If found in both: show candidates and require `--source` to disambiguate.
6. Confirm with user before executing.

### `add-source <url> [--name <name>] [--path <local-path>]`

Register a new custom Git repository as a skill source. This is for skills NOT distributed via marketplace.

Steps:
1. Derive `name` from URL if not provided (e.g., `github.com/user/repo` → `user-repo`)
2. Derive `local_path` if not provided: `~/.claude/skill-repos/<name>`
3. Validate:
   - No existing source with same `name` or `url`
   - URL must use `https://` scheme
   - After clone, resolve `local_path` with `realpath` (following symlinks) and verify it's under `~/.claude/`
4. Ask user to confirm trust: "You're adding `<url>` as a skill source. Skills from this repository can provide instructions and scripts that Claude executes. Do you trust this repository?"
5. Clone: `git clone --depth 1 -- <url> <local_path>`
6. Detect `skills_dir`: look for directories containing subdirectories with `SKILL.md`. Common patterns: `skills/`, `commands/`, root level.
7. Add to registry with `trusted: true`
8. Show available skills from the new source.

### `remove-source <name>`

Unregister a custom skill source.

Steps:
1. Find the source in registry
2. Check for installed skills from this source. If any exist, warn user and set their state to `"orphaned"`.
3. Remove source entry from registry
4. Ask whether to delete the local clone directory. Only delete if confirmed.

### `migrate <name> [--scope global|project] [--all] [--dry-run]`

Convert Commands format (`.claude/commands/<name>.md`) to Skills format (`.claude/skills/<name>/SKILL.md`).

Steps:
1. Validate `name` matches `^[a-z0-9][a-z0-9._-]*$` (reject path traversal patterns like `../`)
2. Locate the target file:
   - `--scope global`: `~/.claude/commands/<name>.md`
   - `--scope project`: `<git-root>/.claude/commands/<name>.md`
   - If scope omitted: scan both, use whichever exists. If both exist, ask user to specify scope.
3. Check for conflicts:
   - Error if `<scope>/.claude/skills/<name>/SKILL.md` already exists
   - Skip if name conflicts with an agent system skill (see Agent Conventions > Codex)
4. Convert:
   - Create directory `<scope>/.claude/skills/<name>/`
   - Copy content from `.claude/commands/<name>.md` to `.claude/skills/<name>/SKILL.md`
   - Preserve YAML frontmatter as-is
5. Old file handling: Ask user for confirmation, then delete. For git-tracked files, suggest `git rm`.
6. Report: suggest updating any references (e.g., `rules/` docs).

With `--all`: convert all `.md` files in the target scope's `.claude/commands/` directory. Skip files that already have a corresponding `.claude/skills/<name>/SKILL.md`.

With `--dry-run`: list files that would be converted without making changes.

### `sync codex [--force] [--clean] [--dry-run]`

Synchronize Claude Code skills to Codex via symlinks, enabling both agents to use the same skills.

#### Global sync (user-level)

Steps:
1. Ensure `~/.codex/skills/` exists (create if needed)
2. Collect sync sources:
   - Read `~/.claude/plugins/installed_plugins.json` → for each installed plugin, read the corresponding marketplace manifest (`<installLocation>/.claude-plugin/marketplace.json`) to get the plugin's `skills` array, then resolve each skill path under `installPath`. Do NOT scan `installPath` directory — only sync skills explicitly listed in the manifest for that plugin.
   - Glob `~/.claude/skills/*/SKILL.md` → global Skills format
3. For each skill, create symlink `~/.codex/skills/<name>` → `<source-dir>`
   - Skip names reserved by target agent (see Agent Conventions > Codex)
   - Skip if target already exists (unless `--force`)
   - Check for case-insensitive collisions on macOS
4. If any Commands format files exist in `~/.claude/commands/`, warn:
   ```
   ⚠ Commands format skills cannot be synced to Codex:
     ~/.claude/commands/skill-manager.md
   → Use `/skill-manager migrate <name>` to convert to Skills format first.
   ```

#### Project sync

Steps:
1. Run `git rev-parse --show-toplevel` to find git root
2. Ensure `<git-root>/.agents/skills/` exists (create if needed)
3. Glob `<git-root>/.claude/skills/*/SKILL.md`
4. For each skill, create relative symlink: `<git-root>/.agents/skills/<name>` → `../../.claude/skills/<name>`
5. If any Commands format files exist in `<git-root>/.claude/commands/`, warn as above

#### Manifests

Global: `~/.codex/skills/.skill-manager-sync.json`
Project: `<git-root>/.agents/skills/.skill-manager-sync.json`

Schema:
```json
{
  "schema_version": 1,
  "synced_at": "<ISO-8601>",
  "links": [
    {
      "name": "<skill-name>",
      "target": "<absolute-or-relative-path-to-source>",
      "link": "<path-to-symlink>",
      "source_type": "plugin|global_skill|project_skill",
      "source_id": "<plugin-name@marketplace> or null"
    }
  ]
}
```

Update the manifest after each sync operation. Write atomically (temp file + rename).

#### `--clean`

Remove only symlinks recorded in the manifest. Never touch agent system directories or non-symlink entries (see Agent Conventions > Codex).
Read manifest → for each entry, verify `lstat` shows symlink → remove → delete manifest.

#### `--dry-run`

List what would be synced/cleaned without making changes.

#### Security

- Validate `link` paths are under expected directories using `realpath`
- `lstat` check: only remove symlinks, never regular files/directories (require user confirmation for those)
- Validate `target` with `realpath` and verify `SKILL.md` exists
- Validate `name` matches `^[a-z0-9][a-z0-9._-]*$`
- `--force` on existing regular file/directory: refuse and require manual intervention

### `doctor`

Verify health of all skills and plugins.

**Fast path** (preferred):
1. Run `bash ~/.claude/skills/skill-manager/scripts/doctor.sh` via a single Bash tool call
2. Parse the returned JSON
3. Format the findings for the user

The script returns a JSON object with:

```json
{
  "summary": {"pass": 0, "warn": 0, "fail": 0},
  "checks": {},
  "errors": [],
  "project_root": null
}
```

- `summary`: count of `pass|warn|fail`
- `checks`: object keyed by category, each value is an array of check objects
- Check object fields: `status`, `code`, `path`, `reason`, `subject`, `scope`
- `errors`: script-level failures in `{code, path, reason}` format
- When run outside a git repository, `project_root` must be `null` and project-scope checks must not be generated

`doctor` is detection-only in this skill version. It must not create backups, rewrite registries, repair symlinks, or re-bootstrap state.

Checks:
1. **Marketplace plugins**: Read `~/.claude/plugins/installed_plugins.json` and verify each plugin's `installPath` directory exists.
2. **Custom skills**: For each entry in `skill-sources.json`:
   - Verify `installed_as` file exists
   - If `has_resources`: verify `resources_path` directory exists and contains expected files
   - Verify source repo clone is accessible
3. **Registry integrity**: Check `skill-sources.json` is valid JSON with `schema_version`. Report failures only; do not create `.bak` or re-bootstrap automatically.
4. **Deprecated format detection**: Scan `~/.claude/commands/*.md` and `<git-root>/.claude/commands/*.md` for Commands format files. Report count and suggest `/skill-manager migrate --all`.
5. **Codex sync status**:
   - Read `~/.codex/skills/.skill-manager-sync.json` and `<git-root>/.agents/skills/.skill-manager-sync.json`
   - For each entry: verify symlink exists and target is valid
   - Skip names reserved by target agent (see Agent Conventions > Codex)
   - Count synced, broken, and unsynced skills
   - Report and suggest `/skill-manager sync codex` if needed
6. **`.agents/skills/` integrity**: Verify each symlink in `.agents/skills/` points to a valid `.claude/skills/<name>` directory containing `SKILL.md`.
7. **Project skill format compliance**: For each project skill (`<git-root>/.claude/skills/*/SKILL.md`), call `skill-creator/scripts/quick_validate.py` and treat its current behavior as the source of truth.
   - **FAIL** criteria (based on current `quick_validate.py` rules):
     - YAML frontmatter missing or malformed
     - `name` missing or invalid
     - `description` missing or invalid
     - Unknown frontmatter keys (allowed by current validator: `name`, `description`, `license`, `allowed-tools`, `metadata`)
     - `compatibility` present in frontmatter
   - **WARN** criteria (best practice, beyond quick_validate.py scope):
     - SKILL.md exceeds 500 lines — suggest splitting to `references/`
     - `agents/openai.yaml` exists but is not auto-validated against `SKILL.md`
   - Output format:
     ```
     ## Project Skill Format Compliance

       Skill            Status   Issues
       ─────            ──────   ──────
       arch-report      ✅ PASS
       implement        ⚠ WARN   SKILL.md exceeds 500 lines (612) — consider splitting to references/
       pencil           ❌ FAIL   missing 'description' in frontmatter
     ```
9. Report issues with suggested fixes.

## Registry

Custom skill state lives in `~/.claude/skill-sources.json`. Marketplace plugin state is managed by `claude plugin` — do NOT duplicate it in the registry.

### Schema

```json
{
  "schema_version": 2,
  "sources": [
    {
      "name": "my-skills",
      "url": "https://github.com/user/my-skills",
      "local_path": "~/.claude/skill-repos/my-skills",
      "local_path_resolved": "/Users/username/.claude/skill-repos/my-skills",
      "skills_dir": "skills",
      "trusted": true,
      "added_at": "2026-03-09"
    }
  ],
  "installed": [
    {
      "name": "my-skill",
      "source": "my-skills",
      "source_type": "custom",
      "source_path": "skills/my-skill/SKILL.md",
      "resources_path": "~/.claude/skill-repos/my-skills/skills/my-skill",
      "has_resources": true,
      "installed_as": "~/.claude/commands/my-skill.md",
      "installed_commit": "abc1234",
      "installed_at": "2026-03-09",
      "last_checked_at": "2026-03-09",
      "state": "installed"
    }
  ]
}
```

`state` values: `installed` (normal), `orphaned` (source removed), `manual` (not from any source)

### Bootstrap

When `~/.claude/skill-sources.json` does not exist:
1. Create empty registry: `{"schema_version": 2, "sources": [], "installed": []}`
2. Scan `~/.claude/commands/*.md` for files not named `skill-manager.md`
3. Register each as `source: "manual"`, `source_type: "manual"`, `state: "manual"`
4. Show user what was detected and confirm

## Custom Skill Install Logic

When installing from a custom source (not marketplace):

1. Verify source clone exists and `trusted == true`
2. Read `<local_path>/<skills_dir>/<name>/SKILL.md`
3. Inventory supporting files (scripts/, agents/, references/, assets/)
4. Transform SKILL.md:
   - Insert Bundled Resources section after YAML frontmatter
   - Rewrite relative paths to absolute paths pointing to `<resources_path>/`
   - Only rewrite paths in code blocks, backticks, or markdown links — not prose
5. Write to `~/.claude/commands/<name>.md`
6. Update registry with commit hash and metadata

## Security

- Custom sources: `trusted == true` required for install/update. If `trusted == false`, refuse and prompt re-trust.
- Path validation: `local_path` must resolve (via `realpath`, following symlinks) to under `~/.claude/`
- URL validation: only `https://` scheme allowed for `add-source`
- Shell safety: pass arguments to git/rm after `--` separator to prevent injection
- Update safety: always show diffs and require user confirmation before applying
- Marketplace: delegated to `claude plugin` CLI (inherits Claude Code's security model)

## Error Handling

- Git failures (network, auth): report clearly, suggest checking connectivity
- Missing source clone: offer to re-clone
- Corrupted registry: back up as `.bak`, offer to re-bootstrap
- Unparseable SKILL.md (no frontmatter): skip with warning

## Output Style

- Use tables for list output
- Use diff-style formatting for update previews
- Be concise — this is a management tool, not a conversation
- Always confirm destructive operations before executing
