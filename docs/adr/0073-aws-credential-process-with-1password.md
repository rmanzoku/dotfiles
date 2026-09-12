---
title: "AWS SDK の credential_process を 1Password の参照ファイルで供給する"
date: 2026-09-12
worked_at: 2026-09-13T01:41:11+09:00
agent_model: "Codex / GPT-6"
status: accepted
updated_at: 2026-09-13
---

# Context

案件 repo のアクセス標準から、手動配置された AWS credentials を除去し、CLI と Terraform が
同じ profile で認証する要件を引き継いだ。AWS / IAM 側は案件 repo、ローカル実装は dotfiles が所有する。
既存の ADR 0036 は `op run --env-file` と unmanaged の参照ファイルを定めている。

# Decision

- SDK 専用の `op-aws-credential-process` を追加し、明示した 1Password account と profile 専用
  env file から `op run` で取得した IAM 長期鍵を、AWS の Version 1 JSON として SDK へ返す。
- 認証情報はメモリと子プロセスの pipe / environment だけを通し、ファイルやログに保存しない。
  一般用途の `oprun` のマスキングは維持し、このヘルパー内部の受け渡しだけ解除する。
- `op` の起動は呼出元の端末セッションを維持し、タイムアウト用のプロセス群だけを分ける。
  Python 3.11 以降の `process_group=0` を使い、`start_new_session=True` で端末を切り離さない。
  AI の一連の OP 操作は `op-cli-runner` Skill に従い同じ PTY で実行する。
- `~/.aws/config`、profile-to-item の参照ファイル、SSH agent の account / vault 選択は
  unmanaged とする。会社・案件固有値を chezmoi template へ持ち込まない。
- 旧キーの保持をユーザーが選んだ場合、新しい認証経路を合意した別 profile に追加する。
  既存の profile とキーを維持し、具体的な profile 対応は案件 repo に記録する。
- 既存の SSH local include を使い、対象 Host だけに 1Password の `IdentityAgent` を設定する。
  鍵の SSH Key item への登録は人間の対話操作とする。
- SSM plugin は Brewfile に追加し、AWS 側の SSM readiness とローカル導入の検証を分ける。
- 実際の移行手順と成功条件は [AWS access guide](../aws-agent-access.md) に置く。

# Alternatives and consequences

`oprun` は一般コマンド向けであり、SDK の JSON 契約を実装しない。
既存 `op-cli-runner` は出力をログに保存するため、secret を含む credential JSON の生成先には使えない。
この繰り返し発生する secret / account 境界には小さな SDK endpoint が必要で、新しい Skill や汎用 runner は不要。
AI は既存 `op-cli-runner` を AWS コマンド全体の観測に使い、endpoint を直接呼ばない。

AWS shell plugin は Terraform / SDK の共通認証経路にならないため主経路にしない。
AWS config へ SSH 型の include を仮定したり、全 profile をテンプレートで置換したりしない。
SSO 等への移行は案件側の既存判断に従い、この変更では追加しない。

5 分の上限、待機ログ、固定文言の失敗分類を設け、別 account / principal / provider へ再試行しない。
1Password の承認は端末と account に結びつき、同じ端末の子プロセスへ共有される。
Codex のコマンドごとの新セッションと、helper のセッション分離を実機で確認したため、
呼出元から `op` まで端末を維持する。別々の端末間での共有や、無操作 10 分・最大 12 時間・
アプリロックによる失効は変更しない。認証維持だけの常駐化・定期呼出し・ディスクキャッシュは追加しない。
[1Password の公式仕様](https://www.1password.dev/cli/app-integration-security)に従う。
新経路を STS で検証するまでは既存 credentials を削除しない。
SSH agent の有効化と鍵登録、および AWS 側の SSM 設定が未完なら、ローカル実装だけで接続完了とはしない。

Terraform AWS provider 6.21.0 の実機検証で、`credential_process` の設定値が先頭・末尾とも
二重引用符の場合に起動が exit 127 となった。秘密情報を使わない `/usr/bin/true` でも再現し、
最後に引用符不要の account サインインアドレスを置く形ではプロセス起動に進むことを確認した。
設定手順をこの記法に統一する。別 SDK / principal への切替で回避せず、同じ profile の記法を修正する。
