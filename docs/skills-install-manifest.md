---
title: "Skill Install Manifest"
updated_at: 2026-04-26
---

# Skill Install Manifest

新しいマシンで配布 skill を復元するときは、この一覧を正本として `gh skill install` を実行する。

当面は script を作らず、docs-only の install manifest として維持する。
将来 `gh` 側に manifest 機能が入ったら、そちらへ移行を検討する。

## First-party publisher skills

repo root を install source にして実行する。

### Claude Code

```bash
gh skill install . skill-manager --from-local --agent claude-code --scope user
gh skill install . docs-entrypoint-check --from-local --agent claude-code --scope user
gh skill install . docs-evaluator --from-local --agent claude-code --scope user
gh skill install . grok --from-local --agent claude-code --scope user
gh skill install . code-evaluator --from-local --agent claude-code --scope user
gh skill install . opus-4-7-tuning --from-local --agent claude-code --scope user
```

### Codex

```bash
gh skill install . skill-manager --from-local --agent codex --scope user
gh skill install . docs-entrypoint-check --from-local --agent codex --scope user
gh skill install . docs-evaluator --from-local --agent codex --scope user
gh skill install . grok --from-local --agent codex --scope user
gh skill install . code-evaluator --from-local --agent codex --scope user
gh skill install . opus-4-7-tuning --from-local --agent codex --scope user
```

## Third-party external skills

third-party external skill はここへ追加で列挙する。

### `gws-*`

- upstream: [googleworkspace/cli `skills/`](https://github.com/googleworkspace/cli/tree/main/skills)
- status: installed globally for Claude Code and Codex
- install mode: direct `gh skill install` from upstream GitHub repository
- pin: `v0.22.5`
- reason: upstream provides official per-service gws skills; keep them external and do not vendor them into this repo
- scope: install only `gws-shared`, `gws-drive`, and `gws-drive-upload`
- prerequisite: `googleworkspace-cli` must be installed, currently managed by `Brewfile`
- update note: keep the skill pin aligned with the installed `googleworkspace-cli` version

#### Claude Code / Codex refresh

repo root で実行する。

```bash
skills=(
  gws-drive
  gws-drive-upload
  gws-shared
)

for agent in claude-code codex; do
  for skill in "${skills[@]}"; do
    gh skill install googleworkspace/cli "$skill" --pin v0.22.5 --agent "$agent" --scope user --force
  done
done
```

### `empirical-prompt-tuning`

- upstream: [mizchi/chezmoi-dotfiles `dot_claude/skills/empirical-prompt-tuning/SKILL.md`](https://github.com/mizchi/chezmoi-dotfiles/blob/main/dot_claude%2Fskills%2Fempirical-prompt-tuning%2FSKILL.md)
- status: installed globally for Claude Code and Codex
- install mode: fetch upstream `SKILL.md`, stage it locally, then install with `gh skill --from-local`
- reason: upstream repo is not a publisher-layout repo, so direct `gh skill install OWNER/REPO skill` is unavailable
- update note: `gh skill update --dry-run empirical-prompt-tuning` currently reports missing GitHub metadata, so refresh by re-fetching and reinstalling

#### Claude Code / Codex refresh

repo root で実行する。

```bash
mkdir -p .context/skill-bootstrap/empirical-prompt-tuning/skills/empirical-prompt-tuning
curl -L --fail --silent --show-error \
  'https://raw.githubusercontent.com/mizchi/chezmoi-dotfiles/main/dot_claude/skills/empirical-prompt-tuning/SKILL.md' \
  -o .context/skill-bootstrap/empirical-prompt-tuning/skills/empirical-prompt-tuning/SKILL.md
gh skill install ./.context/skill-bootstrap/empirical-prompt-tuning empirical-prompt-tuning --from-local --agent claude-code --scope user --force
gh skill install ./.context/skill-bootstrap/empirical-prompt-tuning empirical-prompt-tuning --from-local --agent codex --scope user --force
```

### `grill-me`

- upstream: [mattpocock/skills `grill-me`](https://github.com/mattpocock/skills/tree/main/grill-me)
- status: installed globally for Claude Code and Codex
- install mode: direct `gh skill install` from upstream GitHub repository
- reason: upstream is publisher-discoverable on GitHub, so direct external install is the standard path
- update note: inspect changes with `gh skill preview mattpocock/skills grill-me` before running `gh skill update grill-me`

#### Claude Code / Codex install

repo root で実行する。

```bash
gh skill install mattpocock/skills grill-me --agent claude-code --scope user
gh skill install mattpocock/skills grill-me --agent codex --scope user
```
