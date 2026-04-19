#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--git-root", default="")
    parser.add_argument("--scope", choices=("global", "project", "all"), default="all")
    parser.add_argument("--format", choices=("shell", "json"), default="shell")
    return parser.parse_args()


ARGS = parse_args()
GIT_ROOT = Path(ARGS.git_root).resolve() if ARGS.git_root else None
CLAUDE_HOME = Path(os.environ.get("SKILL_MANAGER_CLAUDE_HOME", "~/.claude")).expanduser()
REGISTRY_PATH = CLAUDE_HOME / "skill-sources.json"


def load_registry() -> tuple[dict[str, Any] | None, list[dict[str, str]]]:
    errors: list[dict[str, str]] = []
    if not REGISTRY_PATH.exists():
        return None, errors
    try:
        with REGISTRY_PATH.open(encoding="utf-8") as handle:
            data = json.load(handle)
    except json.JSONDecodeError as exc:
        errors.append({"code": "JSON_PARSE", "path": str(REGISTRY_PATH), "reason": str(exc)})
        return None, errors
    if not isinstance(data, dict):
        errors.append({"code": "REGISTRY_INVALID", "path": str(REGISTRY_PATH), "reason": "registry must be an object"})
        return None, errors
    return data, errors


def github_repo_from_value(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    if not text:
        return None
    direct = re.fullmatch(r"([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)", text)
    if direct:
        return direct.group(1)
    patterns = [
        r"github\.com[:/]([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+?)(?:\.git)?(?:/|$)",
        r"^https?://github\.com/([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+?)(?:\.git)?(?:/|$)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1)
    return None


def detect_scope(installed_as: Path) -> str:
    try:
        installed_as.relative_to(CLAUDE_HOME / "skills")
        return "global"
    except ValueError:
        pass
    if GIT_ROOT:
        for base in (GIT_ROOT / ".claude" / "skills", GIT_ROOT / ".agents" / "skills"):
            try:
                installed_as.relative_to(base)
                return "project"
            except ValueError:
                continue
    return "unknown"


def detect_repo(installed: dict[str, Any], sources_by_name: dict[str, dict[str, Any]]) -> str | None:
    candidate_keys = (
        "repo",
        "repository",
        "source_repo",
        "github_repo",
        "repo_url",
        "repository_url",
        "url",
        "source_url",
    )
    for key in candidate_keys:
        repo = github_repo_from_value(installed.get(key))
        if repo:
            return repo
    source_name = installed.get("source_name") or installed.get("source")
    if isinstance(source_name, str):
        source = sources_by_name.get(source_name)
        if source:
            for key in candidate_keys + ("remote", "origin", "clone_url"):
                repo = github_repo_from_value(source.get(key))
                if repo:
                    return repo
    return None


def detect_pin(installed: dict[str, Any], source: dict[str, Any] | None) -> str | None:
    keys = ("pinned_ref", "pin", "ref", "version", "tag", "commit", "sha", "revision")
    for key in keys:
        value = installed.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    if source:
        for key in keys:
            value = source.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    return None


def shell_quote(parts: list[str]) -> str:
    return subprocess.list2cmdline(parts)


def build_shell(result: dict[str, Any]) -> str:
    lines: list[str] = []
    gh_version = result.get("gh_version") or "unknown"
    lines.append(f"# gh skill migration plan")
    lines.append(f"# gh version: {gh_version}")
    lines.append(f"# generated_at: {result['generated_at']}")
    if result["errors"]:
        lines.append("# errors:")
        for error in result["errors"]:
            lines.append(f"# - {error['code']}: {error['reason']}")
    if not result["candidates"] and not result["manual_follow_up"]:
        lines.append("# no legacy skills.sh entries were found")
        return "\n".join(lines)
    for candidate in result["candidates"]:
        lines.append("")
        lines.append(f"# {candidate['name']} ({candidate['scope']}) from {candidate['repository']}")
        if candidate.get("pin"):
            lines.append(f"# suggested pin: {candidate['pin']}")
        lines.append(candidate["preview_command"])
        lines.append(candidate["install_command"])
    if result["manual_follow_up"]:
        lines.append("")
        lines.append("# manual follow-up required")
        for item in result["manual_follow_up"]:
            lines.append(
                f"# - {item['name']} ({item['scope']}): {item['reason']}"
            )
    return "\n".join(lines)


def main() -> None:
    registry, errors = load_registry()
    gh_version = ""
    try:
        gh_version = subprocess.check_output(["gh", "--version"], text=True).splitlines()[0].strip()
    except Exception:
        gh_version = ""

    result: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "gh_version": gh_version,
        "project_root": str(GIT_ROOT) if GIT_ROOT else None,
        "candidates": [],
        "manual_follow_up": [],
        "errors": errors,
    }

    if registry is None:
        output = result if ARGS.format == "json" else build_shell(result)
        print(json.dumps(output, ensure_ascii=False, indent=2) if ARGS.format == "json" else output)
        return

    sources = registry.get("sources", [])
    installed_entries = registry.get("installed", [])
    if not isinstance(sources, list) or not isinstance(installed_entries, list):
        result["errors"].append(
            {"code": "REGISTRY_INVALID", "path": str(REGISTRY_PATH), "reason": "sources and installed must be lists"}
        )
        output = result if ARGS.format == "json" else build_shell(result)
        print(json.dumps(output, ensure_ascii=False, indent=2) if ARGS.format == "json" else output)
        return

    sources_by_name = {
        str(source.get("name")): source for source in sources if isinstance(source, dict) and "name" in source
    }

    for installed in installed_entries:
        if not isinstance(installed, dict):
            continue
        name = str(installed.get("name") or "unknown")
        installed_as_value = str(installed.get("installed_as") or "")
        installed_as = Path(installed_as_value).expanduser() if installed_as_value else Path()
        scope = detect_scope(installed_as) if installed_as_value else "unknown"
        if ARGS.scope != "all" and scope != ARGS.scope:
            continue

        source_name = installed.get("source_name") or installed.get("source")
        source = sources_by_name.get(str(source_name)) if source_name is not None else None
        repository = detect_repo(installed, sources_by_name)
        pin = detect_pin(installed, source)

        if scope == "unknown":
            result["manual_follow_up"].append(
                {
                    "name": name,
                    "scope": scope,
                    "installed_as": installed_as_value,
                    "reason": "could not determine whether the install is global or project scoped",
                }
            )
            continue
        if not repository:
            result["manual_follow_up"].append(
                {
                    "name": name,
                    "scope": scope,
                    "installed_as": installed_as_value,
                    "reason": "could not map legacy metadata to a GitHub repository",
                }
            )
            continue

        gh_scope = "user" if scope == "global" else "project"
        preview_parts = ["gh", "skill", "preview", repository, name]
        install_parts = ["gh", "skill", "install", repository, name, "--agent", "claude-code", "--scope", gh_scope]
        if pin:
            install_parts.extend(["--pin", pin])

        result["candidates"].append(
            {
                "name": name,
                "scope": scope,
                "repository": repository,
                "pin": pin or "",
                "installed_as": installed_as_value,
                "preview_command": shell_quote(preview_parts),
                "install_command": shell_quote(install_parts),
            }
        )

    output = result if ARGS.format == "json" else build_shell(result)
    print(json.dumps(output, ensure_ascii=False, indent=2) if ARGS.format == "json" else output)


if __name__ == "__main__":
    main()
