---
title: "AC接続中のMac稼働維持"
updated_at: 2026-09-14
---

# AC接続中のMac稼働維持

macOS標準のcaffeinate -sをユーザーLaunchAgentで起動する。
ACではスリープを抑止し、バッテリーではその抑止が無効になる。
外部ディスプレイなしの閉蓋ではDarkWakeになる場合があり、全アプリの連続処理を保証しない。
導入前の短時間実機試験と、常駐構成の起動・異常終了後の再起動・停止・撤去を検証済み。
ログイン時起動と長時間の作業継続は未検証。
判断根拠と限界は[ADR 0078](adr/0078-use-caffeinate-for-ac-awake.md)を参照。

## 導入と有効化

dotfile-updateの差分確認・承認後、対象ファイルだけを配備する。
plistはDisabled=trueなので、使うMacでのみ次を実行する。
ホームディレクトリ直下のLibrary/Logsが存在することを事前確認する。

```sh
chezmoi apply ~/Library/LaunchAgents/local.ac-awake.plist
launchctl enable "gui/$(id -u)/local.ac-awake"
launchctl bootstrap "gui/$(id -u)" ~/Library/LaunchAgents/local.ac-awake.plist
```

KeepAliveでログイン時起動と異常終了後の再起動を行う。killだけでは停止し続けない。
macOSの画面ロック設定や電源設定、FileVault設定は変更しない。

## 確認

```sh
launchctl print "gui/$(id -u)/local.ac-awake"
pmset -g batt
pmset -g assertions
```

launchctlのstate、pid、runs、last exit codeを確認し、pmsetの所有PIDと照合する。
エラー出力は ~/Library/Logs/local.ac-awake.err.log に記録される。
バッテリーではassertionが一覧に残っても無効になり得る。
画面共有の抑止と区別し、集計値だけでこのサービスの効果を判断しない。

実機試験は手元で開蓋復旧できる状況で行う。AC閉蓋で接続切断後も処理が継続すること、
Batteryでは閉蓋Sleepに戻ること、AC復帰、異常終了、ログイン時起動、画面ロックを個別に確認する。
再起動後の復帰は[リモートアクセスの手順](tailscale-remote-access.md#restart-and-login-checks)も参照。

## 停止・再開・撤去

蓋を開けてから停止する。

```sh
launchctl bootout "gui/$(id -u)/local.ac-awake"
```

再開は上記bootstrapコマンドを使う。次のログイン以降も止める場合は、さらに次を実行する。

```sh
launchctl disable "gui/$(id -u)/local.ac-awake"
```

撤去する場合は停止・無効化後に対象plistを削除する。再配備も不要ならchezmoi sourceを削除するか、
そのMacのignore設定で対象targetを除外する。最後に所有assertionが消えたこととpmset設定が元の値であることを確認する。
電源設定の書込みを行わないため、スリープ禁止値を手動で戻す処理は不要。

撤去試験後に再配備すると、chezmoiがtargetの手動削除を検出して確認を求める場合がある。
端末で対象だけをapplyし、自分が削除した対象で差分が意図どおりと確認してからoverwriteを選ぶ。
TTYがない環境ではTTY付きで実行し、他の差分まで一括上書きしない。
