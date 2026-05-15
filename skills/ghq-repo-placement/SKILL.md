---
name: ghq-repo-placement
description: "Use when Codex sees a Git repository URL, GitHub/GitLab URL, `git clone` request, repository placement question, or task that requires cloning, pulling, inspecting, or opening an external repository. Prefer ghq-based placement and commands over ad hoc clone paths unless the user explicitly needs a project-local vendor, submodule, fixture, or temporary checkout."
---

# Ghq Repo Placement

Use `ghq` as the default local placement authority for project-independent repositories.
Do not clone external repositories into the current working repo just because that is where the request started.

## Decision Rules

1. If the user provides a Git URL or asks to clone/pull/open an external repo, resolve it through `ghq`.
2. If the repo is meant to be vendored, added as a submodule, used as a test fixture, or checked out under a specific project path, follow that explicit project-local intent instead.
3. If `ghq` is installed, use `ghq root` as the clone root and `ghq get` as the clone/update command.
4. If `ghq` is missing but Homebrew is available, prefer installing `ghq` from the repo's `Brewfile` path or with `brew install ghq` before cloning.
5. If `ghq` cannot be used, fall back to `~/workspace/<host>/<owner>/<repo>` and state that it is a fallback.

## Commands

Inspect placement:

```bash
command -v ghq
ghq root
ghq list -p | rg '<owner>/<repo>$|<repo>$'
```

Clone or update:

```bash
ghq get <repository-url-or-host-path>
ghq get -u <repository-url-or-host-path>
```

Open the resolved repo:

```bash
repo_path="$(ghq list -p | rg '/<owner>/<repo>$' | sed -n '1p')"
cd "$repo_path"
```

For GitHub repositories, `ghq get owner/repo` is acceptable when the host is clearly GitHub.
Use the full URL when the host, protocol, or account is ambiguous.

## Output Contract

When acting on a repo URL, report:

- `repo`: normalized URL or host path
- `placement`: `ghq` or fallback path
- `path`: resolved local checkout path
- `action`: cloned, updated, already present, or blocked
- `reason`: only when not using `ghq`

Keep clone placement stable across turns and machines.
