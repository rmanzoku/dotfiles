# リポジトリ管理ルール

- このリポジトリ（dotfiles）は Codex と Claude Code のどちらが編集してもよく、特定の AI を編集担当に限定しない
- このリポジトリは元の利用者の環境を主対象としつつ、他者の初期設定や AI 運用ポリシー参照にも使われるため、個人・会社・案件・マシンに依存する値は git 管理の汎用層へ固定せず、環境変数、ignored private file、1Password-backed restore、または各作業リポジトリの責務へ分離すること
- `tech`、`biz`、`personal` などの role agent は元利用者の判断スタイルや実務文脈を一部模倣する private agent として存在し得るが、利用不能時に AI が元利用者の private context を推測・模倣して補完してはならない
- 他者が流用できる設定を追加・変更するときは、[docs/adopting-this-dotfiles.md](docs/adopting-this-dotfiles.md) のレイヤー分離に従い、owner 固有の既定値・secret-backed state・account profile 対応を差し替え可能にすること
- `dot_*` 配下のファイルは chezmoi により環境へ配置される成果物として扱う
- `dot_*` 配下の変更時は必ず `dotfile-update` スキルを使用すること
- グローバル AI 指示ファイルの共通ルールは `.chezmoitemplates/common-rules.md` を単一の正本とし、AI 別 `.tmpl`（`dot_codex/AGENTS.md.tmpl` など）には include と AI 固有セクションだけを置き、共通ルール文面を複製しないこと
- dotfile 変更前に [chezmoi-knowledge/SKILL.md](.claude/skills/chezmoi-knowledge/SKILL.md) と [semantics.md](.claude/skills/chezmoi-knowledge/references/semantics.md) を確認し、source / target / ignore の前提を外さないこと
- `chezmoi apply` の前とドリフト確認時は `scripts/chezmoi-drift --check-ignore` 相当の `.chezmoiignore` 整合確認を行い、意図せず無効化された source がないことを確認すること
- secret 実値は 1Password に保存し、CLI では `op run --env-file` / `op read` と `op://...` secret reference 経由で受け渡すこと。`~/.config/op/dotfiles.env` は secret reference 置き場として実値を書かず、`~/.zshenv.local` はマシン固有の非 secret local override に限定すること

# Desktop 自動実行設定管理

- Codex / Claude Desktop などの自動実行定義は、再現可能な宣言的設定だけを chezmoi 配下で管理すること
- Codex Desktop の automation は `dot_codex/automations/<automation-id>/automation.toml.tmpl` を正本とすること
- 自動実行の `memory.md`、lock、jitter salt、highwatermark、実行ログ、セッション履歴、UUID ごとの task 実行状態は machine-local state として `.chezmoiignore` で管理対象外にすること
- Claude Desktop / Claude Code の `~/.claude/tasks` は、安定した宣言的 schedule ではなく実行 state として扱い、明示的に管理対象へ昇格する根拠が確認できるまで chezmoi で管理しないこと
- 新しい Desktop 自動実行設定を追加するときは、source / target の対応を確認し、secret・token・認証情報が含まれないことを点検してから git 管理へ追加すること
- アプリが実行時に target へ注入する app 管理設定（例: Codex Desktop が `~/.codex/config.toml` へ書き込む `mcp_servers.node_repl` 等）は machine-local runtime state として source へ取り込まず、pre-commit hook の `APP_MANAGED_DRIFT_ALLOWLIST` で警告のみとすること（[docs/adr/0051](docs/adr/0051-warn-only-app-managed-chezmoi-drift.md)）

# Artifact

- artifact の初期必須項目（`task`、`phase_or_step`、`created_at`）は、Markdown では Front Matter、JSON では同名キーに書く

# スキル管理

- 本リポジトリではリポジトリ専用の Claude Code 用スキル（`.claude/skills/`）も管理対象に含む
- 新しい Skill / Runner / wrapper は、単なる便利化ではなく、再発する失敗パターン、secret / OAuth / account 境界、長時間実行の観測性、副作用リスクを扱う場合に限って追加すること
- 追加前に、運用ルール、既存 wrapper の最終ガード、既存 runner の adapter / option で足りるか確認し、足りない理由を [docs/runner-skill-governance.md](docs/runner-skill-governance.md)、該当 Skill、または ADR に残すこと
- グローバル配備される AI 指示ファイル（例: `dot_codex/AGENTS.md.tmpl`）は薄く保ち、tool 固有・repo 固有の詳細な runner / Skill 作成判断は、この repo の `AGENTS.md`、`docs/`、または該当 Skill に置くこと
- `.claude/skills/` 配下のファイルは repo ローカル用途とし、chezmoi でグローバル配備しない
- 配布する repo オリジナル skill は publisher layout の `skills/` 配下を正本として git 管理すること
- publisher layout の skill は `gh skill install <repo-root> <skill> --from-local --agent <agent> --scope user` を標準配備経路とし、chezmoi で `~/.claude/skills/` や `~/.codex/skills/` へ直接配備しないこと
- 新しいマシン向けの復元情報は当面 script 化せず、`docs/skills-install-manifest.md` の docs-only manifest を正本として保存すること
- external skill はこの repo に vendoring せず、`gh skill` による install / update / remove を標準運用とすること
- third-party external skill が upstream publisher layout を持たない場合は、`docs/skills-install-manifest.md` に `fetch + gh skill install --from-local` 手順を残して管理すること
- Codex `.system/skill-installer` は Codex-only の補助入口として認識し、恒久的な外部 skill 管理は `gh skill` と `docs/skills-install-manifest.md` を正本にすること
- `docs/skills-install-manifest.md` で管理する repo オリジナル skill と external skill は、Claude Code と Codex に同じ skill セット・同じ ref / version で配備すること。追加・更新・削除は両者を同じターンで変更すること
- Codex `.system` skill、Claude / Codex の plugin 同梱 skill、各 host が提供する組み込み skill は parity 対象外とする。例外的に manifest 管理 skill を片方だけへ配備する場合は、理由と期限を manifest または ADR に明記すること
- Claude Code / Codex 間のスキル同期と parity 検証は skill-manager スキルの責務とする
- `dotfile-update` は chezmoi 管理の dotfile 更新専用とし、repo ローカル skill の編集責務を持たせない
- `.claude/skills/` 配下の repo ローカル skill と `skills/` 配下の publisher skill を追加・更新・構成変更する場合は、既存 Skill の更新であっても `skill-creator` スキルの手順に従うこと
- Skill 更新時は `SKILL.md` だけでなく、必要に応じて `scripts/`、`references/`、`assets/`、`agents/openai.yaml` の整合も確認すること
- Skill 更新後は repo ローカルの `scripts/skill-quick-validate <skill-dir>` を実行して基本妥当性を確認すること
