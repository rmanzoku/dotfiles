# 共通ルール

- 日本語で応答すること
- MCP サーバーよりも CLI ツールの利用を優先して検討すること
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

# Plan 共通ルール

- Plan をユーザーに提示する前に、必ず簡易レビューを実行すること
- この手順はすべての Plan 提示に適用し、同一セッションの 2 回目以降でも省略してはならない
- Plan レビューの準備では、plan 本文を作業 worktree 内の `.context/` に一時ファイルとして保存し、その実ファイルパスを reviewer に渡すこと
- Phase を含む Plan では、各 Phase ごとに使用する Skill を明示し、使用しない Phase は `なし` と明記すること
- Phase を含む Plan は、実行時に途中確認を前提にせず完走できる粒度で提示し、Phase 提示後は不測の事態がない限り追加許可を求めず停止せず最後まで進めること。ただし、既存 Skill や repo ルールで明示された事前確認は例外として維持すること
- レビューでは、下記テンプレートを変更せず使用すること
- レビュー結果に `ISSUE` がある場合は Plan を修正し、再レビュー後に提示すること
- レビュー結果の妥当性を判断しきれない場合は、Plan を提示せずユーザーに判断を仰ぐこと
- 以上を満たさない場合は Plan を提示してはならない

## レビュー実行テンプレート

テンプレートを使うときは、`<plan_file_path>` に `.context/` 配下の実ファイルパスを入れること。
`<reference_file_paths...>` にはレビュー根拠として使う既存ファイルの実パスを列挙すること。
plan 本文を shell に直接埋め込まないこと。特に `/dev/stdin`、`/dev/fd/*`、plan 本文の here-doc 直書きは使わないこと。
backtick を含む plan でも shell quoting が壊れないよう、review 対象はファイルに保存してから reviewer へ渡すこと。
下記固定テンプレート内の here-doc はレビュー依頼文を組み立てるための例外として許容し、レビュー対象の plan 本文や複数行成果物を here-doc へ埋め込むことは引き続き禁止すること。

```bash
prompt="$(cat <<'PROMPT'
あなたはプランレビュアーです。以下のプランを簡易レビューしてください。

1. レビュー対象プラン: <plan_file_path>
2. 参考ファイル: <reference_file_paths...>

確認観点:
- ユーザー要求から外れていないか
- スキルを適切に使用しているか
- 実装者に追加判断を残していないか
- 根拠のない決定や先送りが入っていないか
- スコープ外として扱う項目を、理由なく無視していないか
- スコープ外の変更や過剰設計が入っていないか
- 必要なテスト観点と受け入れ条件が欠けていないか

各観点について PASS / ISSUE / SUGGESTION で評価し、ISSUE があれば簡潔な修正案を述べてください。
PROMPT
)"

codex exec --full-auto -m gpt-5.4-mini \
  -c model_reasoning_effort="medium" \
  -c service_tier="fast" \
  -C <project_root> \
  "$prompt"
```

# Codex 固有ルール

## Config / Trust 運用

- Codex の repo enforcement 用 hook は repo ローカル `.codex/hooks.json` を正本とし、`~/.codex/hooks.json` は個人通知などのグローバル用途だけに使うこと
- Codex の hook は `artifact gate` の補助 enforcement として使い、自然言語の意味理解や「本当に完了したか」の判定は持たせないこと
- validator が検査する範囲は `.context/` の artifact 存在、初期必須キー、単発例外宣言ファイルの妥当性までに限定すること
- Codex の trust 設定は原則 `~/.codex/config.toml` に集約し、`[projects."<path>"]` は常用しないこと
- project-scoped `.codex/config.toml` を読む必要がある repo / worktree だけ、例外として対応する `trust_level = "trusted"` を追加すること
- 例外追加前に、その repo に project 固有の Codex 設定が本当に必要か確認すること
- 通常運用で権限不足が出た場合は、恒久設定を緩めず、その実行時だけ `danger-full-access` を使うこと
