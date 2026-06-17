#!/usr/bin/env python3
"""Scan AI usage coach reports for obvious non-shareable content."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


PATTERNS = [
    ("email", re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")),
    ("absolute_path", re.compile(r"(^|[\s\"'`])/(Users|home)/[^\s\"'`]+")),
    ("op_reference", re.compile(r"op://[^\s\"'`]+")),
    ("base_instructions", re.compile(r"base_instructions|system_prompt|system[_ -]?prompt\s*[:=]|You are Codex", re.I)),
    ("token_assignment", re.compile(r"(?i)(api[_-]?key|access[_-]?token|secret|password)\s*[:=]\s*['\"]?[^'\"\s]{8,}")),
    ("long_json_content", re.compile(r'"content"\s*:\s*"[^"]{120,}"')),
]


def scan(path: Path) -> list[tuple[str, int, str]]:
    findings: list[tuple[str, int, str]] = []
    text = path.read_text(encoding="utf-8", errors="replace")
    for lineno, line in enumerate(text.splitlines(), 1):
        for name, pattern in PATTERNS:
            if pattern.search(line):
                excerpt = line.strip()
                if len(excerpt) > 160:
                    excerpt = excerpt[:157] + "..."
                findings.append((name, lineno, excerpt))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="+", help="Report files to scan")
    parser.add_argument("--mode", choices=["trusted-local", "shareable", "teacher-pack"], default="shareable")
    args = parser.parse_args()

    all_findings: list[tuple[Path, str, int, str]] = []
    for raw_path in args.paths:
        path = Path(raw_path)
        if not path.exists():
            print(f"ERROR: missing file: {path}", file=sys.stderr)
            return 2
        for name, lineno, excerpt in scan(path):
            all_findings.append((path, name, lineno, excerpt))

    if not all_findings:
        print("OK: no obvious privacy findings")
        return 0

    for path, name, lineno, excerpt in all_findings:
        print(f"{path}:{lineno}: {name}: {excerpt}")

    if args.mode == "trusted-local":
        print("WARN: findings present in trusted-local mode; keep report private", file=sys.stderr)
        return 0

    print("FAIL: findings are not allowed in shareable/teacher-pack mode", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
