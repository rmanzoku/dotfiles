---
title: "ADR 0053: grok-cli-runner のデフォルトモデルを Grok Build CLI 側デフォルトへ委譲する"
status: accepted
date: 2026-07-13
worked_at: 2026-07-13 23:29 JST
agent_model: Claude Fable 5 (claude-fable-5)
---

# ADR 0053: grok-cli-runner のデフォルトモデルを Grok Build CLI 側デフォルトへ委譲する

## Context

ADR 0049 で `grok-cli-runner` の既定モデルを `grok-build` に設定したが、2026-07-13 に Grok Build CLI 0.2.99 が `grok-build` を unknown model として拒否することを確認した。`grok models` の実測では Default model は `grok-4.5`、利用可能モデルは `grok-4.5` と `grok-composer-2.5-fast` のみだった。

既定モデルのハードコードは ADR 0030（`grok-4-3` へ更新）、ADR 0049（`grok-build` へリセット）に続き 3 回目の破損であり、xAI 側のモデル改名のたびに runner が壊れる構造になっていた。

## Decision

- wrapper のハードコード既定 `DEFAULT_MODEL = "grok-build"` を削除する。
- モデル解決は `--model` → `request.model` → `GROK_BUILD_MODEL` → `GROK_MODEL` の順で行い、いずれも未設定の場合は `-m` を渡さず Grok Build CLI 自身のデフォルトモデルに委ねる。
- これは暗黙 fallback ではなくデフォルト決定の委譲として扱う。`-m` 非付与は `summary.json.command` で観測でき、実行経路は変わらない。
- モデルを固定したい場合は従来どおり `--model` / `request.model` / env で明示し、有効なモデル id は `grok models` で確認する。
- 委譲時の artifact 上の `model` は `null` とし、実際に使われたモデルの特定が必要な場合は Grok Build CLI の出力（`response.parsed_stdout`）を参照する。

## Consequences

- xAI がモデル名を改名・入替しても、モデル未指定の運用（workspace の model registry が前提とする default resolution を含む）は壊れなくなる。
- `summary.json.model` と `grok-response.json.model` は委譲時に `null` になるため、モデル名の確定記録が必要な orchestrator は明示指定するか CLI 出力から読み取る。
- `references/schema.md` の request 例のモデル id は現行 CLI で有効な値に更新したが、例示のピン留め値は今後も陳腐化しうる。ピン留め前に `grok models` を確認する運用を schema notes に明記した。

## Validation

- `python3 -m py_compile skills/grok-cli-runner/scripts/run_grok_cli.py`
- `python3 skills/grok-cli-runner/scripts/run_grok_cli.py --help`
- `scripts/skill-quick-validate skills/grok-cli-runner`
- モデル未指定 request の `--dry-run` で command に `-m` が含まれないこと
- `request.model` 指定 / `GROK_BUILD_MODEL` 指定の `--dry-run` で `-m <model>` が付与されること
- `grok` CLI 導入済み環境でのモデル未指定の実 smoke
