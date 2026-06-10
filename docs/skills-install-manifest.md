---
title: "Skill Install Manifest"
updated_at: 2026-06-23
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
gh skill install . grok-cli-runner --from-local --agent claude-code --scope user
gh skill install . code-evaluator --from-local --agent claude-code --scope user
gh skill install . opus-4-7-tuning --from-local --agent claude-code --scope user
gh skill install . opus-4-8-tuning --from-local --agent claude-code --scope user
gh skill install . gpt-5-5-tuning --from-local --agent claude-code --scope user
gh skill install . codex-cli-runner --from-local --agent claude-code --scope user
gh skill install . gemini-cli-runner --from-local --agent claude-code --scope user
gh skill install . copilot-cli-runner --from-local --agent claude-code --scope user
gh skill install . agent-orchestration-evaluator --from-local --agent claude-code --scope user
gh skill install . ai-usage-coach --from-local --agent claude-code --scope user
gh skill install . soundcore-minutes --from-local --agent claude-code --scope user
gh skill install . ghq-repo-placement --from-local --agent claude-code --scope user
gh skill install . op-cli-runner --from-local --agent claude-code --scope user
gh skill install . onepassword-secret-materialize --from-local --agent claude-code --scope user
gh skill install . handoff --from-local --agent claude-code --scope user
gh skill install . git-branch-review --from-local --agent claude-code --scope user
gh skill install . dads-design --from-local --agent claude-code --scope user
gh skill install . gws-cli-runner --from-local --agent claude-code --scope user
gh skill install . freee-mcp-runner --from-local --agent claude-code --scope user
```

### Codex

```bash
gh skill install . skill-manager --from-local --agent codex --scope user
gh skill install . docs-entrypoint-check --from-local --agent codex --scope user
gh skill install . docs-evaluator --from-local --agent codex --scope user
gh skill install . grok-cli-runner --from-local --agent codex --scope user
gh skill install . code-evaluator --from-local --agent codex --scope user
gh skill install . opus-4-7-tuning --from-local --agent codex --scope user
gh skill install . opus-4-8-tuning --from-local --agent codex --scope user
gh skill install . gpt-5-5-tuning --from-local --agent codex --scope user
gh skill install . claude-cli-runner --from-local --agent codex --scope user
gh skill install . gemini-cli-runner --from-local --agent codex --scope user
gh skill install . copilot-cli-runner --from-local --agent codex --scope user
gh skill install . ai-usage-coach --from-local --agent codex --scope user
gh skill install . soundcore-minutes --from-local --agent codex --scope user
gh skill install . ghq-repo-placement --from-local --agent codex --scope user
gh skill install . op-cli-runner --from-local --agent codex --scope user
gh skill install . onepassword-secret-materialize --from-local --agent codex --scope user
gh skill install . handoff --from-local --agent codex --scope user
gh skill install . git-branch-review --from-local --agent codex --scope user
gh skill install . dads-design --from-local --agent codex --scope user
gh skill install . gws-cli-runner --from-local --agent codex --scope user
gh skill install . freee-mcp-runner --from-local --agent codex --scope user
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

- upstream: [mizchi/skills `empirical-prompt-tuning`](https://github.com/mizchi/skills/tree/main/empirical-prompt-tuning)
- status: installed globally for Claude Code and Codex
- install mode: direct `gh skill install` from upstream GitHub repository
- reason: upstream is now publisher-discoverable on GitHub, so direct external install is the standard path
- update note: refresh by reinstalling from `mizchi/skills` with `--force`

#### Claude Code / Codex refresh

repo root で実行する。

```bash
gh skill install mizchi/skills empirical-prompt-tuning --agent claude-code --scope user --force
gh skill install mizchi/skills empirical-prompt-tuning --agent codex --scope user --force
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
