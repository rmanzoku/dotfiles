#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path
from typing import Any

from common import (
    build_skill_identity,
    build_skill_source_key,
    build_system_skills,
    compute_codex_status,
    detect_source_collisions,
    load_codex_cached_plugins,
    load_codex_enabled_plugins,
    load_codex_marketplaces,
    load_json,
    load_manifest_links,
    load_optional_json,
    parse_frontmatter,
    valid_skill_collection,
    valid_skill_target,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--git-root", default="")
    return parser.parse_args()


ARGS = parse_args()
GIT_ROOT = Path(ARGS.git_root).resolve() if ARGS.git_root else None
CLAUDE_HOME = Path(os.environ.get("SKILL_MANAGER_CLAUDE_HOME", "~/.claude")).expanduser()
CODEX_HOME = Path(os.environ.get("SKILL_MANAGER_CODEX_HOME", "~/.codex")).expanduser()
SKILL_CREATOR_HOME = Path(
    os.environ.get("SKILL_MANAGER_SKILL_CREATOR_HOME", "~/.codex/skills/.system/skill-creator")
).expanduser()

RESULT: dict[str, Any] = {
    "summary": {"pass": 0, "warn": 0, "fail": 0},
    "checks": {},
    "errors": [],
    "project_root": str(GIT_ROOT) if GIT_ROOT else None,
}


def add_error(code: str, path: str | Path, reason: str) -> None:
    RESULT["errors"].append({"code": code, "path": str(path), "reason": str(reason)})


SYSTEM_SKILLS = build_system_skills(CODEX_HOME)
GLOBAL_LINKS = load_manifest_links(CODEX_HOME / "skills" / ".skill-manager-sync.json", add_error)
PROJECT_LINKS = (
    load_manifest_links(GIT_ROOT / ".agents" / "skills" / ".skill-manager-sync.json", add_error)
    if GIT_ROOT
    else {}
)
CODEX_MARKETPLACES = load_codex_marketplaces(CODEX_HOME, add_error)
CODEX_ENABLED_PLUGINS = load_codex_enabled_plugins(CODEX_HOME, add_error)
CODEX_CACHED_PLUGINS = load_codex_cached_plugins(CODEX_HOME, add_error)


def codex_status(name: str, scope: str) -> str:
    return compute_codex_status(
        name=name,
        scope=scope,
        git_root=GIT_ROOT,
        codex_home=CODEX_HOME,
        global_links=GLOBAL_LINKS,
        project_links=PROJECT_LINKS,
        system_skills=SYSTEM_SKILLS,
    )


def add_check(category: str, status: str, code: str, path: str | Path, reason: str, subject: str, scope: str) -> None:
    RESULT["checks"].setdefault(category, []).append(
        {
            "status": status,
            "code": code,
            "path": str(path),
            "reason": reason,
            "subject": subject,
            "scope": scope,
        }
    )
    RESULT["summary"][status] += 1


def add_pass_if_empty(category: str, reason: str, scope: str, subject: str) -> None:
    if not RESULT["checks"].get(category):
        add_check(category, "pass", "NO_ISSUES", "", reason, subject, scope)


def load_plugin_inventory() -> tuple[dict[str, Any], dict[str, Any]]:
    installed_data = load_json(CLAUDE_HOME / "plugins" / "installed_plugins.json", add_error)
    marketplaces_data = load_json(CLAUDE_HOME / "plugins" / "known_marketplaces.json", add_error)
    installed_plugins = installed_data.get("plugins", {}) if isinstance(installed_data, dict) else {}
    marketplaces = marketplaces_data if isinstance(marketplaces_data, dict) else {}
    return installed_plugins, marketplaces


def check_marketplace_plugins() -> None:
    installed_plugins, marketplaces = load_plugin_inventory()
    for plugin_key, entries in installed_plugins.items():
        entry = entries[0] if isinstance(entries, list) and entries else {}
        plugin_name, _, marketplace_name = plugin_key.partition("@")
        subject = plugin_key
        install_path = Path(entry.get("installPath", "")) if entry.get("installPath") else None
        marketplace_info = marketplaces.get(marketplace_name)
        if marketplace_info is None:
            add_check("marketplace_plugins", "fail", "MARKETPLACE_UNKNOWN", plugin_key, "marketplace metadata missing", subject, "global")
            continue
        manifest_path = Path(marketplace_info.get("installLocation", "")) / ".claude-plugin" / "marketplace.json"
        manifest = load_json(manifest_path, add_error)
        plugin_def = None
        if isinstance(manifest, dict):
            plugin_def = next((item for item in manifest.get("plugins", []) if item.get("name") == plugin_name), None)
        if not install_path or not install_path.exists():
            add_check("marketplace_plugins", "fail", "PLUGIN_INSTALL_PATH_MISSING", install_path or "", "installPath missing", subject, "global")
            continue
        if not manifest_path.exists():
            add_check("marketplace_plugins", "fail", "PLUGIN_MANIFEST_MISSING", manifest_path, "marketplace manifest missing", subject, "global")
            continue
        if plugin_def is None:
            add_check("marketplace_plugins", "fail", "PLUGIN_NOT_IN_MANIFEST", manifest_path, "installed plugin missing from manifest", subject, "global")
            continue
        skills = plugin_def.get("skills")
        if skills is None:
            add_check("marketplace_plugins", "warn", "PLUGIN_SKILLS_UNDEFINED", manifest_path, "skills array is undefined", subject, "global")
            continue
        missing_skill = False
        for skill_ref in skills:
            skill_dir = install_path / str(skill_ref).lstrip("./")
            skill_md = skill_dir / "SKILL.md"
            if not skill_md.exists():
                missing_skill = True
                add_check(
                    "marketplace_plugins",
                    "fail",
                    "PLUGIN_SKILL_MISSING",
                    skill_md,
                    "plugin skill SKILL.md missing",
                    f"{subject}:{skill_dir.name}",
                    "global",
                )
        if not missing_skill:
            add_check("marketplace_plugins", "pass", "PLUGIN_OK", install_path, "plugin installPath and manifest are healthy", subject, "global")


def check_codex_plugins() -> None:
    plugin_keys = set(CODEX_ENABLED_PLUGINS) | set(CODEX_CACHED_PLUGINS)
    for marketplace in CODEX_MARKETPLACES.values():
        plugin_keys.update(f"{name}@{marketplace['name']}" for name in marketplace.get("plugins", {}))

    for plugin_key in sorted(plugin_keys):
        plugin_name, _, marketplace_name = plugin_key.partition("@")
        enabled_entry = CODEX_ENABLED_PLUGINS.get(plugin_key, {})
        cached_entry = CODEX_CACHED_PLUGINS.get(plugin_key, {})
        marketplace_entry = CODEX_MARKETPLACES.get(marketplace_name, {})
        marketplace_plugin = marketplace_entry.get("plugins", {}).get(plugin_name)
        enabled = bool(enabled_entry.get("enabled"))
        cached = bool(cached_entry)

        if enabled and marketplace_entry == {} and not cached:
            add_check("codex_plugins", "fail", "CODEX_PLUGIN_UNKNOWN", plugin_key, "enabled plugin is not present in marketplace metadata or cache", plugin_key, "global")
            continue
        if enabled and not cached:
            add_check("codex_plugins", "fail", "CODEX_PLUGIN_CACHE_MISSING", plugin_key, "enabled plugin has no local cache entry", plugin_key, "global")
            continue
        if not cached:
            add_check("codex_plugins", "pass", "CODEX_PLUGIN_AVAILABLE", marketplace_entry.get("manifest_path", ""), "plugin is available via configured marketplace", plugin_key, "global")
            continue

        plugin_path = Path(cached_entry.get("cache_path", ""))
        manifest = cached_entry.get("plugin_manifest")
        if not isinstance(manifest, dict):
            add_check("codex_plugins", "fail", "CODEX_PLUGIN_MANIFEST_INVALID", cached_entry.get("plugin_json_path", ""), "plugin.json missing or invalid", plugin_key, "global")
            continue

        declared_paths = [
            ("skills", cached_entry.get("skills_path")),
            ("apps", cached_entry.get("apps_path")),
            ("mcp_servers", cached_entry.get("mcp_servers_path")),
        ]
        missing_declared = False
        for label, path_str in declared_paths:
            if not path_str:
                continue
            path = Path(path_str)
            if not path.exists():
                add_check("codex_plugins", "fail", f"CODEX_PLUGIN_{label.upper()}_MISSING", path, f"declared {label} path is missing", plugin_key, "global")
                missing_declared = True

        if missing_declared:
            continue

        if enabled:
            add_check("codex_plugins", "pass", "CODEX_PLUGIN_ENABLED", plugin_path, "enabled Codex plugin cache is healthy", plugin_key, "global")
        elif marketplace_plugin is not None:
            add_check("codex_plugins", "pass", "CODEX_PLUGIN_CACHE_OK", plugin_path, "cached Codex plugin matches configured marketplace", plugin_key, "global")
        else:
            add_check("codex_plugins", "warn", "CODEX_PLUGIN_CACHE_UNTRACKED", plugin_path, "cached Codex plugin is not present in configured marketplace metadata", plugin_key, "global")


def check_registry_health() -> None:
    registry_path = CLAUDE_HOME / "skill-sources.json"
    registry = load_optional_json(registry_path, add_error)
    if registry is None:
        if registry_path.exists():
            add_check("registry", "fail", "REGISTRY_JSON_INVALID", registry_path, "skill-sources.json could not be parsed", "skill-sources.json", "global")
            return
        add_check("registry", "pass", "REGISTRY_ABSENT", registry_path, "skill-sources.json not present", "skill-sources.json", "global")
        return
    if not isinstance(registry, dict):
        add_check("registry", "fail", "REGISTRY_INVALID", registry_path, "registry must be a JSON object", "skill-sources.json", "global")
        return
    if registry.get("schema_version") != 2:
        add_check("registry", "fail", "REGISTRY_SCHEMA_INVALID", registry_path, "schema_version must be 2", "skill-sources.json", "global")
    sources = registry.get("sources", [])
    if not isinstance(sources, list):
        add_check("registry", "fail", "REGISTRY_SOURCES_INVALID", registry_path, "sources must be a list", "skill-sources.json", "global")
        sources = []
    for source in sources:
        if not isinstance(source, dict):
            add_check("registry", "fail", "REGISTRY_SOURCE_INVALID", registry_path, "source entry must be an object", "skill-sources.json", "global")
            continue
        name = source.get("name", "unknown")
        local_path = Path(str(source.get("local_path_resolved") or source.get("local_path") or "")).expanduser()
        if not local_path.exists():
            add_check("registry", "fail", "SOURCE_CLONE_MISSING", local_path, "source clone missing", name, "global")
        else:
            add_check("registry", "pass", "SOURCE_CLONE_OK", local_path, "source clone reachable", name, "global")
    installed_entries = registry.get("installed", [])
    if not isinstance(installed_entries, list):
        add_check("registry", "fail", "REGISTRY_INSTALLED_INVALID", registry_path, "installed must be a list", "skill-sources.json", "global")
        installed_entries = []
    for installed in installed_entries:
        if not isinstance(installed, dict):
            add_check("registry", "fail", "REGISTRY_INSTALLED_ENTRY_INVALID", registry_path, "installed entry must be an object", "skill-sources.json", "global")
            continue
        name = installed.get("name", "unknown")
        installed_as = Path(str(installed.get("installed_as", ""))).expanduser()
        if not installed_as.exists():
            add_check("registry", "fail", "INSTALLED_AS_MISSING", installed_as, "installed_as path missing", name, "global")
        resources_path = Path(str(installed.get("resources_path", ""))).expanduser()
        if installed.get("has_resources") and not resources_path.exists():
            add_check("registry", "fail", "RESOURCES_PATH_MISSING", resources_path, "resources_path missing", name, "global")
    add_pass_if_empty("registry", "registry is healthy", "global", "skill-sources.json")


def check_deprecated_commands() -> None:
    global_commands = sorted((CLAUDE_HOME / "commands").glob("*.md")) if (CLAUDE_HOME / "commands").exists() else []
    if global_commands:
        for command in global_commands:
            add_check("deprecated_commands", "warn", "DEPRECATED_COMMAND", command, "legacy command format detected", command.stem, "global")
    else:
        add_check("deprecated_commands", "pass", "NO_DEPRECATED_COMMANDS", CLAUDE_HOME / "commands", "no global legacy commands", "global-commands", "global")

    if not GIT_ROOT:
        return

    project_commands_dir = GIT_ROOT / ".claude" / "commands"
    project_commands = sorted(project_commands_dir.glob("*.md")) if project_commands_dir.exists() else []
    if project_commands:
        for command in project_commands:
            add_check("deprecated_commands", "warn", "DEPRECATED_COMMAND", command, "legacy command format detected", command.stem, "project")
    else:
        add_check("deprecated_commands", "pass", "NO_DEPRECATED_COMMANDS", project_commands_dir, "no project legacy commands", "project-commands", "project")


def add_codex_presence_check(category: str, subject: str, scope: str, path: Path) -> None:
    status = codex_status(subject, scope)
    if status == "installed":
        add_check(category, "pass", "CODEX_INSTALLED", path, "valid Codex skill install detected", subject, scope)
        return
    if status == "system-preferred":
        add_check(category, "pass", "CODEX_SYSTEM_PREFERRED", path, "Codex .system skill takes precedence", subject, scope)
        return
    if status == "missing":
        add_check(category, "fail", "CODEX_MISSING", path, "legacy mirror metadata exists but Codex install is missing", subject, scope)
        return
    add_check(category, "fail", "CODEX_BROKEN", path, "Codex skill install exists but is invalid", subject, scope)


def check_codex_presence() -> None:
    seen_global: set[str] = set()
    for link_name, link in GLOBAL_LINKS.items():
        link_path = Path(str(link.get("link", CODEX_HOME / "skills" / link_name))).expanduser()
        add_codex_presence_check("codex_presence", link_name, "global", link_path)
        seen_global.add(link_name)

    global_skills_dir = CODEX_HOME / "skills"
    if global_skills_dir.exists():
        for path in sorted(global_skills_dir.iterdir()):
            if path.name.startswith(".") or path.name in seen_global or path.name in SYSTEM_SKILLS:
                continue
            if valid_skill_collection(path):
                continue
            if valid_skill_target(path):
                add_check("codex_presence", "pass", "CODEX_INSTALLED", path, "valid Codex skill install detected", path.name, "global")
                continue
            if path.is_symlink():
                try:
                    resolved = path.resolve(strict=True)
                except FileNotFoundError:
                    add_check("codex_presence", "fail", "CODEX_BROKEN", path, "symlink target missing", path.name, "global")
                    continue
                if valid_skill_target(resolved):
                    add_check("codex_presence", "pass", "CODEX_INSTALLED", path, "valid Codex symlink install detected", path.name, "global")
                else:
                    add_check("codex_presence", "fail", "CODEX_BROKEN", path, "symlink target is not a valid skill", path.name, "global")
                continue
            add_check("codex_presence", "fail", "CODEX_BROKEN", path, "entry exists but is not a valid skill install", path.name, "global")

    if not GIT_ROOT:
        return

    seen_project: set[str] = set()
    for link_name, link in PROJECT_LINKS.items():
        link_path = Path(str(link.get("link", GIT_ROOT / ".agents" / "skills" / link_name))).expanduser()
        add_codex_presence_check("codex_presence", link_name, "project", link_path)
        seen_project.add(link_name)

    project_agents_dir = GIT_ROOT / ".agents" / "skills"
    if project_agents_dir.exists():
        for path in sorted(project_agents_dir.iterdir()):
            if path.name.startswith(".") or path.name in seen_project:
                continue
            if valid_skill_collection(path):
                continue
            if valid_skill_target(path):
                add_check("codex_presence", "pass", "CODEX_INSTALLED", path, "valid Codex skill install detected", path.name, "project")
                continue
            if path.is_symlink():
                try:
                    resolved = path.resolve(strict=True)
                except FileNotFoundError:
                    add_check("codex_presence", "fail", "CODEX_BROKEN", path, "symlink target missing", path.name, "project")
                    continue
                if valid_skill_target(resolved):
                    add_check("codex_presence", "pass", "CODEX_INSTALLED", path, "valid Codex symlink install detected", path.name, "project")
                else:
                    add_check("codex_presence", "fail", "CODEX_BROKEN", path, "symlink target is not a valid skill", path.name, "project")
                continue
            add_check("codex_presence", "fail", "CODEX_BROKEN", path, "entry exists but is not a valid skill install", path.name, "project")


def check_agents_integrity() -> None:
    if not GIT_ROOT:
        return
    agents_dir = GIT_ROOT / ".agents" / "skills"
    if not agents_dir.exists():
        add_check("agents_integrity", "pass", "NO_AGENTS_DIR", agents_dir, ".agents/skills does not exist", ".agents/skills", "project")
        return
    for path in sorted(agents_dir.iterdir()):
        if path.name.startswith("."):
            continue
        manifest_has = path.name in PROJECT_LINKS
        if valid_skill_target(path):
            status = "pass" if manifest_has else "warn"
            code = "AGENT_INSTALL_OK" if manifest_has else "AGENT_INSTALL_UNMANIFESTED"
            reason = "skill install is valid" if manifest_has else "valid install not recorded in legacy manifest"
            add_check("agents_integrity", status, code, path, reason, path.name, "project")
            continue
        if not path.is_symlink():
            add_check("agents_integrity", "fail", "AGENT_INSTALL_INVALID", path, "entry exists but is not a valid skill install", path.name, "project")
            continue
        try:
            resolved = path.resolve(strict=True)
        except FileNotFoundError:
            add_check("agents_integrity", "fail", "AGENT_LINK_BROKEN", path, "symlink target missing", path.name, "project")
            continue
        if valid_skill_target(resolved):
            status = "pass" if manifest_has else "warn"
            code = "AGENT_INSTALL_OK" if manifest_has else "AGENT_INSTALL_UNMANIFESTED"
            reason = "symlink target is valid" if manifest_has else "valid symlink not recorded in legacy manifest"
            add_check("agents_integrity", status, code, path, reason, path.name, "project")
        else:
            add_check("agents_integrity", "fail", "AGENT_LINK_INVALID_TARGET", path, "symlink target is not a valid skill", path.name, "project")


def make_collision_probe(
    *,
    bare_name: str,
    scope: str,
    source_type: str,
    source_id: str,
    source_path: Path,
    format_name: str = "skills",
    display_name: str | None = None,
    codex_state: str | None = None,
) -> dict[str, Any]:
    return {
        "name": bare_name,
        "bare_name": bare_name,
        "display_name": display_name or bare_name,
        "scope": scope,
        "source_type": source_type,
        "source_id": source_id,
        "source_key": build_skill_source_key(
            source_type=source_type,
            scope=scope,
            source_id=source_id,
            bare_name=bare_name,
        ),
        "identity": build_skill_identity(
            source_type=source_type,
            scope=scope,
            source_id=source_id,
            bare_name=bare_name,
            format_name=format_name,
        ),
        "source_path": str(source_path),
        "format": format_name,
        "codex_status": codex_state if codex_state is not None else codex_status(bare_name, scope),
    }


def load_bare_name(path: Path) -> str:
    frontmatter, _ = parse_frontmatter(path, add_error)
    fallback_name = path.parent.name if path.name == "SKILL.md" else path.stem
    return frontmatter.get("name") or fallback_name


def collect_collision_entries() -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []

    global_skills_dir = CLAUDE_HOME / "skills"
    if global_skills_dir.exists():
        for skill_md in sorted(global_skills_dir.glob("*/SKILL.md")):
            bare_name = load_bare_name(skill_md)
            entries.append(
                make_collision_probe(
                    bare_name=bare_name,
                    scope="global",
                    source_type="claude_global",
                    source_id="claude-global",
                    source_path=skill_md,
                )
            )

    if GIT_ROOT:
        project_skills_dir = GIT_ROOT / ".claude" / "skills"
        if project_skills_dir.exists():
            for skill_md in sorted(project_skills_dir.glob("*/SKILL.md")):
                bare_name = load_bare_name(skill_md)
                entries.append(
                    make_collision_probe(
                        bare_name=bare_name,
                        scope="project",
                        source_type="claude_project",
                        source_id=str(GIT_ROOT),
                        source_path=skill_md,
                    )
                )

    installed_plugins, marketplaces = load_plugin_inventory()
    for plugin_key, install_entries in installed_plugins.items():
        install_info = install_entries[0] if isinstance(install_entries, list) and install_entries else {}
        plugin_name, _, marketplace_name = plugin_key.partition("@")
        marketplace_info = marketplaces.get(marketplace_name)
        if marketplace_info is None:
            continue
        manifest_path = Path(marketplace_info.get("installLocation", "")) / ".claude-plugin" / "marketplace.json"
        manifest = load_json(manifest_path, add_error)
        if not isinstance(manifest, dict):
            continue
        plugin_def = next((item for item in manifest.get("plugins", []) if item.get("name") == plugin_name), None)
        if not isinstance(plugin_def, dict):
            continue
        install_path = Path(install_info.get("installPath", "")) if install_info.get("installPath") else None
        skills = plugin_def.get("skills")
        if not install_path or not isinstance(skills, list):
            continue
        for skill_ref in skills:
            skill_dir = install_path / str(skill_ref).lstrip("./")
            skill_md = skill_dir / "SKILL.md"
            bare_name = load_bare_name(skill_md)
            entries.append(
                make_collision_probe(
                    bare_name=bare_name,
                    scope="global",
                    source_type="plugin",
                    source_id=plugin_key,
                    source_path=skill_md,
                    display_name=f"{plugin_name}:{bare_name}",
                )
            )

    for plugin_key, cached_entry in CODEX_CACHED_PLUGINS.items():
        skills_path = cached_entry.get("skills_path")
        if not skills_path:
            continue
        plugin_name, _, _marketplace_name = plugin_key.partition("@")
        for skill_md in sorted(Path(skills_path).glob("*/SKILL.md")):
            bare_name = load_bare_name(skill_md)
            entries.append(
                make_collision_probe(
                    bare_name=bare_name,
                    scope="global",
                    source_type="codex_plugin",
                    source_id=plugin_key,
                    source_path=skill_md,
                    display_name=f"{plugin_name}:{bare_name}",
                    codex_state="installed",
                )
            )

    system_dir = CODEX_HOME / "skills" / ".system"
    for skill_name in sorted(SYSTEM_SKILLS):
        skill_md = system_dir / skill_name / "SKILL.md"
        bare_name = load_bare_name(skill_md)
        entries.append(
            make_collision_probe(
                bare_name=bare_name,
                scope="global",
                source_type="codex_system",
                source_id="codex:.system",
                source_path=skill_md,
                display_name=f"system:{bare_name}",
                codex_state="installed",
            )
        )

    return entries


def check_skill_collisions() -> None:
    collisions = detect_source_collisions(collect_collision_entries())
    if not collisions:
        add_check("skill_collisions", "pass", "NO_COLLISIONS", "", "no cross-source skill name collisions", "skills", "global")
        return

    for collision in collisions:
        bare_name = str(collision.get("bare_name", "unknown"))
        members = collision.get("members", [])
        member_names = ", ".join(str(member.get("display_name") or member.get("identity") or "") for member in members)
        path = members[0].get("source_path", "") if members else ""
        if collision.get("collision_type") == "system-preferred":
            add_check(
                "skill_collisions",
                "warn",
                "SYSTEM_PREFERRED_COLLISION",
                path,
                f"Codex .system takes precedence; colliding entries: {member_names}",
                bare_name,
                "global",
            )
            continue
        add_check(
            "skill_collisions",
            "warn",
            "SKILL_NAME_COLLISION",
            path,
            f"same bare skill name appears in multiple sources: {member_names}",
            bare_name,
            "mixed",
        )


def count_lines(path: Path) -> int:
    with path.open(encoding="utf-8") as handle:
        return sum(1 for _ in handle)


def check_project_skill_format() -> None:
    if not GIT_ROOT:
        return
    skills_dir = GIT_ROOT / ".claude" / "skills"
    if not skills_dir.exists():
        add_check("project_skill_format", "pass", "NO_PROJECT_SKILLS", skills_dir, "no project skills present", "project-skills", "project")
        return
    validator = SKILL_CREATOR_HOME / "scripts" / "quick_validate.py"
    if not validator.exists():
        add_check(
            "project_skill_format",
            "fail",
            "VALIDATOR_NOT_FOUND",
            validator,
            "quick_validate.py not found",
            "quick_validate.py",
            "project",
        )
        return
    for skill_dir in sorted(skills_dir.iterdir()):
        if not skill_dir.is_dir():
            continue
        subject = skill_dir.name
        proc = subprocess.run(
            ["python3", str(validator), str(skill_dir)],
            capture_output=True,
            text=True,
            check=False,
        )
        status = "pass" if proc.returncode == 0 else "fail"
        reason = (proc.stdout or proc.stderr).strip() or "quick_validate.py returned no message"
        add_check("project_skill_format", status, "QUICK_VALIDATE", skill_dir / "SKILL.md", reason, subject, "project")
        skill_md = skill_dir / "SKILL.md"
        if skill_md.exists() and count_lines(skill_md) > 500:
            add_check("project_skill_format", "warn", "SKILL_MD_TOO_LONG", skill_md, "SKILL.md exceeds 500 lines", subject, "project")
        agent_yaml = skill_dir / "agents" / "openai.yaml"
        if agent_yaml.exists():
            add_check("project_skill_format", "warn", "OPENAI_YAML_NOT_VALIDATED", agent_yaml, "agents/openai.yaml exists but is not auto-validated", subject, "project")
        frontmatter, warnings = parse_frontmatter(skill_md, add_error)
        if "compatibility" in frontmatter:
            add_check("project_skill_format", "fail", "COMPATIBILITY_UNSUPPORTED", skill_md, "compatibility is not allowed by quick_validate.py", subject, "project")
        for warning in warnings:
            add_check("project_skill_format", "warn", warning["code"], warning["path"], warning["reason"], subject, "project")


def main() -> None:
    check_marketplace_plugins()
    check_codex_plugins()
    check_registry_health()
    check_deprecated_commands()
    check_skill_collisions()
    check_codex_presence()
    check_agents_integrity()
    check_project_skill_format()
    print(json.dumps(RESULT, ensure_ascii=False))


if __name__ == "__main__":
    main()
