# 共通ルール

- 日本語で応答すること
- MCP サーバーよりも CLI ツールの利用を優先して検討すること
- 実装前に、仮定・不明点・複数解釈・重要なトレードオフを明示し、仕様・契約・データ形式などの永続判断は既存実装・テスト・文書・ユーザー確認に基づかない限り作らず、不足時は仮実装・仮差分・コード例を提示せず確認事項と検証計画に留めること
- 要求を満たす最小の実装を優先し、依頼されていない機能・抽象化・設定項目・将来対応を追加しないこと
- 既存コードや文書を編集するときは、ユーザー依頼に直接必要な行だけを変更し、隣接する無関係なリファクタ・整形・削除を行わないこと
- 作業の成功条件を検証可能な形で定め、バグ修正や機能追加では再現・テスト・差分確認などの具体的な確認手段まで含めて完了判断すること
- 再現テストを書くときは、観測済みの失敗と既存契約だけを固定し、未確認の戻り値・エラー型・出力形式を新しい期待値として作らないこと
- secret 実値は 1Password に保存し、CLI では `op run --env-file` / `op read` と `op://...` secret reference 経由で受け渡すこと
- `~/.config/op/dotfiles.env` は管理外の secret reference 置き場とし、実値を書かないこと
- `~/.zshenv.local` は secret の置き場ではなく、マシン固有の非 secret local override に限定すること
- 永続的に参照すべき指示や、worktree / セッションをまたいで再現が必要な情報は Memory ではなく git 管理ファイルに保存すること
- 継続的な指示の保存先は、作業リポジトリの `docs/`、`.agents/`、またはグローバル dotfiles（例: `~/.codex/AGENTS.md`）を使うこと
- 恒久性のあるユーザー指示、再発しやすい運用判断、複数回参照しそうな手順は、原則その作業ターン内で git 管理ファイルへ反映すること
- 反映先は、運用ルールや判断基準なら現在作業中のリポジトリの正規指示ファイル（通常は `AGENTS.md`）と AI 別指示ファイル、背景や継続判断なら `docs/adr/`、反復手順や更新フローなら対応 Skill を使い分けること
- 反映先に迷う場合は、まず現在作業中のリポジトリの正規指示ファイルを優先し、AI 固有の挙動だけ AI 別指示ファイルへ、背景・採用理由・長期判断だけ `docs/adr/` へ分離すること
- 反映不要とする例外は、一過性の事情、既存文書に重複する内容、ユーザーが今回は文書化不要と明示した場合に限ること
- 例外を適用した場合は、反映しなかった理由を作業結果に残すこと
- 一時ファイル、下書き、調査メモなどの一過性ファイルは作業 worktree 内の `.context/` に生成すること
- AI 間や CLI 間で複数行や構造化された内容を受け渡すときは、作業 worktree 内の `.context/` に置いた実ファイル経由を標準とし、`-p` などの引数へのインライン展開や here-doc 直書きは原則避けること
- パイプでの受け渡しは、単一のコマンドが標準入力をただちに 1 回だけ読む単発処理に限って許容し、再読・再送・サブプロセス引き継ぎ・別 Agent への移譲が絡む場合は実ファイル経由を優先すること
- `/private` や `/tmp` は一時ファイル置き場として使わないこと
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
- 外部 CLI / MCP / runner / Skill の詳細な運用ルールは、作業中リポジトリに正規 docs / Skill がある場合はそちらを優先すること
- 新しい永続的な Skill / Runner / wrapper を作る前に、既存 docs / Skill / wrapper / runner adapter で足りるか確認すること
- Phase / Step を持つ作業では、各 Phase / Step の完了前に `.context/` 配下へ中間成果物 artifact を保存すること
- 次の Phase / Step へ進む条件は、対応する artifact の生成とすること
- 口頭合意、推論上の完了宣言、Memory 内だけの状態遷移で Phase / Step を進めてはならない
- artifact の初期必須項目は `task`、`phase_or_step`、`created_at` とし、Markdown は Front Matter、JSON は同名キーで保持すること
- artifact の推奨命名は `.context/<task-or-date>/<nn>-<phase-name>.(md|json)` とし、同名更新時は最新更新時刻のファイルのみを有効扱いにすること
- 非 Phase 作業は artifact 必須対象外とする。ただし単発例外として artifact gate を明示的にバイパスする場合だけ `.context/single-step/<task>.json` を使い、`enabled=true`、`task`、`reason`、`expires_at` を必須とすること
- Phase / Step 遷移の最小原則は現在作業中のリポジトリの正規指示ファイル（通常は `AGENTS.md`）を正本とし、各 Skill 固有の required artifact は `SKILL.md` を正本とすること
- 現在作業中のリポジトリの正規指示ファイル（通常は `AGENTS.md`）と `SKILL.md` が競合する場合は `SKILL.md` をその Skill 実行中の具体契約として優先し、正規指示ファイルは下限ルールとして常に適用すること
- `*.md` ファイルを編集した際は、ファイル全体を見直し、矛盾・重複・ルール漏れが発生していないか必ず確認し、必要なら同じターンで修正すること
- `*.md` ファイルのメタデータは本文に書かず、必ず Front Matter で管理すること
- アーキテクチャ、運用方針、永続設定、複数ファイルにまたがるワークフロー変更などの大きめの変更では、作業リポジトリの `docs/adr/` に ADR を作成または更新すること
- ADR には、少なくとも作業日時と作業した Agent のモデル名を記載すること
- Codex / Claude Desktop などの自動実行定義は、再現可能な宣言的設定だけを chezmoi 配下で管理し、lock、jitter salt、highwatermark、実行ログ、セッション履歴、UUID ごとの task 実行状態は machine-local state として管理対象外にすること

# Plan 共通ルール

- Phase を含む Plan では、各 Phase ごとに使用する Skill を明示し、使用しない Phase は `なし` と明記すること
- Phase を含む Plan は、実行時に途中確認を前提にせず完走できる粒度で提示し、Phase 提示後は不測の事態がない限り追加許可を求めず停止せず最後まで進めること。ただし、既存 Skill や repo ルールで明示された事前確認は例外として維持すること

# Codex 固有ルール

## Config / Trust 運用

- Codex の repo enforcement 用 hook は repo ローカル `.codex/hooks.json` を正本とし、`~/.codex/hooks.json` は個人通知などのグローバル用途だけに使うこと
- Codex の hook は `artifact gate` の補助 enforcement として使い、自然言語の意味理解や「本当に完了したか」の判定は持たせないこと
- validator が検査する範囲は `.context/` の artifact 存在、初期必須キー、単発例外宣言ファイルの妥当性までに限定すること
- Codex の trust 設定は原則 `~/.codex/config.toml` に集約し、`[projects."<path>"]` は常用しないこと
- project-scoped `.codex/config.toml` を読む必要がある repo / worktree だけ、例外として対応する `trust_level = "trusted"` を追加すること
- 例外追加前に、その repo に project 固有の Codex 設定が本当に必要か確認すること
- 通常運用で権限不足が出た場合は、恒久設定を緩めず、その実行時だけ `danger-full-access` を使うこと

## Subagents / Custom Agents 運用

- Codex の custom agent は親スレッドの全コンテキストを暗黙に継承する前提で使わないこと
- Codex では、モデルを横に並べるためだけの委譲よりも、役割が明確な custom agent への委譲を優先すること
- custom agent が利用できない場合は、利用不能理由と代替方針を明示し、委譲したものとして扱わず、親 Codex の限定判断として作業範囲と検証方法を示すこと
- 複数 role にまたがる依頼では主論点で primary custom agent を選び、必要な場合だけ不足観点を別 role へ追加委譲すること。`build-vs-buy` のように事業判断と技術不可逆性が混ざる場合は、事業判断を `biz`、技術リスクや長期保守性を `tech` に分けて扱うこと
- `tech` は、設計レビュー、実装方針の検証、コードレビュー、アーキテクチャ判断、不可逆リスクや長期保守性の評価に使うこと
- `biz` は、事業前提、顧客価値、収益性、運用設計、市場・競合観点、意思決定のトレードオフ整理に使うこと
- `personal` は、予定調整、タスク整理、連絡文案、調査メモ整理、日程・優先度・実務段取りの整理に使い、共有する個人情報は必要最小限に要約し、secret 実値、認証情報、secret reference 自体とその解決結果、認証済みセッション情報を扱わせないこと
- `personal` へ予定や連絡文脈を渡す場合は、原則として raw の予定本文、参加者一覧、連絡先一覧を渡さず、日時、相手、期限、要対応事項、文案目的の要約に絞ること
- ユーザーが親 Codex に 1Password や secret 閲覧を許可した場合でも、その許可を `personal` などの委譲先への secret 共有許可とは扱わないこと
- 技術レビュー custom agent と `fork_context=true` を同時に使えない runtime 制約が観測された場合、親 Codex が必要な repo context、依頼内容、対象ファイル、関連 `AGENTS.md`、ADR、docs、検証ログ、既知の制約を明示的に渡すこと
- `tech` へ委譲するときは、少なくとも関連するビジネス前提（該当しない場合は「該当なし」）、規模、フェーズ、体制、不可逆リスク、既存 ADR の有無、参照してほしい evaluator / skill を親 prompt に含めること
- `tech` のレビューでは、`if`、デフォルト値、マジックナンバー、Boolean 引数、sentinel value、文字列モード、単位のない値、暗黙 fallback、深い層での env/config 参照を、仕様判断・責任・単位・状態が匿名で埋もれていないかの観測点として確認すること。ドメイン上の意味を持つ値や分岐は、名前付き定数、型、enum、policy、明示入力、境界での検証に寄せ、コメントは背景・制約・トレードオフを補うために使い、コード上の意図不足を埋める代替にしないこと
- custom agent からの判断は、渡された context に基づく限定判断として扱い、親 Codex は最終判断前に実リポジトリのコード・設定・テスト・docs へ戻って確認すること

## Automations 運用

- Codex Desktop の automation は `~/.codex/automations/<automation-id>/automation.toml` を実行設定として扱い、secret を含まないものだけ dotfiles の source で管理すること
- `~/.codex/automations/<automation-id>/memory.md` は Desktop が更新する運用 state として扱い、管理対象にしないこと
- `~/.codex/automations/.run-jitter-salt` は machine-local state として管理しないこと
