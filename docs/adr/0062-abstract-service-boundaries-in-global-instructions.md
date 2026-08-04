---
title: "ADR 0062: グローバル指示の境界ルールはサービス名を挙げず抽象化する"
status: accepted
date: 2026-08-04
worked_at: 2026-08-04 14:20 JST
agent_model: Claude Fable 5
---

# ADR 0062: グローバル指示の境界ルールはサービス名を挙げず抽象化する

## Context

圧縮後の共通ルール(ADR-0061)には、サービス名を名指しした境界ルールが 2 本残っていた。

1. Freee / Google の書き込み系操作での principal / company / profile 自動切替禁止
2. secret の 1Password 運用(op コマンド列挙と `~/.config/op/dotfiles.env` / `~/.zshenv.local` のパス詳細を含む)

ユーザーレビューで 2 つの問題が指摘された。第一に、固有名詞の列挙は「名指しされていないサービスなら切替してよい」という逆読みを誘発する。実際、ADR-0061 の hold-out 検証で実行者が「対象 API は Freee/Google ではないため当該ルールは適用対象外」と推論する様子が観測されていた。第二に、パスやコマンドの詳細は op-cli-runner / onepassword-secret-materialize / gws-cli-runner などの skill と dotfiles repo AGENTS.md が正本であり、グローバルへの再掲は「詳細運用は repo docs / Skill を優先」という自身のルールに違反する。「skill が呼ばれない可能性」は skill の発火(description / trigger)の問題として別レイヤで解くべきで、その補償としてグローバルへ固有詳細を漏らさない。

## Decision

1. principal 境界ルールをサービス非依存に抽象化する: 「外部サービスへの作成・更新・削除・送信・承認・共有・権限変更では、失敗や権限エラーを別 principal / 別 company / 別 profile への自動切替で回避しない。読み取り診断でも同様。必要なら principal を明示して再実行し、解消しなければ停止して確認」。Freee / Google は例示としても残さない
2. secret ルールを不変条件だけに縮める: 「secret 実値を 1Password の外へ出さない。コード・設定ファイル・ログ・チャット出力に書かず、受け渡しは `op://...` secret reference 経由」。op コマンドの列挙とパス詳細は削除し、op-cli-runner / onepassword-secret-materialize skill と dotfiles repo AGENTS.md を正本とする(repo 側は従来の詳細記述を保持)
3. 1Password の名指しは維持する。適用先の列挙(開集合)と、指定した唯一の置き場の名前(閉じた選択)は別物として扱う
4. 配置原則: グローバル指示にはサービス非依存の不変条件だけを置き、サービス固有の境界・手順は対応 skill を正本とする。skill の発火漏れは description / trigger 側の欠陥として扱い、グローバルへの詳細再掲で補償しない
5. 抽象化の有効性は、旧版で「対象外」と推論された名指し外サービス(AWS profile / GitHub account)を使った単発プローブで確認する

## Consequences

- 新規サービス(AWS、Stripe 等)の principal 境界が、ルール追記なしで最初から拘束される
- Freee / Google の具体的な操作規律は freee-api-skill(外部)、gws-cli-runner、freee MCP server instructions が担う
- 配備サイズ: 61 行 / 5,073 字(ADR-0061 時点から -107 字)
