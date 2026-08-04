---
title: "Skill Install Manifest"
updated_at: 2026-07-26
---

# Skill Install Manifest

新しいマシンで配布 skill を復元するときは、この一覧を正本として `gh skill install` を実行する。

当面は script を作らず、docs-only の install manifest として維持する。
将来 `gh` 側に manifest 機能が入ったら、そちらへ移行を検討する。

この manifest で管理する repo オリジナル skill と external skill は、Claude Code と Codex に同じ skill セット・同じ ref / version で配備する。
Codex `.system` skill、Claude / Codex の plugin 同梱 skill、各 host の組み込み skill は parity 対象外とする。

## First-party publisher skills

repo root を install source にして実行する。

`claude-cli-runner` は Codex 専用として Codex にのみ install する(Claude 内の claude_code 解決は Self-Elision で subagent を使うため。ADR-0058 parity の明示的例外)。

### Claude Code

```bash
gh skill install . skill-manager --from-local --agent claude-code --scope user
gh skill install . docs-entrypoint-check --from-local --agent claude-code --scope user
gh skill install . docs-evaluator --from-local --agent claude-code --scope user
gh skill install . grok-cli-runner --from-local --agent claude-code --scope user
gh skill install . code-evaluator --from-local --agent claude-code --scope user
gh skill install . opus-5-tuning --from-local --agent claude-code --scope user
gh skill install . fable-5-tuning --from-local --agent claude-code --scope user
gh skill install . gpt-5-6-tuning --from-local --agent claude-code --scope user
gh skill install . codex-cli-runner --from-local --agent claude-code --scope user
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
```

### Codex

```bash
gh skill install . skill-manager --from-local --agent codex --scope user
gh skill install . docs-entrypoint-check --from-local --agent codex --scope user
gh skill install . docs-evaluator --from-local --agent codex --scope user
gh skill install . grok-cli-runner --from-local --agent codex --scope user
gh skill install . code-evaluator --from-local --agent codex --scope user
gh skill install . opus-5-tuning --from-local --agent codex --scope user
gh skill install . fable-5-tuning --from-local --agent codex --scope user
gh skill install . gpt-5-6-tuning --from-local --agent codex --scope user
gh skill install . claude-cli-runner --from-local --agent codex --scope user
gh skill install . codex-cli-runner --from-local --agent codex --scope user
gh skill install . copilot-cli-runner --from-local --agent codex --scope user
gh skill install . agent-orchestration-evaluator --from-local --agent codex --scope user
gh skill install . ai-usage-coach --from-local --agent codex --scope user
gh skill install . soundcore-minutes --from-local --agent codex --scope user
gh skill install . ghq-repo-placement --from-local --agent codex --scope user
gh skill install . op-cli-runner --from-local --agent codex --scope user
gh skill install . onepassword-secret-materialize --from-local --agent codex --scope user
gh skill install . handoff --from-local --agent codex --scope user
gh skill install . git-branch-review --from-local --agent codex --scope user
gh skill install . dads-design --from-local --agent codex --scope user
gh skill install . gws-cli-runner --from-local --agent codex --scope user
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

### `freee-api-skill`

- upstream: [freee/freee-mcp `skills/freee-api-skill`](https://github.com/freee/freee-mcp/tree/main/skills/freee-api-skill)
- release: [v0.30.2](https://github.com/freee/freee-mcp/releases/tag/v0.30.2)
- status: installed globally for Claude Code and Codex
- install mode: direct `gh skill install` from the official upstream GitHub repository
- pin: `v0.30.2`
- reason: official freee distribution provides the API reference skill; keep it external and do not vendor it into this repo
- update note: inspect changes with `gh skill preview freee/freee-mcp freee-api-skill` and keep the skill pin aligned with the intended `freee-mcp` release

#### Claude Code / Codex refresh

repo root で実行する。

```bash
gh skill install freee/freee-mcp freee-api-skill --pin v0.30.2 --agent claude-code --scope user --force
gh skill install freee/freee-mcp freee-api-skill --pin v0.30.2 --agent codex --scope user --force
```
