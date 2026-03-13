---
name: dotfile-update
description: >
  chezmoi 管理の dotfiles リポジトリで dotfile を追加・変更・削除するためのワークフロースキル。
  `dot_*` ファイル、`.chezmoiignore`、`Brewfile`、共通ルールファイル
  （`dot_claude/CLAUDE.md`、`dot_codex/AGENTS.md`、`dot_qwen/QWEN.md`、`dot_gemini/GEMINI.md`）を
  編集する依頼で必ず使用すること。
  AI 間の設定対応、`json` から `toml` への変換、chezmoi の
  `private_` / `dot_` 属性や source / target の対応確認が関わる依頼にも適用すること。
---

# dotfile-update

chezmoi で管理された dotfiles リポジトリの更新ワークフロー。
このリポジトリでは dotfile の変更は必ずこのスキルのワークフローに従う。

## ワークフロー

事前に [docs/chezmoi-reference.md](../../../docs/chezmoi-reference.md) を確認し、
source state / target state / `.chezmoiignore` の前提を外していないか点検すること。

### 1. ソースファイルの編集

chezmoi のソースファイルを直接編集する。
ホームディレクトリの実ファイルではなく、リポジトリ内のソースを編集すること。

補足:
- repo ローカルの `.claude/skills/` 配下の skill 追加・更新は `dotfile-update` ではなく `skill-creator` の責務として扱う。
- source / target の対応で迷ったら `chezmoi target-path <source-path>` と `chezmoi source-path <target-path>` で確認する。
- `*.md` のドキュメントを更新した場合は、更新後にそのファイル全体を読み直し、重複した指示や矛盾した記述が残っていないか確認する。

### 2. AI 間の設定対応

いずれか 1 つの AI 向け設定を変更するときは、他の AI に相当する設定項目があるかを必ず確認し、反映するかどうかを判断する。
「片方だけ変える」こと自体は許容されるが、確認せずに放置しない。

対応表:

| 設定カテゴリ | Claude | Codex | Qwen | Gemini |
|---|---|---|---|---|
| 指示ファイル | `dot_claude/CLAUDE.md` | `dot_codex/AGENTS.md` | `dot_qwen/QWEN.md` | `dot_gemini/GEMINI.md` |
| クライアント設定 | `dot_claude/settings.json` | `dot_codex/private_config.toml` | `dot_qwen/settings.json` | `dot_gemini/settings.json` |

判断ルール:
- 共通運用ルール、保存方針、Plan ルールのように AI 間でそろえるべき内容は、対応ファイルを確認して必要なら反映する。
- UI 固有設定、provider 固有設定、product 固有キーのように他 AI に等価概念がないものは、無理に横展開しない。
- `json` と `toml` のようにフォーマットが違う場合は、構文を合わせて再構成する。直接コピーしない。
- 対応先があるか曖昧な場合は、既存ファイル内容と product の実在キーを確認してから判断する。
- 反映しなかった場合は、「対応項目なし」「product 固有」「今回は同期不要」など理由を作業結果に残す。
- Gemini の `~/.gemini/` では `settings.json` と `GEMINI.md` を managed 対象候補として確認し、`oauth_creds.json`、`trustedFolders.json`、`history/` などの state ファイルは原則 `.chezmoiignore` で非管理にする。

フォーマット差分の扱い:
- `settings.json` を `config.toml` へそのままコピーしない。必ず `toml` として再構成する。
- JSON のオブジェクトは TOML のテーブルに写像する。入れ子は `[section.subsection]` を使う。
- 文字列・真偽値・数値・配列は型を保って変換する。キー名や型を推測で変えない。
- Claude / Qwen 固有キーを Codex 側に同名キーで作らない。Codex に等価な設定がある場合だけ対応する TOML セクションへ移す。
- Codex 設定は `model`、`model_reasoning_effort`、`approval_policy`、`sandbox_mode`、`[features]`、`[mcp_servers.<name>]` など Codex 実在キーに合わせる。

### 3. 共通ルールの同期

`dot_claude/CLAUDE.md`、`dot_codex/AGENTS.md`、`dot_qwen/QWEN.md` は共通ルールセクションを共有している。
いずれかの共通ルール部分を変更した場合、残りの 2 ファイルにも同じ変更を反映すること。

共通ルールセクションの識別: `# 共通ルール` 見出し配下の箇条書き。

Claude Code 固有ルール（`# Claude Code 固有ルール` 以降）は `dot_claude/CLAUDE.md` のみに存在し、
同期対象外。

### 4. chezmoi apply の実行

編集が完了したら、変更を実機に反映する:

1. `chezmoi diff` で差分を確認し、ユーザーに提示する
2. ユーザーの確認を得てから `chezmoi apply` を実行する（確認なしに自動実行しない）
3. chezmoi が未インストールの場合は `brew install chezmoi` を案内して停止する

### 5. ドリフト確認

apply 後に差分がないことを確認する:

```bash
scripts/chezmoi-drift
```

「差分はありません」と出力されれば完了。

### 6. `.chezmoiignore` の管理

新しいファイルやディレクトリを追加する際、以下に該当するものは `.chezmoiignore` に追記する:
- キャッシュ・ログ・セッション等のトランジェントデータ
- マシン固有の状態ファイル
- リポジトリ専用ファイル（`setup.sh`、`scripts/` 等、既に登録済み）

`.chezmoiignore` の注意:
- パターンは source path ではなく target path に対して書く。
- `dot_claude/...` のような chezmoi ソース名ではなく、`.claude/...` のような最終 target 名で考える。
- 先頭 `.` の source ディレクトリは `.chezmoi*` を除いて既定で無視されるため、repo ローカルの `.claude/skills/` を `.chezmoiignore` で制御しようとしない。

## 注意事項

- `Brewfile` の更新後は `brew bundle` の実行は不要（パッケージインストールはユーザーが別途行う）
- シークレット（API キー等）は `~/.zshenv` に配置し、chezmoi 管理外とする。リポジトリにコミットしない
- pre-commit hook（`.claude/hooks/chezmoi-pre-commit-hook`）がコミット前にドリフトを自動検出する。ドリフトがあるとコミットがブロックされるため、必ず apply まで完了させること
- chezmoi の仕様に自信がない場合は、推測で編集せず公式ドキュメントを確認してから変更すること
- `.claude/skills/` 配下を更新した場合は、`skill-creator` の手順に従い `scripts/quick_validate.py` で基本妥当性を確認すること
