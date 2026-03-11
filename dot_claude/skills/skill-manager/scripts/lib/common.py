#!/usr/bin/env python3
from __future__ import annotations

import json
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


def compute_sync_state(
    *,
    name: str,
    scope: str,
    git_root: Path | None,
    codex_home: Path,
    global_links: dict[str, dict[str, Any]],
    project_links: dict[str, dict[str, Any]],
    system_skills: set[str],
) -> tuple[str, bool, bool]:
    if name in system_skills:
        return "system", True, True

    if scope == "global":
        link_path = codex_home / "skills" / name
        manifest_links = global_links
    else:
        if not git_root:
            return "unsynced", False, False
        link_path = git_root / ".agents" / "skills" / name
        manifest_links = project_links

    manifest_has_entry = name in manifest_links
    if link_path.is_symlink():
        try:
            resolved = link_path.resolve(strict=True)
        except FileNotFoundError:
            return "broken", False, False
        if valid_skill_target(resolved):
            return "synced", True, False
        return "broken", False, False
    if manifest_has_entry:
        return "broken", False, False
    if link_path.exists():
        return "broken", False, False
    return "unsynced", False, False
