#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


BOOTSTRAP_KEYWORDS = (
    "初期化",
    "bootstrap",
    "scaffold",
    "雛形",
    "テンプレート",
    "starter",
    "ひな形",
    "叩き台を作る",
)

CATEGORY_VALUES = (
    "docs-index",
    "architecture",
    "services",
    "design-system",
    "operational",
    "entrypoint",
    "spec-structure",
    "size",
)

CATEGORY_ORDER = {
    "docs-index": 0,
    "architecture": 1,
    "services": 2,
    "design-system": 3,
    "operational": 4,
    "entrypoint": 5,
    "spec-structure": 6,
    "size": 7,
}

SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}

SECTION_BY_CATEGORY = {
    "docs-index": "docs構造改善提案",
    "architecture": "docs構造改善提案",
    "services": "docs構造改善提案",
    "design-system": "docs構造改善提案",
    "operational": "docs構造改善提案",
    "entrypoint": "Agent探索評価",
    "spec-structure": "Agent探索評価",
    "size": "構造レベルの書き換え候補",
}

BOOTSTRAP_TARGETS = {
    "README.md": {
        "priority": "high",
        "sections": ["リポジトリ概要", "最初に読む docs", "主要ディレクトリ", "開発ルール"],
        "starter_content_type": "outline",
        "report_section": "提案ファイル一覧",
        "reason": "repo 全体の入口を固定するため",
    },
    "docs/README.md": {
        "priority": "high",
        "sections": ["Docs Index", "読み順", "正規ソース", "更新時チェック"],
        "starter_content_type": "outline",
        "report_section": "提案ファイル一覧",
        "reason": "docs の導線と正本を固定するため",
    },
    "AGENTS.md": {
        "priority": "high",
        "sections": ["リポジトリの目的", "最初に読む docs", "ドキュメント正本", "Agent探索ルール"],
        "starter_content_type": "agent-entrypoint-snippet",
        "report_section": "提案ファイル一覧",
        "reason": "agent 向け入口を repo 直下に置くため",
    },
    "docs/architecture/overview.md": {
        "priority": "medium",
        "sections": ["Responsibility", "Depends On", "Owns Data", "Flow"],
        "starter_content_type": "outline",
        "report_section": "提案ファイル一覧",
        "reason": "architecture 理解を集約するため",
    },
    "docs/services/README.md": {
        "priority": "medium",
        "sections": ["サービス一覧", "責務", "依存関係", "所有データ"],
        "starter_content_type": "outline",
        "report_section": "提案ファイル一覧",
        "reason": "service docs の入口を固定するため",
    },
    "docs/design-system/README.md": {
        "priority": "medium",
        "sections": ["コンポーネント一覧", "利用原則", "参照先"],
        "starter_content_type": "outline",
        "report_section": "提案ファイル一覧",
        "reason": "design system docs を集約するため",
    },
    "docs/adr/0001-record-docs-bootstrap-rules.md": {
        "priority": "medium",
        "sections": ["Status", "Date", "Worked At", "Agent Model", "Context", "Decision", "Consequences"],
        "starter_content_type": "adr-snippet",
        "report_section": "提案ファイル一覧",
        "reason": "docs bootstrap の運用判断を記録するため",
    },
}

TEXT_EXTENSIONS = {".md", ".txt", ".rst"}

AREA_CONFIG = {
    "architecture": {
        "recommended_paths": ["docs/architecture/overview.md", "docs/architecture/README.md"],
        "canonical_prefixes": ["docs/architecture", "docs/arch"],
        "search_keywords": ("architecture", "arch", "system", "design", "concept"),
        "missing_severity": "high",
        "normalize_severity": "medium",
        "missing_message": "architecture docs の入口が見つかりません。",
        "normalize_message": "architecture 相当の docs はありますが、推奨パスに正規化されていません。",
        "missing_fix": "architecture の overview または index を追加してください。",
        "normalize_fix": "既存 docs を推奨パスへ寄せ、README/index からそこを正本として参照してください。",
    },
    "services": {
        "recommended_paths": ["docs/services/README.md"],
        "canonical_prefixes": ["docs/services", "docs/service"],
        "search_keywords": ("service", "services", "module", "modules", "api"),
        "missing_severity": "medium",
        "normalize_severity": "medium",
        "missing_message": "service docs の入口が見つかりません。",
        "normalize_message": "service 相当の docs はありますが、推奨パスに正規化されていません。",
        "missing_fix": "サービス一覧または責務一覧を置いてください。",
        "normalize_fix": "既存の service 関連 docs を推奨パスへマップし、service index から辿れるようにしてください。",
    },
    "design-system": {
        "recommended_paths": ["docs/design-system/README.md"],
        "canonical_prefixes": ["docs/design-system", "docs/design_system", "docs/ui"],
        "search_keywords": ("design-system", "design_system", "component", "components", "ui"),
        "missing_severity": "medium",
        "normalize_severity": "medium",
        "missing_message": "design-system docs の入口が見つかりません。",
        "normalize_message": "design-system 相当の docs はありますが、推奨パスに正規化されていません。",
        "missing_fix": "design system の index または component catalog を追加してください。",
        "normalize_fix": "既存の UI / component docs を推奨パスへ寄せ、design-system index から参照してください。",
    },
    "operational": {
        "recommended_paths": ["docs/adr/", "docs/runbooks/", "docs/governance/"],
        "canonical_prefixes": ["docs/adr", "docs/governance", "docs/standards", "docs/contributing", "docs/runbooks"],
        "search_keywords": ("adr", "runbook", "governance", "contributing", "guide", "playbook", "rules", "workflow"),
        "missing_severity": "medium",
        "normalize_severity": "low",
        "missing_message": "運用文書または ADR への入口が見つかりません。",
        "normalize_message": "運用文書はありますが、推奨パスに正規化されていません。",
        "missing_fix": "docs/adr/ などに運用判断を記録してください。",
        "normalize_fix": "既存の運用文書を docs/adr や docs/runbooks などの推奨パスへ整理してください。",
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Diagnose repo docs for AI-agent readability.")
    parser.add_argument("--target-repo", default=".", help="Target repository path. Defaults to current directory.")
    parser.add_argument("--reference-repo", default=None, help="Optional reference repository path.")
    parser.add_argument(
        "--request-text",
        default="",
        help="Original user request used for diagnose/bootstrap mode routing.",
    )
    parser.add_argument(
        "--mode",
        choices=("auto", "diagnose", "bootstrap"),
        default="auto",
        help="Mode override. Default is auto.",
    )
    return parser.parse_args()


def choose_mode(mode: str, request_text: str) -> str:
    if mode != "auto":
        return mode
    lowered = request_text.lower()
    for keyword in BOOTSTRAP_KEYWORDS:
        if keyword.lower() in lowered:
            return "bootstrap"
    return "diagnose"


def ensure_repo(path_str: str) -> Path:
    path = Path(path_str).resolve()
    if not path.exists():
        raise FileNotFoundError(f"target repo not found: {path}")
    if not path.is_dir():
        raise NotADirectoryError(f"target repo is not a directory: {path}")
    return path


def safe_rel(path: Path, base: Path) -> str:
    try:
        return str(path.relative_to(base))
    except ValueError:
        return str(path)


def first_existing(base: Path, candidates: list[str]) -> Path | None:
    for candidate in candidates:
        path = base / candidate
        if path.exists():
            return path
    return None


def contains_docs_links(path: Path) -> bool:
    if not path or not path.exists() or not path.is_file():
        return False
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = path.read_text(encoding="utf-8", errors="ignore")
    return "docs/" in text or "docs\\" in text


def contains_reading_order(path: Path) -> bool:
    if not path or not path.exists() or not path.is_file():
        return False
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = path.read_text(encoding="utf-8", errors="ignore")
    patterns = ("読み順", "最初に読む", "read this first", "docs index", "探索してください")
    return any(p in text.lower() for p in [x.lower() for x in patterns])


def find_matches(base: Path, prefixes: list[str]) -> list[Path]:
    matches: list[Path] = []
    for prefix in prefixes:
        path = base / prefix
        if path.exists():
            matches.append(path)
    return sorted(set(matches))


def discover_docs_candidates(base: Path, keywords: tuple[str, ...], excluded_prefixes: list[str]) -> list[str]:
    docs_dir = base / "docs"
    if not docs_dir.exists():
        return []
    results: list[str] = []
    excluded = tuple(excluded_prefixes)
    for path in docs_dir.rglob("*"):
        if not path.exists():
            continue
        rel = safe_rel(path, base)
        if rel.startswith(excluded):
            continue
        if path.is_file() and path.suffix.lower() not in TEXT_EXTENSIONS:
            continue
        lowered = rel.lower()
        if any(keyword in lowered for keyword in keywords):
            results.append(rel)
    return sorted(set(results))


def scan_large_docs(base: Path) -> list[dict]:
    findings = []
    for path in base.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in TEXT_EXTENSIONS:
            continue
        try:
            size = path.stat().st_size
            with path.open("r", encoding="utf-8", errors="ignore") as fh:
                lines = sum(1 for _ in fh)
        except OSError:
            continue
        if lines > 300 or size > 12 * 1024:
            findings.append(
                {
                    "severity": "medium",
                    "category": "size",
                    "message": "巨大な docs 候補があり、AI の chunk 取得効率を落とす可能性があります。",
                    "evidence": {
                        "path": safe_rel(path, base),
                        "lines": lines,
                        "bytes": size,
                    },
                    "suggested_fix": "topic 単位で分割し、README または index から参照してください。",
                    "report_section": "構造レベルの書き換え候補",
                }
            )
    return findings


def add_missing(
    findings: list[dict],
    *,
    severity: str,
    category: str,
    message: str,
    evidence: dict,
    suggested_fix: str,
) -> None:
    findings.append(
        {
            "severity": severity,
            "category": category,
            "message": message,
            "evidence": evidence,
            "suggested_fix": suggested_fix,
            "report_section": SECTION_BY_CATEGORY[category],
        }
    )


def build_checks(repo: Path, reference_repo: Path | None) -> list[dict]:
    checks = []
    checks.append({"name": "target_exists", "ok": repo.exists(), "details": safe_rel(repo, repo)})
    checks.append(
        {
            "name": "reference_enabled",
            "ok": reference_repo is not None,
            "details": str(reference_repo) if reference_repo else "comparison disabled",
        }
    )
    return checks


def summarize(findings: list[dict], mode: str) -> dict:
    counts = {key: 0 for key in SEVERITY_ORDER}
    for finding in findings:
        counts[finding["severity"]] += 1
    return {
        "mode": mode,
        "finding_counts": counts,
        "has_high_priority_issues": counts["critical"] > 0 or counts["high"] > 0,
    }


def sort_and_trim(findings: list[dict]) -> list[dict]:
    findings.sort(
        key=lambda item: (
            SEVERITY_ORDER[item["severity"]],
            CATEGORY_ORDER[item["category"]],
            item["evidence"].get("path", ""),
        )
    )
    capped: list[dict] = []
    per_severity = {key: 0 for key in SEVERITY_ORDER}
    has_high_priority = any(item["severity"] in {"critical", "high"} for item in findings)
    for finding in findings:
        if has_high_priority and finding["severity"] == "low" and finding["category"] == "size":
            continue
        if per_severity[finding["severity"]] >= 3:
            continue
        per_severity[finding["severity"]] += 1
        capped.append(finding)
    return capped


def detect(repo: Path, mode: str, reference_repo: Path | None) -> dict:
    findings: list[dict] = []
    notes: list[str] = []

    root_readme = first_existing(repo, ["README.md", "README", "README.txt"])
    docs_index = first_existing(repo, ["docs/README.md", "docs/index.md"])
    architecture_matches = find_matches(repo, AREA_CONFIG["architecture"]["canonical_prefixes"])
    services_matches = find_matches(repo, AREA_CONFIG["services"]["canonical_prefixes"])
    design_system_matches = find_matches(repo, AREA_CONFIG["design-system"]["canonical_prefixes"])
    operational_matches = find_matches(repo, AREA_CONFIG["operational"]["canonical_prefixes"])
    entrypoint_matches = find_matches(repo, ["AGENTS.md", "CLAUDE.md", "docs/agent_entrypoint.md", "docs/agents/README.md"])

    if root_readme is None:
        add_missing(
            findings,
            severity="high",
            category="docs-index",
            message="repo 直下の README が見つかりません。",
            evidence={"path": ""},
            suggested_fix="README.md を追加し、docs への導線を明記してください。",
        )
    elif not contains_docs_links(root_readme):
        add_missing(
            findings,
            severity="medium",
            category="docs-index",
            message="README に docs への明確な導線が見つかりません。",
            evidence={"path": safe_rel(root_readme, repo)},
            suggested_fix="docs/README.md または docs/index.md へのリンクを追加してください。",
        )

    if docs_index is None:
        add_missing(
            findings,
            severity="high",
            category="docs-index",
            message="docs index が見つかりません。",
            evidence={"path": "docs/README.md or docs/index.md"},
            suggested_fix="docs の読み順と正本を示す index を作成してください。",
        )
    elif not contains_reading_order(docs_index):
        add_missing(
            findings,
            severity="high",
            category="entrypoint",
            message="docs index に読み順が見つかりません。",
            evidence={"path": safe_rel(docs_index, repo)},
            suggested_fix="最初に読む docs の順序を明記してください。",
        )

    for category, canonical_matches in [
        ("architecture", architecture_matches),
        ("services", services_matches),
        ("design-system", design_system_matches),
        ("operational", operational_matches),
    ]:
        config = AREA_CONFIG[category]
        if canonical_matches:
            continue
        discovered = discover_docs_candidates(repo, config["search_keywords"], config["canonical_prefixes"])
        if discovered:
            add_missing(
                findings,
                severity=config["normalize_severity"],
                category=category,
                message=config["normalize_message"],
                evidence={
                    "detected_paths": discovered[:5],
                    "recommended_paths": config["recommended_paths"],
                },
                suggested_fix=config["normalize_fix"],
            )
        else:
            add_missing(
                findings,
                severity=config["missing_severity"],
                category=category,
                message=config["missing_message"],
                evidence={"recommended_paths": config["recommended_paths"]},
                suggested_fix=config["missing_fix"],
            )

    if not entrypoint_matches:
        add_missing(
            findings,
            severity="high",
            category="entrypoint",
            message="agent 向け入口ファイルが見つかりません。",
            evidence={"path": "AGENTS.md or equivalent"},
            suggested_fix="AGENTS.md などの agent entrypoint を追加してください。",
        )

    specs_dir = repo / "docs" / "specs"
    if specs_dir.exists():
        bad_specs = []
        for child in sorted(specs_dir.iterdir()):
            if not child.is_dir():
                continue
            required = {"SPEC.md", "ACCEPTANCE.md", "TASKS.md"}
            present = {p.name for p in child.iterdir() if p.is_file()}
            if not required.issubset(present):
                bad_specs.append({"path": safe_rel(child, repo), "missing": sorted(required - present)})
        if bad_specs:
            add_missing(
                findings,
                severity="medium",
                category="spec-structure",
                message="spec ディレクトリの必須成果物が揃っていません。",
                evidence={"items": bad_specs[:5]},
                suggested_fix="各 feature に SPEC.md / ACCEPTANCE.md / TASKS.md を揃えてください。",
            )

    findings.extend(scan_large_docs(repo))

    if reference_repo is None:
        notes.append("reference_repo が未指定または利用不能のため、cross-repo 比較はスキップしました。")
    else:
        notes.append(f"reference_repo={reference_repo} を比較ヒューリスティクス用に読み取りました。")

    findings = sort_and_trim(findings)
    bootstrap_candidates = build_bootstrap_candidates(repo, mode)
    checks = build_checks(repo, reference_repo)
    summary = summarize(findings, mode)

    return {
        "target_repo": str(repo),
        "reference_repo": str(reference_repo) if reference_repo else None,
        "mode": mode,
        "summary": summary,
        "findings": findings,
        "checks": checks,
        "bootstrap_candidates": bootstrap_candidates,
        "notes": notes,
    }


def build_bootstrap_candidates(repo: Path, mode: str) -> list[dict]:
    candidates = []
    for path, spec in BOOTSTRAP_TARGETS.items():
        full_path = repo / path
        if full_path.exists():
            continue
        existing_sources = discover_bootstrap_sources(repo, path)
        candidate = {
            "path": path,
            "reason": spec["reason"],
            "priority": spec["priority"],
            "sections": spec["sections"],
            "starter_content_type": spec["starter_content_type"],
            "report_section": spec["report_section"],
        }
        if existing_sources:
            candidate["reason"] = f"{spec['reason']} 既存 docs を推奨パスへ正規化する候補があります。"
            candidate["source_paths"] = existing_sources[:5]
        if mode == "bootstrap":
            candidate["starter_snippet"] = starter_snippet_for(path)
        candidates.append(candidate)
    candidates.sort(key=lambda item: ({"high": 0, "medium": 1, "low": 2}[item["priority"]], item["path"]))
    return candidates


def starter_snippet_for(path: str) -> str:
    snippets = {
        "README.md": "## Repository Overview\\n- この repo の責務\\n- 最初に読む docs\\n- 主要ディレクトリ\\n",
        "docs/README.md": "# Docs Index\\n\\n## 読み順\\n1. README.md\\n2. docs/architecture/overview.md\\n",
        "AGENTS.md": "# Agent Entrypoint\\n\\n## 1. リポジトリの目的\\n- 主な責務\\n",
        "docs/architecture/overview.md": "# Architecture Overview\\n\\n## Responsibility\\n- 主要責務\\n",
        "docs/services/README.md": "# Services Index\\n\\n## サービス一覧\\n- name\\n- responsibility\\n",
        "docs/design-system/README.md": "# Design System Index\\n\\n## コンポーネント一覧\\n- component\\n- purpose\\n",
        "docs/adr/0001-record-docs-bootstrap-rules.md": "# ADR\\n\\n- Status: Proposed\\n- Date: YYYY-MM-DD\\n",
    }
    return snippets.get(path, "")


def discover_bootstrap_sources(repo: Path, target_path: str) -> list[str]:
    mapping = {
        "docs/architecture/overview.md": discover_docs_candidates(
            repo, AREA_CONFIG["architecture"]["search_keywords"], AREA_CONFIG["architecture"]["canonical_prefixes"]
        ),
        "docs/services/README.md": discover_docs_candidates(
            repo, AREA_CONFIG["services"]["search_keywords"], AREA_CONFIG["services"]["canonical_prefixes"]
        ),
        "docs/design-system/README.md": discover_docs_candidates(
            repo, AREA_CONFIG["design-system"]["search_keywords"], AREA_CONFIG["design-system"]["canonical_prefixes"]
        ),
        "docs/adr/0001-record-docs-bootstrap-rules.md": discover_docs_candidates(
            repo, AREA_CONFIG["operational"]["search_keywords"], AREA_CONFIG["operational"]["canonical_prefixes"]
        ),
        "AGENTS.md": ["README.md"] if (repo / "README.md").exists() else [],
        "docs/README.md": ["README.md"] if (repo / "README.md").exists() else [],
    }
    return mapping.get(target_path, [])


def main() -> int:
    args = parse_args()
    repo = ensure_repo(args.target_repo)
    mode = choose_mode(args.mode, args.request_text)

    reference_repo = None
    if args.reference_repo:
        try:
            reference_repo = ensure_repo(args.reference_repo)
        except (FileNotFoundError, NotADirectoryError):
            reference_repo = None

    result = detect(repo, mode, reference_repo)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
