#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from common import (
    build_system_skills,
    compute_sync_state,
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


def skill_sync_state(name: str, scope: str) -> tuple[str, bool, bool]:
    return compute_sync_state(
        name=name,
        scope=scope,
        git_root=GIT_ROOT,
        codex_home=CODEX_HOME,
        global_links=GLOBAL_LINKS,
        project_links=PROJECT_LINKS,
        system_skills=SYSTEM_SKILLS,
    )


def normalize_skill_entry(*, path: Path, scope: str, format_name: str, hidden_duplicate: bool) -> dict[str, Any]:
    frontmatter, warnings = parse_frontmatter(path, add_error)
    fallback_name = path.parent.name if path.name == "SKILL.md" else path.stem
    name = frontmatter.get("name") or fallback_name
    description = frontmatter.get("description") or ""
    sync_state, codex_synced, codex_system = skill_sync_state(name, scope)
    return {
        "name": name,
        "description": description,
        "codex_synced": codex_synced,
        "codex_system": codex_system,
        "sync_state": sync_state,
        "format": format_name,
        "deprecated": format_name == "command",
        "hidden_duplicate": hidden_duplicate,
        "warnings": warnings,
    }


def collect_skill_entries(base_dir: Path, scope: str) -> list[dict[str, Any]]:
    skills_by_name: dict[str, dict[str, Any]] = {}
    ordered_entries: list[dict[str, Any]] = []

    if base_dir.exists():
        for skill_md in sorted(base_dir.glob("*/SKILL.md")):
            entry = normalize_skill_entry(
                path=skill_md,
                scope=scope,
                format_name="skills",
                hidden_duplicate=False,
            )
            skills_by_name[entry["name"]] = entry
            ordered_entries.append(entry)

    commands_dir = base_dir.parent / "commands"
    if commands_dir.exists():
        for command_md in sorted(commands_dir.glob("*.md")):
            entry = normalize_skill_entry(
                path=command_md,
                scope=scope,
                format_name="command",
                hidden_duplicate=False,
            )
            if entry["name"] in skills_by_name:
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
                    frontmatter, skill_warnings = parse_frontmatter(skill_path, add_error)
                    skill_name = frontmatter.get("name") or skill_dir.name
                    sync_state, codex_synced, codex_system = skill_sync_state(skill_name, "global")
                    skill_entries.append(
                        {
                            "name": skill_name,
                            "description": frontmatter.get("description") or "",
                            "codex_synced": codex_synced,
                            "codex_system": codex_system,
                            "sync_state": sync_state,
                            "warnings": skill_warnings,
                        }
                    )
            plugins_out.append(
                {
                    "name": plugin["name"],
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


def main() -> None:
    RESULT["marketplace_plugins"] = collect_marketplace_plugins()
    RESULT["global_skills"] = collect_skill_entries(CLAUDE_HOME / "skills", "global")
    if GIT_ROOT:
        RESULT["project_skills"] = collect_skill_entries(GIT_ROOT / ".claude" / "skills", "project")
    skill_sources = load_optional_json(CLAUDE_HOME / "skill-sources.json", add_error)
    if skill_sources is not None:
        RESULT["skill_sources"] = skill_sources
    print(json.dumps(RESULT, ensure_ascii=False))


if __name__ == "__main__":
    main()
