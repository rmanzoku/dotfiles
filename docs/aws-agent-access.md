---
title: "AWS credentials and EC2 access through 1Password"
date: 2026-09-12
updated_at: 2026-09-13
agent_model: "Codex / GPT-6"
---

# AWS credentials and EC2 access through 1Password

AWS CLI、Terraform、対応 SDK は、同じ AWS profile の `credential_process` から
1Password の IAM access key を実行時に取得する。EC2 への主経路は SSM Session Manager、
SSH は案件側の標準が認める場合の手動選択経路とする。

## 管理するもの

| 対象 | 管理方法 |
|---|---|
| `~/.local/bin/op-aws-credential-process` | chezmoi。SDK 専用の認証情報受け渡し |
| `session-manager-plugin` | Brewfile の cask。AWS CLI と 1Password CLI も既存 Brewfile で導入 |
| `~/.aws/config` | unmanaged。profile、region、account、参照ファイルの対応 |
| `~/.config/op/aws/<profile>.env` | unmanaged、0600。2 フィールドの secret reference のみ |
| `~/.config/1Password/ssh/agent.toml` | unmanaged、0600。公開対象 account / vault の限定 |
| `~/.ssh/config.local` | unmanaged。案件ごとのホストと `IdentityAgent` |

具体的な profile 名、account / vault / item、参照は git へ書かない。
AWS config には SSH の `Include` を流用せず、既存ファイルの必要な profile だけを更新する。
ローカル設定の別マシンへの復元は既存の `onepassword-secret-materialize` の
`Secrets Manifest` を使う。IAM 鍵そのものは materialize しない。

## AWS profile の設定

1Password アプリの CLI 連携を有効にし、担当者の account を使用する。
対象 IAM key の item とフィールドを確認し、フィールドの **Copy Secret Reference** で
取得した参照を、ローカルの profile 専用 env file に保存する。
API Credential の既定フィールドを使う場合、アクセスキー ID は `username`、シークレットは
`credential` に保存できる。フィールドの表示名を推測せず、実際の参照を使う。
`AWS_ACCESS_KEY_ID` と `AWS_SECRET_ACCESS_KEY` の 2 行を `KEY=op://...` 形式で指定する。
参照には同じ vault / item を使う。任意の前後空白、行コメント、値全体の引用符は許容するが、
変数展開、行末コメント、追加の変数、平文の鍵は受け付けない。
ファイルは所有者のみ読み書き可能な 0600 にする。

`~/.aws/config` の対象 `[profile <profile>]` に次の `credential_process` を指定する。
これは **設定値の形**であり、直接実行するコマンドではない。

```ini
credential_process = "/absolute/home/.local/bin/op-aws-credential-process" --env-file "/absolute/home/.config/op/aws/<profile>.env" --account <account-sign-in-address>
```

パスは実際の絶対パスに置き換える。AWS の仕様に従い `~` / `$HOME` を使わない。
最後の account には空白や shell の特殊文字を含まないサインインアドレスを指定する。
Terraform AWS provider 6.21.0 の検証では、設定値が先頭・末尾とも二重引用符の形だと
コマンドが終了コード 127 で起動に失敗した。上記の並びを使い、設定値全体を引用符で囲まない。
region と profile 名は案件の既存設定に合わせる。

ヘルパーは `op run --env-file` で参照を解決し、AWS の Version 1 JSON を SDK の pipe に返す。
IAM 長期鍵を対象とし、Expiration やディスクキャッシュは作らない。
`op run` のマスキング解除はこの内部 pipe のみに限定する。
AI はヘルパーや内部 `--emit` を直接実行・ログ保存せず、AWS CLI / SDK を通して利用する。
pipe 検査は誤操作を減らすガードで、呼出元の認証ではない。

開始・15 秒ごとの待機・完了・失敗を stderr に記録し、5 分で打ち切る。
呼び出し元 SDK がより短い期限を設けている場合は、その期限が先に作用する。
成功時の stderr は SDK が表示しない場合があるため、AI の実機検証は `op-cli-runner` で
AWS コマンド全体を包み、進捗を記録する。認証エラー時は再試行や別 account への切替をせず停止する。
ヘルパーは provider の生 stderr と secret をログに転送しない。
既存 `oprun` は一般コマンド用なので変更しない。AWS shell plugin の初期化は不要。

## 端末セッションと承認の再利用

ヘルパーは Python 3.11 以降を使い、呼び出し元の端末セッションを維持して `op` を起動する。
タイムアウト時の終了対象だけを独立したプロセス群にし、端末から切り離さない。
AI は `op-cli-runner` の手順に従い、一連の AWS / OP 操作を同じ PTY 内でまとめるか、
実行中の端末セッションを継続利用する。毎回新しい PTY を作っても承認は引き継がれない。
ヘルパーは別々の端末を統合せず、認証維持だけの常駐プロセスや定期呼び出しも作らない。

1Password の macOS / Linux アプリ連携は、同じ account・端末内の子プロセスへ承認を共有する。
無操作 10 分、最大 12 時間、またはアプリのロックで失効するため、承認回数が常に 1 回とは保証しない。
Mac の画面ロック（ディスプレイ消灯・蓋閉じ）でアプリも同時にロックされ、承認は全て失効する。
ロック中の承認要求は即時 `promptError`、その後の要求は約 60 秒の承認タイムアウトで失敗する（2026-09-14 実機確認）。
10 分を超える AWS 処理は、`op-cli-runner` の `scripts/with_aws_session.sh`（`bash` で実行）で開始時に 1 回だけ承認を受け、
`sts get-session-token` の一時認証情報（既定 4 時間、最大 36 時間）をジョブのプロセス環境変数だけに載せて走り切る。
ジョブ側は `aws --profile` を使わず `AWS_PROFILE` に依存すること（明示 `--profile` は環境変数の認証情報を無視する）。
これは OP の承認再利用であり、AWS 認証情報のディスクキャッシュは追加しない。
[公式の承認モデル](https://www.1password.dev/cli/app-integration-security)を参照する。

## 移行と検証

1. profile 設定と参照ファイルを用意する。既存 `~/.aws/config` の他 profile は保持する。
2. `AWS_SHARED_CREDENTIALS_FILE` に存在する空ファイルを指定し、AWS の認証用環境変数を
   外した状態で `aws --profile <profile> sts get-caller-identity` を実行する。
   空ファイルや検証結果は作業 repo の `.context/` に置き、返った principal を既存の記録と照合する。
3. 同じ profile を指定した SDK / Terraform の読み取り確認を行う。
4. 新経路が通った後に限り、保持不要と確認できた `~/.aws/credentials` の対象セクションを削除する。
   旧キーを保持する場合は、ユーザーと合意した別 profile に新経路を追加し、既存 profile を維持する。
   同じ profile に shared credentials と `credential_process` を併記して新経路へ移行したと扱わない。
   他セクションを保持し、secret を含むバックアップや差分を `.context/` へ複製しない。
   旧キーが新 item と異なる場合は、削除前に復旧元を確認するか、削除自体の明示的な了承を得る。
5. 空ファイル指定を外し、STS を再確認する。
6. `aws --profile <profile> ssm describe-instance-information` と、対象を確認したうえで
   `aws --profile <profile> ssm start-session --target <instance-id>` を実行する。
   AWS 側の IAM policy、EC2 instance role、SSM agent、ネットワークは案件 repo の責務。
   セッション文書の指定も、その IAM policy に許可されたものへ合わせる。

鍵の取得成功だけで SSM 接続成功と報告しない。SSM 不成立時に SSH へ自動切替しない。

## 1Password SSH agent

1Password アプリで SSH agent を有効にし、必要な鍵を **SSH Key** item として登録する。
Developer 画面から SSH agent の設定を開く版では、鍵名の保存確認などの初期設定も完了させる。
設定ボタンを押しただけで有効化済みとせず、socket の存在と `ssh-add -l` で確認する。
Document の鍵を一時ファイルにダウンロードして代用しない。対話的な鍵登録は担当者が行う。

`~/.config/1Password/ssh/agent.toml` に案件指定の account / vault を明示する。
既存設定がある場合、他案件の鍵公開範囲を黙って追加・削除せず、所有する案件の規約を確認する。

```toml
[[ssh-keys]]
account = "<account sign-in address>"
vault = "<approved vault>"
```

macOS では `~/.ssh/config.local` の対象 Host ブロックだけに次を指定する。
GitHub 等の既存 SSH 設定はそのまま維持する。

```sshconfig
IdentityAgent "~/Library/Group Containers/2BUA8C4S2C.com.1password/t/agent.sock"
IdentityFile none
IdentitiesOnly no
```

同じ socket を `SSH_AUTH_SOCK` に指定した `ssh-add -l` で鍵の公開を確認する。
`ssh -G <host>` で対象ホストの `identityagent` を確認し、接続先・host key を確認して SSH 接続する。
上の設定はローカルの秘密鍵を読み込まず、選択した agent の鍵を使う。
`IdentitiesOnly yes` を使う場合は当該鍵の公開鍵を `IdentityFile` に指定する。
private key をローカルに保存しない。

バックグラウンドからの SSH 署名要求は、1Password のメニューバーアイコンに承認待ちとして
通知される場合がある。実機では 60 秒の承認待ち期限切れが、SSH 側の
`communication with agent failed` として現れた。鍵が列挙できても署名承認の完了とは扱わず、
1Password のログで原因を確認し、担当者が承認できる状態になってから再実行する。

## References

- [AWS external credential process](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-sourcing-external.html)
- [AWS SDK process provider support](https://docs.aws.amazon.com/sdkref/latest/guide/feature-process-credentials.html)
- [1Password op run](https://www.1password.dev/cli/reference/commands/run)
- [1Password SSH agent config](https://www.1password.dev/ssh/agent/config)
- [1Password SSH agent authorization](https://www.1password.dev/ssh/agent/security)
- [Session Manager Homebrew cask](https://formulae.brew.sh/cask/session-manager-plugin)
- [ADR 0073](adr/0073-aws-credential-process-with-1password.md)
