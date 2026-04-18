# リポジトリ管理ルール

- このリポジトリ（dotfiles）の管理責任は Codex が持つ
- `dot_*` 配下のファイルは chezmoi により環境へ配置される成果物として扱う
- `dot_*` 配下の変更時は必ず `dotfile-update` スキルを使用すること
- dotfile 変更前に [chezmoi-knowledge/SKILL.md](/Users/rmanzoku/.local/share/chezmoi/.claude/skills/chezmoi-knowledge/SKILL.md) と [semantics.md](/Users/rmanzoku/.local/share/chezmoi/.claude/skills/chezmoi-knowledge/references/semantics.md) を確認し、source / target / ignore の前提を外さないこと
- `chezmoi apply` の前とドリフト確認時は `scripts/chezmoi-drift --check-ignore` 相当の `.chezmoiignore` 整合確認を行い、意図せず無効化された source がないことを確認すること
- 手動編集は `~/.zshenv.local` 等の chezmoi 管理外ファイルに限る

# 恒久指示の反映運用

- 恒久性のあるユーザー指示、再発しやすい運用判断、複数回参照しそうな手順は、原則その作業ターン内で git 管理ファイルへ反映すること
- 反映先は、運用ルールや判断基準なら `AGENTS.md` と AI 別指示ファイル、背景や継続判断なら `docs/adr/`、反復手順や更新フローなら対応 Skill を使い分けること
- 反映不要とする例外は、一過性の事情、既存文書に重複する内容、ユーザーが今回は文書化不要と明示した場合に限ること
- 例外を適用した場合は、反映しなかった理由を作業結果に残すこと
- AI 間や CLI 間で複数行や構造化された内容を受け渡すときは、作業 worktree 内の `.context/` に置いた実ファイル経由を標準とし、`-p` などの引数へのインライン展開や here-doc 直書きは原則避けること
- パイプでの受け渡しは、単一のコマンドが標準入力をただちに 1 回だけ読む単発処理に限って許容し、再読・再送・サブプロセス引き継ぎ・別 Agent への移譲が絡む場合は実ファイル経由を優先すること

# Phase / Step Artifact ルール

- Phase / Step を持つ作業では、各 Phase / Step の完了前に `.context/` 配下へ中間成果物 artifact を保存すること
- 次の Phase / Step へ進む条件は、対応する artifact の生成とすること
- 口頭合意、推論上の完了宣言、Memory 内だけの状態遷移で Phase / Step を進めてはならない
- artifact の初期必須項目は `task`、`phase_or_step`、`created_at` とし、Markdown は Front Matter、JSON は同名キーで保持すること
- artifact の推奨命名は `.context/<task-or-date>/<nn>-<phase-name>.(md|json)` とし、同名更新時は最新更新時刻のファイルのみを有効扱いにすること
- 非 Phase 作業は artifact 必須対象外とする。ただし単発例外として artifact gate を明示的にバイパスする場合だけ `.context/single-step/<task>.json` を使い、`enabled=true`、`task`、`reason`、`expires_at` を必須とすること
- Phase / Step 遷移の最小原則は `AGENTS.md` を正本とし、各 Skill 固有の required artifact は `SKILL.md` を正本とすること
- `AGENTS.md` と `SKILL.md` が競合する場合は `SKILL.md` をその Skill 実行中の具体契約として優先し、`AGENTS.md` は下限ルールとして常に適用すること

# スキル管理

- 本リポジトリではリポジトリ専用の Claude Code 用スキル（`.claude/skills/`）も管理対象に含む
- `.claude/skills/` 配下のファイルは repo ローカル用途とし、chezmoi でグローバル配備しない
- 各 AI ツール間のスキル同期は skill-manager スキルの責務であり、本リポジトリでは扱わない
- `dotfile-update` は chezmoi 管理の dotfile 更新専用とし、repo ローカル skill の編集責務を持たせない
- `.claude/skills/` 配下の Skill を追加・更新・構成変更する場合は、既存 Skill の更新であっても `skill-creator` スキルの手順に従うこと
- Skill 更新時は `SKILL.md` だけでなく、必要に応じて `scripts/`、`references/`、`assets/`、`agents/openai.yaml` の整合も確認すること
- Skill 更新後は `skill-creator` が提供する `quick_validate.py` を実行して基本妥当性を確認すること
