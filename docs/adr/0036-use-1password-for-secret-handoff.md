---
title: "Use 1Password For Secret Handoff"
date: 2026-05-20
agent: "Codex GPT-5"
status: "accepted"
---

# Context

Secrets had been documented as manual shell exports in `~/.zshenv.local`.
That made local bootstrap simple, but it encouraged plaintext API keys in shell startup files and made CLI handoff conventions inconsistent across tools.

# Decision

Secret values are stored in 1Password.
CLI workflows pass them through 1Password CLI using `op run --env-file`, `op read`, and `op://...` secret references.

The default dotenv path is `~/.config/op/dotfiles.env`.
This file is intentionally unmanaged because even secret references can reveal private vault, item, and field names.
It must contain only secret references, not plaintext secret values.
The default 1Password account selector is `my.1password.com`.

The managed helper `~/.local/bin/oprun` wraps:

```bash
op run --env-file "$OP_DOTFILES_ENV_FILE" -- <command>
```

When `OP_DOTFILES_ENV_FILE` is unset, it defaults to `~/.config/op/dotfiles.env`.

Secret-backed files that must exist on disk are declared in a 1Password Document item named `Secrets Manifest` and restored with the `opmaterialize` script bundled in the `onepassword-secret-materialize` skill.
The manifest is not managed by this repository because it can reveal individual secret item names and local file destinations.
Generated files remain ignored.
The default 1Password vault for this workflow is `Dotfiles Secrets`.
`opmaterialize add <file>` is the standard way to upload a local secret-backed file as a 1Password Document and add or update its manifest row.
Use `--vault <vault>` only when overriding the default.
`opmaterialize diff` checks whether manifest-declared files are missing or changed before restore without printing secret contents.
AI agents use the `onepassword-secret-materialize` skill as the workflow entrypoint. The `~/.local/bin/opmaterialize` command is only a convenience wrapper that delegates to the installed skill script.

# Consequences

- `~/.zshenv.local` remains available for non-secret machine-local overrides only.
- New machines restore the wrapper and example file through chezmoi, then create the local reference file manually.
- Commands that need API keys should be launched with `oprun <command>` or a direct `op run --env-file ... -- <command>`.
- Resolved config files produced by `op inject` must stay outside git and under ignored local paths such as `~/.config/op/injected/`.
- File-based secrets such as VPN configs should be restored with `opmaterialize` into stable `~/.config/...` paths.
- New file-based secrets should be registered with `opmaterialize add` instead of editing the manifest by hand when possible.
- Run `opmaterialize diff` before restore when deciding whether local secret-backed files will change.
- Keep the repo-local `onepassword-secret-materialize` skill aligned with `opmaterialize` behavior when the workflow changes.
