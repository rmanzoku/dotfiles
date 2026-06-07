@~/.codex/AGENTS.md

# Claude Code 固有ルール

- このファイルは `~/.codex/AGENTS.md` を共通ルールとして import する
- import した `~/.codex/AGENTS.md` 内の `# Codex 固有ルール` 以降は Codex 専用として扱い、Claude Code の行動指示としては適用しないこと
- Claude Code の hook は `artifact gate` の補助 enforcement として使い、自然言語の意味理解や「本当に完了したか」の判定は持たせないこと
- artifact gate の validator は `.context/` の artifact 存在、初期必須キー、単発例外宣言ファイルの妥当性だけを検査すること
- コミット前に、auto memory（~/.claude/projects/*/memory/）に保存された内容のうち、恒久的な運用ルール・判断基準・再利用する手順としてプロジェクトに有用なものがあれば、プロジェクトの CLAUDE.md に反映するか確認すること
- auto memory の反映対象は、今後の Agent の行動を変える具体的なルール・判断基準・手順に限り、既存ルールの再掲、単なる repo メタ情報、会話履歴の要約は反映不要とすること
- グローバル指示ファイルが別の管理元から配備されている場合、target の実ファイルを直接編集せず、対応する管理元ファイルへ反映すること
- テキスト変換は単発・バッチ処理を優先し、同一ファイルに対して `sed` などの逐次実行を繰り返さないこと
- `sed` を使う場合は `-e` で式をまとめるか script file を使い、複数変更を 1 回の実行に集約すること
- 複雑なパターンは `perl`、JSON / TS / AST などの構造化データは専用 parser / tool を使うこと
- 複数ファイルの一括処理は `xargs` や `git ls-files` などでまとめ、不必要なプロセス spawn と file I/O を避けること

## Desktop 自動実行 state

- Claude Desktop / Claude Code の `~/.claude/tasks` は、UUID ごとの実行ログ、lock、highwatermark を含む runtime state として扱い、安定した宣言的 schedule であることを確認できる場合を除いて dotfiles 管理へ追加しないこと
