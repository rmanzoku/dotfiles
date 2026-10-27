---
title: "ADR 0080: Codex runner の既定を goal 付き app-server にする"
status: accepted
date: 2026-10-27
worked_at: 2026-10-27 JST
agent_model: "GPT-6 / Claude Opus 5.5 (claude-opus-5-5, rename)"
---

# Context

`gpt-6.1-terra` に大きめの実装を `codex exec` で依頼した実験では、35〜42 秒で調査のみを行い、理由なく未完了として終了する事象を 2 回観測した。`/goal` を exec の prompt に書いても goal は作られず、実験時の `goals_1.sqlite` にも記録されなかった。一方、app-server の `thread/goal/set` で goal を設定した小さな作業は 5.6 秒で complete に到達した。これは依頼元が提示した実測であり、すべての大規模作業の完遂を保証するものではない。

既存 wrapper の prompt adapter だけでは thread の goal lifecycle を開始できない。docs や指示の追加ではこの差を埋められないため、新しい Skill を増やさず、既存 runner に JSON-RPC adapter を追加する。

# Decision

- 既定は runner が専有する stdio `codex app-server --stdio` とする。initialize、thread/start、thread/goal/set、turn/start の順に実行し、turn 完了だけでなく goal の terminal status を待つ。既定 objective は最初の message の依頼と Success criteria の完了、Stop only if に該当したときだけ blocked とする趣旨。明示 objective／ファイルと `--no-goal` を用意する。
- 既存 daemon の Unix WebSocket 接続は `--app-server-daemon` の明示 option とする。daemon は Desktop と作業を共有し、更新によって実行中の作業が中断され得る。専有 stdio を既定とすることでその lifecycle から実行を分離する。runner は daemon を起動・停止しない。
- `--transport exec` を明示選択として残す。名前付き profile と CLI 固有引数が必要な caller の経路を維持するためであり、app-server の失敗時に自動切替しない。exec は goal を設定しない。
- `--profile` は exec 専用とする。stdio・daemon では Codex の起動前（version probe を含む）に明示エラーとし、非ゼロ exit と `summary.json.failure_reasons` に記録する。黙って無視したり profile 内容を独自に merge したりしない。確認した CLI の app-server と protocol に名前付き profile の選択手段はなかった。依頼元の caller 調査では利用箇所・ローカル profile 定義とも見つからず、2026-10-27 に利用者がこの制約を承認した。
- sandbox・approval は config に任せる。server request は記録して拒否する。timeout は interrupt を送信し、goal 停止、server 終了、RPC／client 異常とは分けて記録する。
- binary の既定値・選択順は変えない。従来の `--codex-bin` と PATH から選んだ実行ファイルを使い、解決した path とその `--version` を summary に保存する。probe は 5 秒で制限し、取得失敗は明示的な nonfatal 理由に残す。daemon 接続時のこの情報はローカル CLI のものであり、daemon の版を示さない。
- 既定経路が `codex exec` ではなくなったため、skill 名を `codex-cli-runner` から `codex-runner`、wrapper を `run_codex.py` に改名する（2026-10-27 利用者承認、Claude Opus 5.5 が実施）。GPT 系の名前にしないのは、他の runner と同じく実行する harness 名で命名し、Codex 上で動かすモデルが変わっても名前を保つため。旧名の互換 alias は作らず、両 agent の install も新名へ置き換える。

# Evidence

- 最初の実装で `gpt-6.1-sol`・`gpt-6.1-terra` × stdio・既存 daemon の 4 smoke がすべて goal complete となり、作成した 2 ファイルの内容を確認した。所要時間は約 10〜18 秒。証跡は作業 worktree の `.context/app-server-validation/smoke-results.json`。
- 実験環境には app 同梱の `~/.local/bin/codex`（0.164.0-alpha.11.1）と Homebrew の `/opt/homebrew/bin/codex`（0.163.0）があり、前回実行では PATH が後者を選んだ。固定パスの新しい既定を設けず、実際の選択を観測可能にする。
- [公式 app-server protocol](https://learn.chatgpt.com/docs/app-server) と、ローカル CLI から生成した schema・起動時エラーを参照した。Unix socket 上の WebSocket と daemon の共有状態は依頼元の実機実験に基づく。

# Consequences

caller は profile／extra CLI args を使う場合に exec を明示する必要がある。app-server の events は送受信方向付きの JSON-RPC 記録となり、exec の stdout event format とは異なる。共通の prompt、last-message、summary、failure と expected artifact 検査は維持する。goal complete は runner の完了条件であり、成果物の品質は引き続き caller が検証する。

# Validation

no-API fake server で成功、複数 turn、goal の停止状態、timeout と interrupt、server 終了、approval 拒否、protocol 異常、no-goal、artifact 欠落、caller stdin、profile の起動前拒否、binary 情報、exec profile、WebSocket を検査する。完成版で sol・terra × stdio・daemon の 4 smoke と exec 1 回を実行し、ファイル内容・summary を確認する。`scripts/skill-quick-validate skills/codex-runner` と差分検査を行い、通常の pre-commit hook を通して commit する。
