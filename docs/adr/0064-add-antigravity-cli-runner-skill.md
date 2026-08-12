---
title: "ADR 0064: Antigravity CLI (agy) の runner skill を追加する"
status: "Accepted"
date: "2026-08-09"
worked_at: "2026-08-09 JST"
agent_model: "Claude Opus 5"
---

# ADR 0064: Antigravity CLI (agy) の runner skill を追加する

## Context

ADR 0052（2026-07-08）で個人向け Gemini CLI から Antigravity CLI（`agy`）へ移行したが、runner skill の作成は「`agy -p` の非対話実行、構造化出力、権限モデル、既存 Gemini runner との成功判定契約が一致しない」ことを理由に保留し、別 ADR と検証で扱うとした。本 ADR がその follow-up である。

その後 `gemini-cli-runner` は d0f35dd（2026-08-04「Retire gemini and qwen toolchains」）で削除済みであり、ADR 0052 の「`gemini-cli-runner` は残す」という決定は既に有効ではない。結果として Gemini 系モデルへの実行経路は存在しない状態になっていた。

この空白は実害を出している。workspace の GEO 定点観測 2026-08-08 run で gemini エンジンが blocked となり、成立エンジンが 4/4 → 3/4 に落ちた。前回の唯一の誤事実源が gemini だったため「誤事実 0」KPI と「gemini の被引用」KPI の 2 つが連続 2 run 要件を確認できず判定保留に落ちている。

`agy` 1.1.10 の print モードを実測して確認した仕様:

- モデル ID に `auto` は存在しない（`gemini-3.6-flash-{high,medium,low}` / `gemini-3.5-flash-{high,medium,low}` / `gemini-3.1-pro-{high,low}` ほか）。不正な ID は exit 1 + `{"status":"ERROR","error":"invalid model selection …"}`。
- `--output-format json` は `status` / `response` / `usage` / `conversation_id` を返す。成功時 `status: SUCCESS`。
- プロンプトは **argv 値でしか渡せない**。`agy -p --model … "…"` は `--model` をプロンプト値として飲み込む。stdin に流すと `status: SUCCESS` かつ応答が空になる（stdin は context として読まれない）。
- Web 検索などのツール利用には `--dangerously-skip-permissions` が要る。無いと exit 0・空応答という判別しにくい失敗になる。

## Decision

- `skills/agy-cli-runner` を新設し、provider `gemini` の runner とする。既存 runner（grok / codex / claude / copilot / gws / op）と同じ artifact 契約に揃える: prompt file を正本とし、`run.prompt.md` / 応答 artifact / `run.err` / `summary.json` / `failure.md` を `.context/<task>/` に残す。
- **プロンプトはファイルを正本とし、実行時のみ argv へ渡す**。共通ルールの「`-p` などの引数へのインライン展開を避ける」は監査可能性と quoting 破損の回避が目的であり、`agy` にファイル／stdin 入力が無い以上、監査可能性は prompt file + `run.prompt.md` で担保し、quoting は単一 argv 要素での受け渡しで担保する。取りこぼしを黙って起こさないため 128 KiB の上限検査を置き、超過は `invalid_prompt` として明示的に失敗させる。
- `--model` を必須引数にする。`auto` が無いため、省略時の暗黙既定を持たせると invalid model で落ちる経路を作るだけになる。
- `--print-timeout` は `--timeout-seconds` から導出し、必ず wrapper の kill より先に発火させる（60 秒超は 30 秒マージン、以下は 10%）。agy 側が先に諦めれば構造化エラーが残り、wrapper の kill が先に出ると原因が読めない signal 死になる。
- ツール利用を伴うロールでは `--skip-permissions` を明示的に渡す。既定 ON にはしない。
- fallback backend は追加しない。`agy` の不在・認証失敗・モデル拒否は artifact から報告する。
- ADR 0052 の「`gemini-cli-runner` は残す」「Antigravity CLI の runner skill は今回作らない」は本 ADR で置き換える。enterprise / API key 環境向けの Gemini CLI 経路は、必要になった時点で別 skill として再設計する。

## Consequences

- provider `gemini` の実行経路が復旧し、GEO 定点観測の 4 エンジン測定に戻せる。KPI の連続要件も再び確定可能になる。
- workspace の `rules/model_registry.yaml` は `providers.gemini.runner` を `agy-cli-runner` に、`models.gemini_researcher.model_id` を `auto` から固定 ID に変更する必要がある（workspace 側 ADR 2026-08-09 参照）。
- `models.<alias>.config.env`（`TERM` / `NO_COLOR`）は Gemini CLI のターミナル描画対策であり、`agy --output-format json` では不要になるため廃止する。
- プロンプトサイズが 128 KiB を超える委譲はこの経路では実行できない。分割するか別 provider を選ぶ判断が呼び出し側に要る。

## Validation

```bash
scripts/skill-quick-validate skills/agy-cli-runner
python3 skills/agy-cli-runner/scripts/run_agy_cli.py --help
```

実測した runtime 検証（2026-08-09、agy 1.1.10）:

| ケース | 期待 | 結果 |
|---|---|---|
| `--dry-run` | exit 0、backend 呼び出しなし、`dry_run_payload` 記録 | OK |
| prompt file 不在 | `invalid_prompt` + `failure.md` | OK |
| 不正 `--model` | exit 1、`nonzero_exit,agy_error` | OK |
| Web 検索付き実行（`--skip-permissions`） | exit 0、`status: SUCCESS`、応答非空 | OK（`usage.total_tokens` 記録あり） |
| 強制 timeout（`--timeout-seconds 20`） | exit 124、`timeout` 分類 | OK（`--print-timeout 18s` を導出） |
