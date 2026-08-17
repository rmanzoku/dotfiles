#!/usr/bin/env python3
"""Refresh git branch state: fetch, fast-forward tracking branches that are behind,
delete local branches already merged into the default remote branch, delete merged
origin branches when the repository is private, and report remote branch / PR state."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass
class CmdResult:
    code: int
    stdout: str
    stderr: str


def run(cmd: list[str], cwd: Path, check: bool = False) -> CmdResult:
    proc = subprocess.run(
        cmd,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    result = CmdResult(proc.returncode, proc.stdout.strip(), proc.stderr.strip())
    if check and result.code != 0:
        raise RuntimeError(f"{' '.join(cmd)} failed: {result.stderr or result.stdout}")
    return result


def git(cwd: Path, *args: str, check: bool = False) -> CmdResult:
    return run(["git", *args], cwd, check=check)


def quote_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ").strip() or "-"


def current_branch(cwd: Path) -> str:
    result = git(cwd, "branch", "--show-current", check=True)
    return result.stdout or "(detached)"


def upstream_for(cwd: Path, branch: str) -> str:
    if branch == "(detached)":
        return ""
    result = git(cwd, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}")
    return result.stdout if result.code == 0 else ""


def ahead_behind(cwd: Path, left: str, right: str) -> tuple[int, int] | None:
    result = git(cwd, "rev-list", "--left-right", "--count", f"{left}...{right}")
    if result.code != 0:
        return None
    left_count, right_count = result.stdout.split()
    return int(left_count), int(right_count)


def default_ref(cwd: Path) -> str:
    origin_head = git(cwd, "symbolic-ref", "-q", "--short", "refs/remotes/origin/HEAD")
    if origin_head.code == 0 and origin_head.stdout:
        return origin_head.stdout
    for candidate in ("origin/main", "origin/master"):
        if git(cwd, "show-ref", "--verify", "--quiet", f"refs/remotes/{candidate}").code == 0:
            return candidate
    return ""


def local_branches(cwd: Path) -> list[dict[str, str]]:
    fmt = "%(refname:short)%00%(upstream:short)%00%(committerdate:iso8601)%00%(objectname:short)%00%(objectname)%00%(subject)"
    result = git(cwd, "for-each-ref", "refs/heads", f"--format={fmt}", "--sort=-committerdate", check=True)
    rows: list[dict[str, str]] = []
    for line in result.stdout.splitlines():
        name, upstream, updated, sha, oid, subject = (line.split("\0") + [""] * 6)[:6]
        rows.append(
            {"name": name, "upstream": upstream, "updated": updated, "sha": sha, "oid": oid, "subject": subject}
        )
    return rows


def remote_branches(cwd: Path) -> list[dict[str, str]]:
    fmt = "%00".join(
        [
            "%(refname:short)",
            "%(committerdate:iso8601)",
            "%(objectname)",
            "%(objectname:short)",
            "%(subject)",
        ]
    )
    result = git(
        cwd,
        "for-each-ref",
        "refs/remotes/origin",
        f"--format={fmt}",
        "--sort=-committerdate",
        check=True,
    )
    rows: list[dict[str, str]] = []
    for line in result.stdout.splitlines():
        ref, updated, oid, sha, subject = (line.split("\0") + [""] * 5)[:5]
        if ref == "origin/HEAD" or not ref.startswith("origin/"):
            continue
        rows.append(
            {
                "ref": ref,
                "name": ref.removeprefix("origin/"),
                "updated": updated,
                "oid": oid,
                "sha": sha,
                "subject": subject,
            }
        )
    return rows


def worktree_branches(cwd: Path) -> dict[str, str]:
    """Map branch name -> worktree path for every branch checked out in a worktree."""
    result = git(cwd, "worktree", "list", "--porcelain")
    mapping: dict[str, str] = {}
    path = ""
    for line in result.stdout.splitlines():
        if line.startswith("worktree "):
            path = line.removeprefix("worktree ")
        elif line.startswith("branch refs/heads/"):
            mapping[line.removeprefix("branch refs/heads/")] = path
    return mapping


def is_ancestor(cwd: Path, branch: str, base_ref: str) -> bool | None:
    if not base_ref:
        return None
    result = git(cwd, "merge-base", "--is-ancestor", branch, base_ref)
    if result.code == 0:
        return True
    if result.code == 1:
        return False
    return None


def merged_status(cwd: Path, branch: str, base_ref: str) -> str:
    merged = is_ancestor(cwd, branch, base_ref)
    if merged is True:
        return f"merged into {base_ref}"
    if merged is False:
        return f"not merged into {base_ref}"
    return "unknown"


def pr_for_branch(prs: list[dict[str, object]], branch: str, lookup_status: str) -> str:
    if lookup_status != "ok":
        return lookup_status
    prs = [pr for pr in prs if pr.get("headRefName") == branch]
    if not prs:
        return "no PR found"
    parts: list[str] = []
    for pr in prs:
        state = pr.get("state", "")
        if pr.get("mergedAt"):
            state = "MERGED"
        draft = " draft" if pr.get("isDraft") else ""
        parts.append(f"#{pr.get('number')} {state}{draft} {pr.get('url')}")
    return "<br>".join(parts)


def same_repository_prs(prs: list[dict[str, object]], branch: str) -> list[dict[str, object]]:
    return [
        pr
        for pr in prs
        if pr.get("headRefName") == branch and pr.get("isCrossRepository") is not True
    ]


def merged_default_prs(
    prs: list[dict[str, object]], branch: str, oid: str, default_name: str
) -> list[dict[str, object]]:
    return [
        pr
        for pr in same_repository_prs(prs, branch)
        if pr.get("mergedAt") and pr.get("headRefOid") == oid and pr.get("baseRefName") == default_name
    ]


def repository_prs(cwd: Path) -> tuple[list[dict[str, object]], str]:
    if shutil.which("gh") is None:
        return [], "gh unavailable"
    result = run(
        [
            "gh",
            "pr",
            "list",
            "--state",
            "all",
            "--json",
            "number,state,mergedAt,isDraft,url,title,baseRefName,headRefName,headRefOid,headRepositoryOwner,isCrossRepository,updatedAt",
            "--limit",
            "1000",
        ],
        cwd,
    )
    if result.code != 0:
        return [], "gh error"
    try:
        prs = json.loads(result.stdout or "[]")
    except json.JSONDecodeError:
        return [], "gh parse error"
    if not isinstance(prs, list):
        return [], "gh parse error"
    return prs, "ok"


def protected_branches(cwd: Path) -> tuple[set[str], str]:
    if shutil.which("gh") is None:
        return set(), "gh unavailable"
    result = run(
        [
            "gh",
            "api",
            "--paginate",
            "repos/{owner}/{repo}/branches?protected=true&per_page=100",
            "--jq",
            ".[].name",
        ],
        cwd,
    )
    if result.code != 0:
        return set(), "gh error"
    return set(result.stdout.splitlines()), "ok"


def repository_visibility(cwd: Path) -> str:
    """Return `private`, `public`, `internal`, or `unknown: <reason>` for the GitHub repository."""
    if shutil.which("gh") is None:
        return "unknown: gh unavailable"
    result = run(["gh", "repo", "view", "--json", "visibility", "--jq", ".visibility"], cwd)
    if result.code != 0:
        return "unknown: gh error"
    visibility = result.stdout.strip().lower()
    if visibility in ("private", "public", "internal"):
        return visibility
    return "unknown: unexpected visibility"


def delete_remote_branches(cwd: Path, candidates: list[dict[str, str]]) -> list[tuple[str, str, str]]:
    """Delete origin branches one by one. Returns (branch, tip, result).

    Rollback handle: `git push origin <tip>:refs/heads/<branch>`; the tip stays reachable from the
    default branch (candidates are merged), so the objects are not lost.
    """
    results: list[tuple[str, str, str]] = []
    for row in candidates:
        result = git(cwd, "push", "origin", "--delete", row["name"])
        outcome = "deleted" if result.code == 0 else f"failed: {result.stderr or result.stdout}"
        results.append((row["name"], row["sha"], outcome))
    return results


def remote_branch_classification(
    cwd: Path,
    row: dict[str, str],
    default_remote: str,
    prs: list[dict[str, object]],
    pr_lookup_status: str,
    protected: set[str],
    protection_status: str,
) -> tuple[str, str]:
    if row["ref"] == default_remote:
        return "keep", "default remote branch"
    if not default_remote:
        return "unknown", "ambiguous default remote branch"
    if pr_lookup_status != "ok" or protection_status != "ok":
        gaps = sorted(
            {
                status
                for status in (pr_lookup_status, protection_status)
                if status != "ok"
            }
        )
        return "unknown", ", ".join(gaps)
    if row["name"] in protected:
        return "keep", "protected branch"

    branch_prs = same_repository_prs(prs, row["name"])
    open_prs = [pr for pr in branch_prs if pr.get("state") == "OPEN" and not pr.get("mergedAt")]
    if open_prs:
        numbers = ", ".join(f"#{pr.get('number')}" for pr in open_prs)
        return "keep", f"open or draft PR {numbers}"

    merged = is_ancestor(cwd, row["ref"], default_remote)
    default_name = default_remote.removeprefix("origin/") if default_remote else ""
    merged_prs = merged_default_prs(prs, row["name"], row["oid"], default_name)
    if merged is True:
        return "safe deletion candidate", f"merged into {default_remote}"
    if merged_prs:
        numbers = ", ".join(f"#{pr.get('number')}" for pr in merged_prs)
        return "safe deletion candidate", f"current tip matches merged PR {numbers}"
    if merged is None:
        return "unknown", "cannot compare with default remote branch"
    return "needs confirmation", "not merged and no open PR"


def fast_forward_branches(
    cwd: Path,
    current: str,
    dirty: bool,
    rows: list[dict[str, str]],
    checked_out: dict[str, str],
) -> list[tuple[str, str, str, str]]:
    """Fast-forward every local tracking branch that is strictly behind its upstream.

    Returns (branch, before, after, result) rows for branches that were behind.
    Rollback handle: the previous tip stays reachable from the new tip; `git reset --hard <before>`
    (current branch) or `git branch -f <branch> <before>` restores it.
    """
    results: list[tuple[str, str, str, str]] = []
    for row in rows:
        name, upstream = row["name"], row["upstream"]
        if not upstream:
            continue
        if git(cwd, "show-ref", "--verify", "--quiet", f"refs/remotes/{upstream}").code != 0:
            continue
        counts = ahead_behind(cwd, name, upstream)
        if counts is None:
            continue
        ahead, behind = counts
        if behind == 0:
            continue
        before = row["sha"]
        if ahead > 0:
            results.append((name, before, before, f"skipped: diverged (ahead {ahead}, behind {behind})"))
            continue
        if name == current:
            if dirty:
                results.append((name, before, before, "skipped: worktree dirty"))
                continue
            result = git(cwd, "pull", "--ff-only")
        elif name in checked_out:
            results.append((name, before, before, f"skipped: checked out at {checked_out[name]}"))
            continue
        else:
            result = git(cwd, "fetch", ".", f"refs/remotes/{upstream}:refs/heads/{name}")
        after = git(cwd, "rev-parse", "--short", name).stdout
        if result.code == 0:
            results.append((name, before, after, f"fast-forwarded from {upstream} (+{behind})"))
        else:
            results.append((name, before, after, f"failed: {result.stderr or result.stdout}"))
    return results


def cleanup_local_branches(
    cwd: Path,
    current: str,
    default_remote: str,
    prs: list[dict[str, object]],
    pr_lookup_status: str,
    remote_classes: dict[str, str],
    checked_out: dict[str, str],
) -> list[tuple[str, str, str, str, str]]:
    """Delete local branches whose tip is already contained in the default remote branch.

    Returns (branch, tip, upstream, reason, result). Rollback handle: `git branch <branch> <tip>`;
    the tip stays reachable from the default branch, so nothing is lost.
    """
    if not default_remote:
        return []
    default_name = default_remote.removeprefix("origin/")
    deleted: list[tuple[str, str, str, str, str]] = []
    for row in local_branches(cwd):
        name = row["name"]
        if name in (current, default_name) or row["upstream"] == default_remote:
            continue
        if name in checked_out:
            continue
        if row["upstream"] and remote_classes.get(row["upstream"]) == "keep":
            continue
        merged = is_ancestor(cwd, name, default_remote)
        if merged is True:
            reason = f"merged into {default_remote}"
        else:
            merged_prs = merged_default_prs(prs, name, row["oid"], default_name) if pr_lookup_status == "ok" else []
            if not merged_prs:
                continue
            reason = "tip matches merged PR " + ", ".join(f"#{pr.get('number')}" for pr in merged_prs)
        result = git(cwd, "branch", "-D", name)
        outcome = "deleted" if result.code == 0 else f"failed: {result.stderr or result.stdout}"
        deleted.append((name, row["sha"], row["upstream"], reason, outcome))
    return deleted


def print_table(headers: list[str], rows: list[list[str]], aligns: list[str] | None = None) -> None:
    aligns = aligns or ["---"] * len(headers)
    print("| " + " | ".join(headers) + " |")
    print("| " + " | ".join(aligns) + " |")
    for row in rows:
        print("| " + " | ".join(quote_cell(value) for value in row) + " |")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repo", nargs="?", default=".", help="Repository path, default: current directory")
    parser.add_argument("--no-fetch", action="store_true", help="Skip git fetch --prune")
    parser.add_argument(
        "--no-fast-forward",
        action="store_true",
        help="Do not fast-forward local tracking branches that are strictly behind upstream",
    )
    parser.add_argument(
        "--no-local-cleanup",
        action="store_true",
        help="Do not delete local branches already merged into the default remote branch",
    )
    parser.add_argument(
        "--no-remote-cleanup",
        action="store_true",
        help="Do not delete safe-deletion-candidate origin branches even when the repository is private",
    )
    parser.add_argument(
        "--no-pr",
        action="store_true",
        help="Skip GitHub PR, protected-branch, and visibility lookups through gh (remote cleanup is then skipped)",
    )
    args = parser.parse_args()

    cwd = Path(args.repo).expanduser().resolve()
    if git(cwd, "rev-parse", "--is-inside-work-tree").code != 0:
        print(f"Not a git repository: {cwd}", file=sys.stderr)
        return 2

    print(f"[git-branch-review] repo={cwd}")
    if not args.no_fetch:
        print("[git-branch-review] fetching remotes with prune")
        fetch = git(cwd, "fetch", "--all", "--prune")
        if fetch.code != 0:
            print(f"[git-branch-review] fetch failed: {fetch.stderr or fetch.stdout}", file=sys.stderr)

    branch = current_branch(cwd)
    upstream = upstream_for(cwd, branch)
    dirty = bool(git(cwd, "status", "--porcelain").stdout)
    default_remote = default_ref(cwd)
    checked_out = worktree_branches(cwd)

    ff_rows: list[tuple[str, str, str, str]] = []
    if not args.no_fast_forward:
        print("[git-branch-review] fast-forwarding tracking branches that are behind")
        ff_rows = fast_forward_branches(cwd, branch, dirty, local_branches(cwd), checked_out)

    counts = ahead_behind(cwd, "HEAD", upstream) if upstream else None
    ahead = counts[0] if counts else "-"
    behind = counts[1] if counts else "-"

    remote_branch_rows = remote_branches(cwd)
    repository_pr_rows: list[dict[str, object]] = []
    pr_lookup_status = "skipped"
    protected: set[str] = set()
    protection_status = "skipped"
    visibility = "skipped"
    if not args.no_pr:
        print("[git-branch-review] querying GitHub PRs")
        repository_pr_rows, pr_lookup_status = repository_prs(cwd)
        print("[git-branch-review] querying protected GitHub branches")
        protected, protection_status = protected_branches(cwd)
        print("[git-branch-review] querying repository visibility")
        visibility = repository_visibility(cwd)

    remote_reviews: list[tuple[dict[str, str], str, str]] = []
    for row in remote_branch_rows:
        classification, reason = remote_branch_classification(
            cwd, row, default_remote, repository_pr_rows, pr_lookup_status, protected, protection_status
        )
        remote_reviews.append((row, classification, reason))
    remote_classes = {row["ref"]: status for row, status, _ in remote_reviews}

    cleanup_rows: list[tuple[str, str, str, str, str]] = []
    if not args.no_local_cleanup:
        print("[git-branch-review] deleting local branches already merged into the default remote branch")
        cleanup_rows = cleanup_local_branches(
            cwd, branch, default_remote, repository_pr_rows, pr_lookup_status, remote_classes, checked_out
        )

    deletion_candidates = [row for row, status, _ in remote_reviews if status == "safe deletion candidate"]
    remote_cleanup_rows: list[tuple[str, str, str]] = []
    remote_cleanup_ran = not args.no_remote_cleanup and visibility == "private" and bool(deletion_candidates)
    if remote_cleanup_ran:
        print("[git-branch-review] repository is private: deleting safe-deletion-candidate origin branches")
        remote_cleanup_rows = delete_remote_branches(cwd, deletion_candidates)

    branch_rows = local_branches(cwd)

    print("\n# Git Branch Review\n")
    print("## Current Branch\n")
    print_table(
        ["field", "value"],
        [
            ["repo", str(cwd)],
            ["branch", branch],
            ["upstream", upstream],
            ["worktree", "dirty" if dirty else "clean"],
            ["ahead", str(ahead)],
            ["behind", str(behind)],
            ["default remote ref", default_remote],
            ["repository visibility", visibility],
        ],
    )

    print("\n## Fast-Forward\n")
    if args.no_fast_forward:
        print("Skipped by `--no-fast-forward`.")
    elif not ff_rows:
        print("No local tracking branch was behind its upstream.")
    else:
        print_table(["branch", "before", "after", "result"], [list(row) for row in ff_rows])
        print("\nRollback: `git reset --hard <before>` for the current branch, `git branch -f <branch> <before>` otherwise.")

    print("\n## Local Cleanup\n")
    if args.no_local_cleanup:
        print("Skipped by `--no-local-cleanup`.")
    elif not cleanup_rows:
        print("No local branch was merged into the default remote branch.")
    else:
        print_table(["branch", "tip", "upstream", "reason", "result"], [list(row) for row in cleanup_rows])
        print("\nRollback: `git branch <branch> <tip>` (the tip stays reachable from the default branch).")

    open_pr_rows = [
        pr for pr in repository_pr_rows if pr.get("state") == "OPEN" and not pr.get("mergedAt")
    ]

    print("\n## Remote Open PRs\n")
    if pr_lookup_status != "ok":
        print(f"GitHub PR lookup: {quote_cell(pr_lookup_status)}")
    elif not open_pr_rows:
        print("No open PRs found.")
    else:
        local_names = {row["name"] for row in branch_rows}
        table_rows: list[list[str]] = []
        for pr in open_pr_rows:
            head = str(pr.get("headRefName") or "")
            state = str(pr.get("state") or "OPEN")
            if pr.get("isDraft"):
                state += " draft"
            number = str(pr.get("number") or "")
            url = str(pr.get("url") or "")
            pr_link = f"[#{number}]({url})" if number and url else number or url
            table_rows.append(
                [
                    pr_link,
                    state,
                    head,
                    "yes" if head in local_names else "no",
                    str(pr.get("baseRefName") or ""),
                    str(pr.get("updatedAt") or ""),
                    str(pr.get("title") or ""),
                ]
            )
        print_table(
            ["PR", "state", "head", "local branch", "base", "updated", "title"],
            table_rows,
            ["---:", "---", "---", "---", "---", "---", "---"],
        )

    print("\n## Remote Branches\n")
    if not remote_reviews:
        print("No origin remote branches found.")
    else:
        local_upstreams: dict[str, list[str]] = {}
        for local in branch_rows:
            if local["upstream"]:
                local_upstreams.setdefault(local["upstream"], []).append(local["name"])
        deleted_remote = {name for name, _, outcome in remote_cleanup_rows if outcome == "deleted"}
        table_rows = []
        for row, classification, reason in remote_reviews:
            protected_status = (
                "unknown" if protection_status != "ok" else "yes" if row["name"] in protected else "no"
            )
            table_rows.append(
                [
                    row["ref"],
                    classification + (" (deleted)" if row["name"] in deleted_remote else ""),
                    reason,
                    protected_status,
                    ", ".join(local_upstreams.get(row["ref"], [])),
                    row["updated"],
                    row["sha"],
                    row["subject"],
                ]
            )
        print_table(
            ["remote branch", "classification", "reason", "protected", "local branches", "updated", "tip", "subject"],
            table_rows,
        )

    print("\n## Remote Cleanup\n")
    if args.no_remote_cleanup:
        print("Skipped by `--no-remote-cleanup`.")
    elif remote_cleanup_ran:
        print_table(["remote branch", "tip", "result"], [list(row) for row in remote_cleanup_rows])
        print("\nRollback: `git push origin <tip>:refs/heads/<branch>` (the tip stays reachable from the default branch).")
    elif not deletion_candidates:
        print("No origin branch qualifies as a safe deletion candidate.")
    else:
        print(f"Not run: repository visibility is `{visibility}` (only `private` repositories are cleaned server-side).")

    print("\n## Recommended Next Actions\n")
    confirmation_needed = [row["name"] for row, status, _ in remote_reviews if status == "needs confirmation"]
    unknown_branches = [row["name"] for row, status, _ in remote_reviews if status == "unknown"]
    if deletion_candidates and not remote_cleanup_ran:
        names = " ".join(row["name"] for row in deletion_candidates)
        print(
            "- Safe deletion candidates left on origin (restore handle = tip SHA in the table): "
            f"`git push origin --delete {names}`"
        )
    elif not deletion_candidates:
        print("- No remote branch currently qualifies as a safe deletion candidate.")
    if confirmation_needed:
        print("- Not merged and no open PR (owner intent unknown): " + ", ".join(confirmation_needed))
    if unknown_branches:
        print("- PR, protection, default-ref, or ancestry information missing: " + ", ".join(unknown_branches))
    if dirty:
        print("- Worktree is dirty; the current branch is not fast-forwarded while it has uncommitted changes.")

    print("\n## Local Branches\n")
    table_rows = []
    for row in branch_rows:
        upstream_name = row["upstream"]
        counts = ahead_behind(cwd, row["name"], upstream_name) if upstream_name else None
        row_ahead = str(counts[0]) if counts else "-"
        row_behind = str(counts[1]) if counts else "-"
        merged = merged_status(cwd, row["name"], default_remote)
        pr = pr_for_branch(repository_pr_rows, row["name"], pr_lookup_status)
        table_rows.append(
            [
                row["name"],
                upstream_name,
                row_ahead,
                row_behind,
                merged,
                pr,
                row["updated"],
                row["sha"],
                row["subject"],
            ]
        )
    print_table(
        ["branch", "upstream", "ahead", "behind", "merged", "PR", "updated", "tip", "subject"],
        table_rows,
        ["---", "---", "---:", "---:", "---", "---", "---", "---", "---"],
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
