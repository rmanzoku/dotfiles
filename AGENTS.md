# リポジトリ管理ルール

- このリポジトリ（dotfiles）の管理責任は Codex が持つ
- `dot_*` 配下のファイルは chezmoi により環境へ配置される成果物として扱う
- `dot_*` 配下の変更時は必ず `dotfile-update` スキルを使用すること
- dotfile 変更前に [chezmoi-knowledge/SKILL.md](.claude/skills/chezmoi-knowledge/SKILL.md) と [semantics.md](.claude/skills/chezmoi-knowledge/references/semantics.md) を確認し、source / target / ignore の前提を外さないこと
- `chezmoi apply` の前とドリフト確認時は `scripts/chezmoi-drift --check-ignore` 相当の `.chezmoiignore` 整合確認を行い、意図せず無効化された source がないことを確認すること
- secret 実値は 1Password に保存し、CLI では `op run --env-file` / `op read` と `op://...` secret reference 経由で受け渡すこと
- `~/.config/op/dotfiles.env` は管理外の secret reference 置き場とし、実値を書かないこと
- `~/.zshenv.local` は secret の置き場ではなく、マシン固有の非 secret local override に限定すること
- ファイル探索は `rg --files`、内容検索は `rg` を第一候補とし、`rg` が使えない場合だけ `ag`、最後に `grep` を使うこと

# 作業姿勢

- 実装前に、仮定・不明点・複数解釈・重要なトレードオフを明示し、仕様・契約・データ形式などの永続判断は既存実装・テスト・文書・ユーザー確認に基づかない限り作らず、不足時は仮実装・仮差分・コード例を提示せず確認事項と検証計画に留めること
- 要求を満たす最小の実装を優先し、依頼されていない機能・抽象化・設定項目・将来対応を追加しないこと
- 既存コードや文書を編集するときは、ユーザー依頼に直接必要な行だけを変更し、隣接する無関係なリファクタ・整形・削除を行わないこと
- 作業の成功条件を検証可能な形で定め、バグ修正や機能追加では再現・テスト・差分確認などの具体的な確認手段まで含めて完了判断すること
- 再現テストを書くときは、観測済みの失敗と既存契約だけを固定し、未確認の戻り値・エラー型・出力形式を新しい期待値として作らないこと

# Desktop 自動実行設定管理

- Codex / Claude Desktop などの自動実行定義は、再現可能な宣言的設定だけを chezmoi 配下で管理すること
- Codex Desktop の automation は `dot_codex/automations/<automation-id>/automation.toml.tmpl` を正本とすること
- 自動実行の `memory.md`、lock、jitter salt、highwatermark、実行ログ、セッション履歴、UUID ごとの task 実行状態は machine-local state として `.chezmoiignore` で管理対象外にすること
- Claude Desktop / Claude Code の `~/.claude/tasks` は、安定した宣言的 schedule ではなく実行 state として扱い、明示的に管理対象へ昇格する根拠が確認できるまで chezmoi で管理しないこと
- 新しい Desktop 自動実行設定を追加するときは、source / target の対応を確認し、secret・token・認証情報が含まれないことを点検してから git 管理へ追加すること

# 恒久指示の反映運用

- 恒久性のあるユーザー指示、再発しやすい運用判断、複数回参照しそうな手順は、原則その作業ターン内で git 管理ファイルへ反映すること
- 反映先は、運用ルールや判断基準なら `AGENTS.md` と AI 別指示ファイル、背景や継続判断なら `docs/adr/`、反復手順や更新フローなら対応 Skill を使い分けること
- 反映不要とする例外は、一過性の事情、既存文書に重複する内容、ユーザーが今回は文書化不要と明示した場合に限ること
- 例外を適用した場合は、反映しなかった理由を作業結果に残すこと
- AI 間や CLI 間で複数行や構造化された内容を受け渡すときは、作業 worktree 内の `.context/` に置いた実ファイル経由を標準とし、`-p` などの引数へのインライン展開や here-doc 直書きは原則避けること
- パイプでの受け渡しは、単一のコマンドが標準入力をただちに 1 回だけ読む単発処理に限って許容し、再読・再送・サブプロセス引き継ぎ・別 Agent への移譲が絡む場合は実ファイル経由を優先すること
- 長めの処理を実行するためにスクリプトを生成する場合、特にループで外部通信を伴う処理では、処理開始、各反復または定期間隔、リトライ、完了、失敗を標準出力へログ出力し、AI や利用者が停止と進行を判別できるようにすること
- 長時間スクリプトの進捗ログには、対象件数、現在位置、処理対象 ID や URL の要約、経過時間、次の待機やリトライ予定など、秘密情報を含めずに再実行判断へ必要な情報を含めること
- 長時間スクリプトのログは artifact gate と同じく観測可能性のための運用契約として扱い、静かな成功を前提にせず、hang や外部 API 待ちで無出力に見える実装を避けること
- AI が作る script / skill では、特に外部接続を伴う処理について、主経路の失敗原因を隠す暗黙 fallback を追加しないこと。代替経路が必要な場合は、目的、発動条件、観測ログ、冪等性、再実行時の挙動、検証欠落、恒久対策レビューの要否を明示し、安定した代替経路は fallback ではなく主経路へ昇格すること。同じデータに対する複数 RPC / mirror / replica のように同等性と選択条件が明示された冗長 provider は、この禁止の例外として扱うこと
- 汎用 CLI / tool error は、失敗扱いする前に意味で分類すること。`rg` の exit code 1 は原則「検索一致なし」として検索仮説・検索範囲・次に広げる範囲を見直し、`apply_patch` の context mismatch は対象範囲を再読してから最小差分を作り直し、`sed` / `rg` の missing path は `rg --files` 等で実在 path を確認し、`git` の conflict / dirty state はユーザー変更保護を優先し、format / typecheck / test failure は対象 file・error shape・再実行 command を固定してから続行すること
- コマンド、ツール、環境、権限、依存関係、検証でエラーが出た場合は、一時的な迂回で作業継続してよいが、同種エラーの再発、検証省略、環境・設定・権限・依存関係の不備、再現性低下、次回も必要になりそうな手順がある場合は恒久対策レビューの対象として扱うこと
- 恒久対策レビューでは、エラー原因、一時迂回、恒久対策候補、git 管理へ反映すべき設定・文書・hook・Skill、machine-local に留める state、検証方法を分けて整理すること
- サブエージェントや runner を使える環境では、恒久対策レビューを必要に応じて別 agent / reviewer / evaluator に委譲してよいが、親 Agent は提案をそのまま採用せず、既存実装・設定・文書・テストへ戻って妥当性を確認すること
- 複数モデルの使い分け自体を目的にせず、調査、レビュー、設計評価、事業判断、秘書的整理など明確な役割へ切り出せる作業では、必要に応じて role-appropriate なサブエージェント、custom agent、または runner を積極的に使うこと
- サブエージェントや custom agent へ委譲するときは、親 Agent が目的、背景、対象範囲、制約、許可する副作用、期待成果物、検証方法を明示し、最終判断・統合・ユーザーへの報告責任を保持すること

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
- 配布する repo オリジナル skill は publisher layout の `skills/` 配下を正本として git 管理すること
- publisher layout の skill は `gh skill install --from-local <repo-root> <skill> --agent <agent> --scope user` を標準配備経路とし、chezmoi で `~/.claude/skills/` や `~/.codex/skills/` へ直接配備しないこと
- 新しいマシン向けの復元情報は当面 script 化せず、`docs/skills-install-manifest.md` の docs-only manifest を正本として保存すること
- external skill はこの repo に vendoring せず、`gh skill` による install / update / remove を標準運用とすること
- third-party external skill が upstream publisher layout を持たない場合は、`docs/skills-install-manifest.md` に `fetch + gh skill install --from-local` 手順を残して管理すること
- Codex `.system/skill-installer` は Codex-only の補助入口として認識し、恒久的な外部 skill 管理は `gh skill` と `docs/skills-install-manifest.md` を正本にすること
- 各 AI ツール間のスキル同期は skill-manager スキルの責務であり、本リポジトリでは扱わない
- `dotfile-update` は chezmoi 管理の dotfile 更新専用とし、repo ローカル skill の編集責務を持たせない
- `.claude/skills/` 配下の repo ローカル skill と `skills/` 配下の publisher skill を追加・更新・構成変更する場合は、既存 Skill の更新であっても `skill-creator` スキルの手順に従うこと
- Skill 更新時は `SKILL.md` だけでなく、必要に応じて `scripts/`、`references/`、`assets/`、`agents/openai.yaml` の整合も確認すること
- Skill 更新後は repo ローカルの `scripts/skill-quick-validate <skill-dir>` を実行して基本妥当性を確認すること
