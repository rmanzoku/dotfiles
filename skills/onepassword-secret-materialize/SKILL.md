---
name: onepassword-secret-materialize
description: Manage this dotfiles repository's 1Password-backed secret file workflow. Use when the user asks to save, register, restore, diff, check, or materialize secret-backed files such as VPN configs, env files, API-key dotenv files, or other local config files through 1Password, especially with `opmaterialize`, `Secrets Manifest`, `Dotfiles Secrets`, `OP_ACCOUNT`, or paths under `~/.config`.
---

# Onepassword Secret Materialize

Use this skill for file-based secrets that should be reproducible on other machines without storing secret values or individual secret item names in git.

The repository owns the generic tool and policy. 1Password owns the sensitive manifest and file contents.

## Default Model

- Account selector: `my.1password.com`
- Vault: `Dotfiles Secrets`
- Manifest item: `Secrets Manifest`
- Managed restore tool source: `scripts/opmaterialize` inside this skill
- Optional deployed wrapper after `chezmoi apply`: `~/.local/bin/opmaterialize`
- Generated local files remain ignored by `.chezmoiignore`

Do not print secret file contents. Do not add materialized files, manifest rows, VPN configs, API keys, tokens, private keys, or real `op://...` references to git.

## Choose The Operation

### Save Or Register A Local Secret-Backed File

Use this when the user says a file is ready and should be saved for other PCs.

1. Confirm the file exists without printing its contents:

   ```bash
   test -r <path>
   ```

2. Register it with 1Password and update `Secrets Manifest`:

   ```bash
   opmaterialize add <path>
   ```

   If the deployed command is not available in the current shell, run the bundled script:

   ```bash
   OP_ACCOUNT=my.1password.com \
   OP_DOTFILES_MATERIALIZE_VAULT="Dotfiles Secrets" \
   sh ~/.codex/skills/onepassword-secret-materialize/scripts/opmaterialize add <path>
   ```

3. Report only the created/updated item name and manifest status from command output. Do not show file contents.

Use `--item`, `--out-path`, `--mode`, or `--vault` only when the user asks for an override or the default path/name would be wrong.

### Check Restore Impact

Run this before restore when the user wants to know what would change, or when restore might overwrite existing local files.

```bash
opmaterialize diff
```

Interpretation:

- `missing`: a manifest-declared file is absent locally
- `changed`: local file differs from the 1Password Document
- `unchanged`: local file already matches
- exit `1`: at least one file is missing or changed
- exit `0`: no differences

The diff command must not print secret contents or write target files.

### Restore Secret-Backed Files

Use this when setting up a new machine or rehydrating ignored local config files.

1. Check first unless the user explicitly asks to restore immediately:

   ```bash
   opmaterialize diff
   ```

2. Restore:

   ```bash
   opmaterialize restore
   ```

3. If restore stops because a target differs, do not force overwrite silently. Explain the path and ask whether to use:

   ```bash
   opmaterialize restore --force
   ```

## Troubleshooting

- If `op` reports multiple accounts, use `OP_ACCOUNT=my.1password.com`.
- If `op` requires authentication, let the user unlock/sign in to 1Password; do not ask them to paste secrets into chat.
- If `Dotfiles Secrets` or `Secrets Manifest` is missing, create or ask the user to create it in 1Password rather than storing its content in git.
- If a requested generated path is not ignored, update `.chezmoiignore` before registering the file.
- If changing the managed script, README, ADR, `.chezmoiignore`, or deployed dotfiles, follow the repository `dotfile-update` workflow.
- If changing this skill, follow `skill-creator` and run `scripts/skill-quick-validate`.

## Validation For Script Or Policy Changes

After editing the workflow implementation or docs, run:

```bash
shellcheck skills/onepassword-secret-materialize/scripts/opmaterialize dot_local/bin/executable_opmaterialize dot_local/bin/executable_oprun
git diff --check -- . ':(exclude).context'
scripts/chezmoi-drift --check-ignore
scripts/skill-quick-validate .claude/skills/onepassword-secret-materialize
```

For behavior changes, use a fake `op` in `.context/` to test `diff`, `restore`, and `add` without touching live 1Password.
