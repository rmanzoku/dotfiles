#!/usr/bin/env python3
from __future__ import annotations

import json
import tomllib
from pathlib import Path
from typing import Any, Callable, Union

ErrorSink = Callable[[str, Union[str, Path], str], None]


def load_json(path: Path, add_error: ErrorSink, missing_code: str = "FILE_NOT_FOUND") -> Any | None:
    try:
        with path.open(encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError:
        add_error(missing_code, path, f"{path.name} not found")
    except json.JSONDecodeError as exc:
        add_error("JSON_PARSE", path, str(exc))
    return None


def load_optional_json(path: Path, add_error: ErrorSink) -> Any | None:
    try:
        with path.open(encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError:
        return None
    except json.JSONDecodeError as exc:
        add_error("JSON_PARSE", path, str(exc))
    return None


def load_optional_toml(path: Path, add_error: ErrorSink) -> Any | None:
    try:
        with path.open("rb") as handle:
            return tomllib.load(handle)
    except FileNotFoundError:
        return None
    except tomllib.TOMLDecodeError as exc:
        add_error("TOML_PARSE", path, str(exc))
    return None


def split_header_value(line: str) -> tuple[str, str] | None:
    if ":" not in line:
        return None
    key, value = line.split(":", 1)
    return key.strip(), value.strip()


def consume_block(lines: list[str], start: int, indicator: str) -> tuple[str, int]:
    folded = indicator.startswith(">")
    idx = start + 1
    chunks: list[str] = []
    while idx < len(lines):
        line = lines[idx]
        if line.startswith("---") and line.strip() == "---":
            break
        if line and not line.startswith((" ", "\t")):
            break
        stripped = line.lstrip(" \t")
        if folded:
            chunks.append(stripped.strip())
        else:
            chunks.append(stripped.rstrip("\n"))
        idx += 1
    if folded:
        text = " ".join(part for part in chunks if part).strip()
    else:
        text = "\n".join(chunks).strip()
    return text, idx


def parse_frontmatter(path: Path, add_error: ErrorSink) -> tuple[dict[str, str], list[dict[str, str]]]:
    warnings: list[dict[str, str]] = []
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        add_error("FILE_READ", path, str(exc))
        return {}, warnings

    if not text.startswith("---\n"):
        return {}, warnings

    lines = text.splitlines()
    idx = 1
    frontmatter: dict[str, str] = {}
    while idx < len(lines):
        line = lines[idx]
        if line.strip() == "---":
            return frontmatter, warnings
        if not line.strip():
            idx += 1
            continue
        parsed = split_header_value(line)
        if parsed is None:
            warnings.append(
                {
                    "code": "UNSUPPORTED_FRONTMATTER_LINE",
                    "path": str(path),
                    "reason": f"unsupported line: {line}",
                }
            )
            idx += 1
            continue
        key, value = parsed
        if value in {">", ">-", ">+", "|", "|-", "|+"}:
            block, idx = consume_block(lines, idx, value)
            frontmatter[key] = block
            continue
        if value.startswith(('"', "'")) and value.endswith(('"', "'")) and len(value) >= 2:
            value = value[1:-1]
        elif value.startswith(("[", "{")):
            warnings.append(
                {
                    "code": "UNSUPPORTED_FRONTMATTER_VALUE",
                    "path": str(path),
                    "reason": f"unsupported complex value for {key}",
                }
            )
            value = ""
        frontmatter[key] = value
        idx += 1

    warnings.append(
        {
            "code": "UNTERMINATED_FRONTMATTER",
            "path": str(path),
            "reason": "frontmatter terminator not found",
        }
    )
    return frontmatter, warnings


def valid_skill_target(target: Path) -> bool:
    return target.exists() and target.is_dir() and (target / "SKILL.md").is_file()


def valid_skill_collection(target: Path) -> bool:
    if not target.exists() or not target.is_dir():
        return False
    for child in target.iterdir():
        if child.is_dir() and (child / "SKILL.md").is_file():
            return True
    return False


def load_manifest_links(path: Path, add_error: ErrorSink) -> dict[str, dict[str, Any]]:
    data = load_json(path, add_error, missing_code="MANIFEST_NOT_FOUND")
    if not isinstance(data, dict):
        return {}
    links = data.get("links", [])
    if not isinstance(links, list):
        add_error("MANIFEST_INVALID", path, "links must be a list")
        return {}
    out: dict[str, dict[str, Any]] = {}
    for link in links:
        if isinstance(link, dict) and "name" in link:
            out[str(link["name"])] = link
    return out


def build_system_skills(codex_home: Path) -> set[str]:
    system_dir = codex_home / "skills" / ".system"
    if not system_dir.exists():
        return set()
    return {entry.name for entry in system_dir.iterdir() if entry.is_dir()}


def resolve_relative_ref(base_dir: Path, ref: str | None) -> Path | None:
    if not ref:
        return None
    return (base_dir / ref).resolve() if ref.startswith(".") else Path(ref).expanduser()


def load_codex_config(codex_home: Path, add_error: ErrorSink) -> dict[str, Any]:
    config = load_optional_toml(codex_home / "config.toml", add_error)
    return config if isinstance(config, dict) else {}


def load_codex_marketplaces(codex_home: Path, add_error: ErrorSink) -> dict[str, dict[str, Any]]:
    config = load_codex_config(codex_home, add_error)
    raw_marketplaces = config.get("marketplaces", {})
    if not isinstance(raw_marketplaces, dict):
        return {}

    marketplaces: dict[str, dict[str, Any]] = {}
    for marketplace_name, entry in raw_marketplaces.items():
        if not isinstance(entry, dict):
            continue
        source_type = str(entry.get("source_type", ""))
        source = str(entry.get("source", ""))
        manifest_path: Path | None = None
        manifest: Any | None = None
        if source_type == "local" and source:
            manifest_path = Path(source).expanduser() / ".agents" / "plugins" / "marketplace.json"
            manifest = load_optional_json(manifest_path, add_error)
        plugins: dict[str, dict[str, Any]] = {}
        if isinstance(manifest, dict):
            for plugin in manifest.get("plugins", []):
                if isinstance(plugin, dict) and plugin.get("name"):
                    plugins[str(plugin["name"])] = plugin
        marketplaces[str(marketplace_name)] = {
            "name": str(marketplace_name),
            "source_type": source_type,
            "source": source,
            "manifest_path": str(manifest_path) if manifest_path else None,
            "manifest": manifest if isinstance(manifest, dict) else None,
            "plugins": plugins,
        }
    return marketplaces


def load_codex_enabled_plugins(codex_home: Path, add_error: ErrorSink) -> dict[str, dict[str, Any]]:
    config = load_codex_config(codex_home, add_error)
    raw_plugins = config.get("plugins", {})
    if not isinstance(raw_plugins, dict):
        return {}
    enabled: dict[str, dict[str, Any]] = {}
    for plugin_key, entry in raw_plugins.items():
        if isinstance(entry, dict):
            enabled[str(plugin_key)] = entry
    return enabled


def load_codex_cached_plugins(codex_home: Path, add_error: ErrorSink) -> dict[str, dict[str, Any]]:
    cache_root = codex_home / "plugins" / "cache"
    cached: dict[str, dict[str, Any]] = {}
    if not cache_root.exists():
        return cached

    for plugin_json in sorted(cache_root.glob("*/*/*/.codex-plugin/plugin.json")):
        try:
            marketplace_name, plugin_name, revision = plugin_json.relative_to(cache_root).parts[:3]
        except ValueError:
            continue
        manifest = load_optional_json(plugin_json, add_error)
        plugin_root = plugin_json.parent.parent
        plugin_key = f"{plugin_name}@{marketplace_name}"
        cached[plugin_key] = {
            "plugin_key": plugin_key,
            "marketplace_name": marketplace_name,
            "plugin_name": plugin_name,
            "revision": revision,
            "cache_path": str(plugin_root),
            "plugin_json_path": str(plugin_json),
            "plugin_manifest": manifest if isinstance(manifest, dict) else None,
            "skills_path": str(resolve_relative_ref(plugin_root, str(manifest.get("skills", "")))) if isinstance(manifest, dict) and manifest.get("skills") else None,
            "apps_path": str(resolve_relative_ref(plugin_root, str(manifest.get("apps", "")))) if isinstance(manifest, dict) and manifest.get("apps") else None,
            "mcp_servers_path": str(resolve_relative_ref(plugin_root, str(manifest.get("mcpServers", "")))) if isinstance(manifest, dict) and manifest.get("mcpServers") else None,
        }
    return cached


def build_skill_source_key(*, source_type: str, scope: str, source_id: str, bare_name: str) -> str:
    return "::".join([source_type, scope, source_id, bare_name])


def build_skill_identity(
    *,
    source_type: str,
    scope: str,
    source_id: str,
    bare_name: str,
    format_name: str,
) -> str:
    return "::".join([source_type, scope, source_id, bare_name, format_name])


def detect_source_collisions(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    buckets: dict[str, dict[str, dict[str, Any]]] = {}
    for entry in entries:
        bare_name = str(entry.get("bare_name") or entry.get("name") or "")
        source_key = str(entry.get("source_key") or "")
        if not bare_name or not source_key:
            continue
        buckets.setdefault(bare_name, {})[source_key] = entry

    collisions: list[dict[str, Any]] = []
    for bare_name in sorted(buckets):
        members = list(buckets[bare_name].values())
        if len(members) < 2:
            continue
        collision_type = (
            "system-preferred"
            if any(member.get("source_type") == "codex_system" for member in members)
            else "source-collision"
        )
        collisions.append(
            {
                "bare_name": bare_name,
                "collision_type": collision_type,
                "members": [
                    {
                        "identity": member.get("identity"),
                        "display_name": member.get("display_name"),
                        "source_type": member.get("source_type"),
                        "source_id": member.get("source_id"),
                        "scope": member.get("scope"),
                        "format": member.get("format"),
                        "source_path": member.get("source_path"),
                        "codex_status": member.get("codex_status"),
                    }
                    for member in members
                ],
            }
        )
    return collisions


def compute_codex_status(
    *,
    name: str,
    scope: str,
    git_root: Path | None,
    codex_home: Path,
    global_links: dict[str, dict[str, Any]],
    project_links: dict[str, dict[str, Any]],
    system_skills: set[str],
) -> str:
    if name in system_skills:
        return "system-preferred"

    if scope == "global":
        install_path = codex_home / "skills" / name
        manifest_links = global_links
    else:
        if not git_root:
            return "missing"
        install_path = git_root / ".agents" / "skills" / name
        manifest_links = project_links

    manifest_has_entry = name in manifest_links
    if install_path.is_symlink():
        try:
            resolved = install_path.resolve(strict=True)
        except FileNotFoundError:
            return "broken"
        if valid_skill_target(resolved):
            return "installed"
        return "broken"
    if install_path.exists():
        if valid_skill_target(install_path):
            return "installed"
        return "broken"
    if manifest_has_entry:
        return "broken"
    return "missing"
