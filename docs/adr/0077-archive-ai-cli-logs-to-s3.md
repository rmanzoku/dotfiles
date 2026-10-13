---
title: "AI CLI のセッションログを S3 へ日次差分で退避する"
date: 2026-10-14
worked_at: 2026-10-14T00:30:14+09:00
agent_model: "Claude Code / Opus 5.5"
status: accepted
---

# Context

Claude Code と Codex のセッションログは、ローカルで 2026-10 時点で合計約 18 GB ある。
2026-09 以降は月 8〜9 GB のペースで増えている。
Claude Code は `cleanupPeriodDays` の既定値 30 日でトランスクリプトを削除するため、
退避しないと古いログが失われる。

保存先として Google Drive（Workspace の 30 GB 枠）も検討したが、半年ほどで容量を使い切る。
差分判定も自前で実装する必要がある。

# Decision

- 保存先は所有者の個人 AWS アカウントの S3 バケットとする（東京リージョン）。
  - 非公開、Block Public Access は有効、SSE はデフォルト、バージョニングは無効。
- ライフサイクルルールで 30 日後に Glacier Instant Retrieval へ移す。
  - アップロード時は STANDARD のままにする。追記中のファイルを上書きしても、
    Glacier IR の 90 日最低保存料金がかからないようにするため。
- `~/.local/bin/ai-log-archive` が `aws s3 sync` で次のディレクトリを
  `s3://<bucket>/<LocalHostName>/<name>/` へコピーする。
  - `~/.claude/projects`
  - `~/.codex/sessions`
  - `~/.codex/archived_sessions`
  - 圧縮はしない。S3 側も含め、どこでも削除しない（`--delete` は使わない）。
- launchd（`local.ai-log-archive`）で毎日 03:00 に起動する。
  - スリープ中に時刻を過ぎた場合は、復帰時に 1 回実行される。
  - 起動できなかった日の分は、次の実行で差分として追いつく。
- ローカルの保持期間は各 CLI の設定に従う。目安は 3 ヶ月。
  - Claude Code は `cleanupPeriodDays: 90` とする。
  - Codex には保持期間の設定がないため、削除処理は追加しない。
- 認証情報の扱いは、1Password を経由しない例外とする（所有者の判断）。
  - このバケット専用の IAM ユーザーを作り、`~/.aws/credentials` の専用 profile に置く。
  - 権限は `s3:ListBucket` と `s3:PutObject` だけに絞る。
  - 理由: launchd は端末を持たないため、ADR 0073 の 1Password 承認フローでは無人で実行できない。
- バケット名と profile 名は所有者固有の値なので git には置かない。
  - unmanaged の `~/.config/ai-log-archive/env` に
    `AI_LOG_ARCHIVE_BUCKET` と `AI_LOG_ARCHIVE_AWS_PROFILE` を書く。secret は書かない。

# Alternatives and consequences

- Google Drive: 容量の上限があり、gws をファイルごとに呼ぶ実装が必要なため採らない。
- 1Password service account / 実行ごとの承認: 前者はトークンという別の secret の置き場所が要る。
  後者は毎日承認画面が出る可能性があるため、所有者が採らなかった。
- 最小権限でも `PutObject` は上書きできる。鍵が漏れた場合に既存ログが改ざんされる可能性は受け入れる。
  - 削除権限と読み取り権限は付けない。
- Codex がファイルを `sessions` から `archived_sessions` へ移すと、S3 には両方が残る。
  コストは小さいため許容する。
- 進捗は `~/Library/Logs/ai-log-archive.log` に開始・ソースごとの結果・終了を記録する。
  失敗したソースは exit 1 で残り、次回の実行で再送される。

# Setup

AWS 側の作成は 1 回だけ行う。
1. 所有者がアップロード用の IAM ユーザーを作る。アクセスキーを `~/.aws/credentials` の専用 profile に置き、一時的に管理者権限を付ける。
   この profile でバケットを作成し、ライフサイクルルールを付ける。
2. 同じユーザーに次の inline policy を付けてから、管理者権限を外す。
   外したあとは、`iam` 操作が拒否されることを確認する。

   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {"Effect": "Allow", "Action": "s3:ListBucket", "Resource": "arn:aws:s3:::<bucket>"},
       {"Effect": "Allow", "Action": "s3:PutObject", "Resource": "arn:aws:s3:::<bucket>/*"}
     ]
   }
   ```

3. `~/.aws/credentials` は owner-only（600）にする。
4. `~/.config/ai-log-archive/env` を作り、手動で `ai-log-archive` を 1 回実行して初回分を上げる。
5. `launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/local.ai-log-archive.plist` で登録する。

別のマシンでは、同じ IAM ユーザーのアクセスキーを `~/.aws/credentials` の専用 profile に置き、手順 3〜5 を行う。S3 のキーは `<LocalHostName>/` で分かれるため、マシン同士で衝突しない。
