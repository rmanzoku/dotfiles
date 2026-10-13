---
title: "Use an opt-in caffeinate LaunchAgent for AC-only awake operation"
created_at: 2026-09-14T17:20:00+09:00
agent_model: GPT-6
status: accepted-with-validation-limits
updated_at: 2026-09-14T18:55:25+09:00
---

# AC接続時の稼働維持

外部ディスプレイなしでAC接続中の閉蓋稼働を行い、バッテリーでは閉蓋スリープへ戻す。
電源設定を永続変更するpmset disablesleepは全体設定で、監視停止時の残留が問題になる。

macOS標準のcaffeinate -sをユーザーLaunchAgentで起動する構成を採用する。
現地manのAC限定契約と、macOS 26.6.1の実機試験に基づく。root権限と独自監視wrapperは追加しない。
KeepAliveで異常終了後に再起動する。Disabled=trueを配布し、利用するMacだけlaunchctl enableで有効化する。
有効化状態はlaunchdのmachine-local stateであり、全マシンへ自動展開しない。

実機ではAC閉蓋時にDarkWakeへ移行しつつ監視処理が継続し、画面共有の再接続に成功した。
バッテリーではcaffeinate生存中に115秒の閉蓋Sleepが記録された。
同一プロセスのまま電源を往復するとPreventSystemSleep集計は1→0→1となり、SIGKILL後は所有assertionが消えた。
画面共有など他assertionも存在するため、電源往復の集計だけで単独効果を断定しない。

LaunchAgentの起動、SIGKILL後の自動再起動、停止・無効化・target撤去後の所有assertion消失と電源設定不変、再配備を実機確認した。
長時間のCodex処理、画面ロック、AC復帰後の閉蓋再接続、LaunchAgentのログイン時起動は未検証。
DarkWakeでの短時間試験をFullWake維持や全アプリの連続稼働保証と扱わない。
ログアウト中・ログイン前の稼働は対象外。停止時はbootoutし、恒久停止時はdisableも行う。

反復手順は[運用文書](../mac-ac-awake.md)に置く。常時ロード指示や新Skillは追加しない。
