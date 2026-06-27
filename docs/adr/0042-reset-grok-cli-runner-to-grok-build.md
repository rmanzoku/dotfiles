---
title: "ADR 0042: grok-cli-runner を Grok Build CLI runner として再設計する"
status: accepted
date: 2026-06-27
worked_at: 2026-06-27 23:01 JST
agent_model: GPT-5 Codex
---

# ADR 0042: grok-cli-runner を Grok Build CLI runner として再設計する

## Context

`grok-cli-runner` は Hermes Agent `xai-oauth` と direct `x_search_tool` を主経路にしていた。
しかし Hermes / `x-raw` 経路の安定性に疑義があり、ユーザーから 0 ベースで Grok Build CLI runner として再実装してよいという指示があった。

2026-06-27 時点の xAI 公式 docs では、Grok Build は headless automation 向けに `grok -p`、`--output-format json` / `streaming-json`、`--no-auto-update`、`--cwd`、`--permission-mode`、`grok login --device-auth`、`XAI_API_KEY` を案内している。

## Decision

- `grok-cli-runner` の主経路を公式 Grok Build CLI headless mode に変更する。
- wrapper は `grok --no-auto-update -p <prompt> --output-format json --cwd <path> -m <model> --permission-mode auto --no-plan --verbatim` を基本形にする。
- Hermes backend、direct Hermes `x_search_tool`、`x-raw` retrieval mode、`x-search-results.json` 契約は削除する。
- `grok-request.json`、`grok-response.json`、`summary.json`、`run.err`、`failure.md` の file-based runner 契約は維持する。
- 既定モデルは Grok Build CLI の config alias と整合する `grok-build` とし、API model id の `grok-build-0.1` が必要な場合は request / `--model` / env で明示する。
- fallback backend は追加しない。Grok Build CLI が未導入、未認証、または permission / model / rate-limit で失敗した場合は runner artifact に失敗を記録する。
- plan mode が tool 実行を阻害する場合があるため、`--permission-mode auto --no-plan` を既定にする。plan mode が必要な場合だけ `--plan` で戻す。
- wrapper は request 由来 prompt を `--verbatim` で渡し、Grok Build が runner 自体や repository wrapper をタスクとして誤解しにくい形にする。

## Consequences

- X URL raw evidence 専用の `x-search-results.json` は生成されなくなる。
- X / web / repo tool 利用は Grok Build CLI 自体の tool 能力と permission mode に委ねる。
- CI や automation では `--dry-run` で request/command shape を確認し、実行環境には `grok` CLI と auth state または `XAI_API_KEY` が必要になる。
- 旧 Hermes 経路が必要になった場合は、この runner に暗黙 fallback として戻さず、別 runner として再評価する。

## Validation

- `python3 -m py_compile skills/grok-cli-runner/scripts/run_grok_cli.py`
- `python3 skills/grok-cli-runner/scripts/run_grok_cli.py --help`
- `scripts/skill-quick-validate skills/grok-cli-runner`
- valid request の `--dry-run`
- invalid request の failure artifact 生成
- `grok` CLI 導入済み環境での実 smoke
- public X post retrieval smoke with `--permission-mode auto --no-plan`
