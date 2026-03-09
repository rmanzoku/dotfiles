# 共通ルール

- 日本語で応答すること
- MCP サーバーよりも CLI ツールの利用を優先して検討すること

# Claude Code 固有ルール

- コミット前に、auto memory（~/.claude/projects/*/memory/）に保存された内容のうちプロジェクトに有用なものがあれば、プロジェクトの CLAUDE.md に反映するか確認すること
- Plan をユーザーに提示する前に、Codex でレビューを行いフィードバックを反映すること。勝手にモデルとReasoningを変更しないこと。コマンドパターン:

```bash
codex exec --full-auto -m gpt-5.3-codex-spark \
  -c model_reasoning_effort="medium" \
  -C <project_root> \
  "$(cat <<'PROMPT'
あなたはプランレビュアーです。以下のファイルを読んでレビューしてください。

1. レビュー対象プラン: <plan_file_path>
2. 参考ファイル: <reference_file_paths...>

レビュー観点:
- スキルを適切に使用しているか？
<観点リスト>

各観点について PASS / ISSUE / SUGGESTION で評価し、ISSUEの場合は具体的な修正案を述べてください。
PROMPT
)"
```

  - ポイント: プロンプトにファイル内容をインライン展開せず、**ファイルパスを渡して Codex に読ませる**
  - heredoc (`<<'PROMPT'`) で複数行プロンプトを渡す
  - `-C` でプロジェクトルートを指定し、Codex がリポジトリ内ファイルを参照できるようにする
  - 出力が大きい場合は `2>&1` でリダイレクトし、保存されたファイルを Read で確認する
  - レビュー観点にスキルを適切に使用しているかどうかを入れる
