#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
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
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--full", default="false")
    parser.add_argument("--git-root", default="")
    return parser.parse_args()


def build_result(git_root: Path | None) -> dict[str, Any]:
    return {
        "marketplace_plugins": [],
        "global_skills": [],
        "project_skills": [],
        "codex_marketplaces": [],
        "codex_plugins": [],
        "codex_system_skills": [],
        "skills": [],
        "collisions": [],
        "project_root": str(git_root) if git_root else None,
        "skill_sources": None,
        "errors": [],
    }


ARGS = parse_args()
FULL_MODE = ARGS.full.lower() == "true"
GIT_ROOT = Path(ARGS.git_root).resolve() if ARGS.git_root else None
CLAUDE_HOME = Path(os.environ.get("SKILL_MANAGER_CLAUDE_HOME", "~/.claude")).expanduser()
CODEX_HOME = Path(os.environ.get("SKILL_MANAGER_CODEX_HOME", "~/.codex")).expanduser()
RESULT = build_result(GIT_ROOT)


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


def make_inventory_entry(
    *,
    bare_name: str,
    description: str,
    scope: str,
    source_type: str,
    source_id: str,
    source_path: Path,
    format_name: str,
    warnings: list[dict[str, str]],
    hidden_duplicate: bool = False,
    display_name: str | None = None,
    codex_state: str | None = None,
) -> dict[str, Any]:
    source_key = build_skill_source_key(
        source_type=source_type,
        scope=scope,
        source_id=source_id,
        bare_name=bare_name,
    )
    return {
        "name": bare_name,
        "bare_name": bare_name,
        "display_name": display_name or bare_name,
        "description": description,
        "scope": scope,
        "source_type": source_type,
        "source_id": source_id,
        "source_key": source_key,
        "identity": build_skill_identity(
            source_type=source_type,
            scope=scope,
            source_id=source_id,
            bare_name=bare_name,
            format_name=format_name,
        ),
        "source_path": str(source_path),
        "codex_status": codex_state if codex_state is not None else codex_status(bare_name, scope),
        "format": format_name,
        "deprecated": format_name == "command",
        "hidden_duplicate": hidden_duplicate,
        "warnings": warnings,
    }


def normalize_skill_entry(
    *,
    path: Path,
    scope: str,
    format_name: str,
    hidden_duplicate: bool,
    source_type: str,
    source_id: str,
    display_name: str | None = None,
    codex_state: str | None = None,
) -> dict[str, Any]:
    frontmatter, warnings = parse_frontmatter(path, add_error)
    fallback_name = path.parent.name if path.name == "SKILL.md" else path.stem
    bare_name = frontmatter.get("name") or fallback_name
    description = frontmatter.get("description") or ""
    return make_inventory_entry(
        bare_name=bare_name,
        description=description,
        scope=scope,
        source_type=source_type,
        source_id=source_id,
        source_path=path,
        format_name=format_name,
        warnings=warnings,
        hidden_duplicate=hidden_duplicate,
        display_name=display_name,
        codex_state=codex_state,
    )


def collect_skill_entries(base_dir: Path, scope: str) -> list[dict[str, Any]]:
    skills_by_name: dict[str, dict[str, Any]] = {}
    ordered_entries: list[dict[str, Any]] = []
    source_type = "claude_global" if scope == "global" else "claude_project"
    source_id = "claude-global" if scope == "global" else str(GIT_ROOT or "")

    if base_dir.exists():
        for skill_md in sorted(base_dir.glob("*/SKILL.md")):
            entry = normalize_skill_entry(
                path=skill_md,
                scope=scope,
                format_name="skills",
                hidden_duplicate=False,
                source_type=source_type,
                source_id=source_id,
            )
            skills_by_name[entry["bare_name"]] = entry
            ordered_entries.append(entry)

    commands_dir = base_dir.parent / "commands"
    if commands_dir.exists():
        for command_md in sorted(commands_dir.glob("*.md")):
            entry = normalize_skill_entry(
                path=command_md,
                scope=scope,
                format_name="command",
                hidden_duplicate=False,
                source_type=source_type,
                source_id=source_id,
            )
            if entry["bare_name"] in skills_by_name:
                entry["hidden_duplicate"] = True
            ordered_entries.append(entry)

    return ordered_entries


def collect_marketplace_plugins() -> list[dict[str, Any]]:
    installed_data = load_json(CLAUDE_HOME / "plugins" / "installed_plugins.json", add_error)
    marketplaces_data = load_json(CLAUDE_HOME / "plugins" / "known_marketplaces.json", add_error)
    installed_plugins = installed_data.get("plugins", {}) if isinstance(installed_data, dict) else {}
    marketplaces = marketplaces_data if isinstance(marketplaces_data, dict) else {}
    installed_keys = set(installed_plugins.keys())
    entries: list[dict[str, Any]] = []

    for marketplace_name, info in marketplaces.items():
        install_location = Path(info.get("installLocation", ""))
        manifest_path = install_location / ".claude-plugin" / "marketplace.json"
        manifest = load_json(manifest_path, add_error)
        if not isinstance(manifest, dict):
            continue
        plugins_out: list[dict[str, Any]] = []
        for plugin in manifest.get("plugins", []):
            if not isinstance(plugin, dict) or "name" not in plugin:
                continue
            plugin_key = f"{plugin['name']}@{marketplace_name}"
            is_installed = plugin_key in installed_keys
            if not FULL_MODE and not is_installed:
                continue
            info_entry = installed_plugins.get(plugin_key, [{}])
            install_info = info_entry[0] if isinstance(info_entry, list) and info_entry else {}
            skill_entries: list[dict[str, Any]] = []
            warnings: list[dict[str, str]] = []
            skills = plugin.get("skills")
            install_path = Path(install_info.get("installPath", "")) if install_info.get("installPath") else None
            if is_installed and skills is None:
                warnings.append(
                    {
                        "code": "PLUGIN_SKILLS_UNDEFINED",
                        "path": str(manifest_path),
                        "reason": f"skills is undefined for {plugin['name']}",
                    }
                )
            if is_installed and isinstance(skills, list) and install_path:
                for skill_ref in skills:
                    skill_dir = install_path / str(skill_ref).lstrip("./")
                    skill_path = skill_dir / "SKILL.md"
                    entry = normalize_skill_entry(
                        path=skill_path,
                        scope="global",
                        format_name="skills",
                        hidden_duplicate=False,
                        source_type="plugin",
                        source_id=plugin_key,
                    )
                    entry["display_name"] = f"{plugin['name']}:{entry['bare_name']}"
                    skill_entries.append(entry)
            plugins_out.append(
                {
                    "name": plugin["name"],
                    "source_id": plugin_key,
                    "description": plugin.get("description", ""),
                    "status": "installed" if is_installed else "available",
                    "version": install_info.get("version", ""),
                    "scope": install_info.get("scope", ""),
                    "skills": skill_entries,
                    "warnings": warnings,
                }
            )
        if plugins_out:
            entries.append({"name": marketplace_name, "plugins": plugins_out})
    return entries


def collect_codex_plugin_skills(plugin_key: str, cached_entry: dict[str, Any]) -> list[dict[str, Any]]:
    skills_path = cached_entry.get("skills_path")
    if not skills_path:
        return []
    skills_dir = Path(skills_path)
    if not skills_dir.exists():
        return []
    entries: list[dict[str, Any]] = []
    plugin_name, _, _marketplace_name = plugin_key.partition("@")
    for skill_md in sorted(skills_dir.glob("*/SKILL.md")):
        entry = normalize_skill_entry(
            path=skill_md,
            scope="global",
            format_name="skills",
            hidden_duplicate=False,
            source_type="codex_plugin",
            source_id=plugin_key,
            codex_state="installed",
        )
        entry["display_name"] = f"{plugin_name}:{entry['bare_name']}"
        entries.append(entry)
    return entries


def collect_codex_marketplaces() -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for marketplace_name in sorted(CODEX_MARKETPLACES):
        entry = CODEX_MARKETPLACES[marketplace_name]
        entries.append(
            {
                "name": marketplace_name,
                "source_type": entry.get("source_type", ""),
                "source": entry.get("source", ""),
                "manifest_path": entry.get("manifest_path"),
                "plugin_count": len(entry.get("plugins", {})),
            }
        )
    return entries


def collect_codex_plugins() -> list[dict[str, Any]]:
    plugin_keys = set(CODEX_ENABLED_PLUGINS) | set(CODEX_CACHED_PLUGINS)
    for marketplace in CODEX_MARKETPLACES.values():
        plugin_keys.update(f"{name}@{marketplace['name']}" for name in marketplace.get("plugins", {}))

    entries: list[dict[str, Any]] = []
    for plugin_key in sorted(plugin_keys):
        plugin_name, _, marketplace_name = plugin_key.partition("@")
        enabled_entry = CODEX_ENABLED_PLUGINS.get(plugin_key, {})
        cached_entry = CODEX_CACHED_PLUGINS.get(plugin_key, {})
        marketplace_entry = CODEX_MARKETPLACES.get(marketplace_name, {})
        marketplace_plugin = marketplace_entry.get("plugins", {}).get(plugin_name, {})
        enabled = bool(enabled_entry.get("enabled"))
        cached = bool(cached_entry)
        if enabled and cached:
            status = "enabled"
        elif enabled:
            status = "configured"
        elif cached:
            status = "cached"
        else:
            status = "available"

        manifest = cached_entry.get("plugin_manifest") if cached else {}
        interface = manifest.get("interface", {}) if isinstance(manifest, dict) else {}
        description = manifest.get("description") or marketplace_plugin.get("description", "")
        entries.append(
            {
                "name": plugin_name,
                "source_id": plugin_key,
                "marketplace": marketplace_name,
                "enabled": enabled,
                "cached": cached,
                "status": status,
                "version": manifest.get("version", "") if isinstance(manifest, dict) else "",
                "description": description,
                "display_name": interface.get("displayName") or plugin_name,
                "cache_path": cached_entry.get("cache_path"),
                "plugin_json_path": cached_entry.get("plugin_json_path"),
                "skills_path": cached_entry.get("skills_path"),
                "apps_path": cached_entry.get("apps_path"),
                "mcp_servers_path": cached_entry.get("mcp_servers_path"),
                "skills": collect_codex_plugin_skills(plugin_key, cached_entry),
            }
        )
    return entries


def collect_codex_system_skills() -> list[dict[str, Any]]:
    system_dir = CODEX_HOME / "skills" / ".system"
    entries: list[dict[str, Any]] = []
    if not system_dir.exists():
        return entries
    for skill_name in sorted(SYSTEM_SKILLS):
        skill_path = system_dir / skill_name / "SKILL.md"
        entry = normalize_skill_entry(
            path=skill_path,
            scope="global",
            format_name="skills",
            hidden_duplicate=False,
            source_type="codex_system",
            source_id="codex:.system",
            codex_state="installed",
        )
        entry["display_name"] = f"system:{entry['bare_name']}"
        entries.append(entry)
    return entries


def flatten_inventory() -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    entries.extend(RESULT["global_skills"])
    entries.extend(RESULT["project_skills"])
    entries.extend(RESULT["codex_system_skills"])
    for marketplace in RESULT["marketplace_plugins"]:
        for plugin in marketplace.get("plugins", []):
            entries.extend(plugin.get("skills", []))
    for plugin in RESULT["codex_plugins"]:
        entries.extend(plugin.get("skills", []))
    return entries


def main() -> None:
    RESULT["marketplace_plugins"] = collect_marketplace_plugins()
    RESULT["global_skills"] = collect_skill_entries(CLAUDE_HOME / "skills", "global")
    if GIT_ROOT:
        RESULT["project_skills"] = collect_skill_entries(GIT_ROOT / ".claude" / "skills", "project")
    RESULT["codex_marketplaces"] = collect_codex_marketplaces()
    RESULT["codex_plugins"] = collect_codex_plugins()
    RESULT["codex_system_skills"] = collect_codex_system_skills()
    RESULT["skills"] = flatten_inventory()
    RESULT["collisions"] = detect_source_collisions(RESULT["skills"])
    skill_sources = load_optional_json(CLAUDE_HOME / "skill-sources.json", add_error)
    if skill_sources is not None:
        RESULT["skill_sources"] = skill_sources
    print(json.dumps(RESULT, ensure_ascii=False))


if __name__ == "__main__":
    main()
