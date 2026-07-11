---
title: "ADR 0052: 個人向け Gemini CLI を Antigravity CLI へ移行する"
status: "Accepted"
date: "2026-07-08"
worked_at: "2026-07-08 12:56 JST"
agent_model: "GPT-5 Codex"
---

# ADR 0052: 個人向け Gemini CLI を Antigravity CLI へ移行する

## Context

Google は 2026-06-18 以降、Gemini Code Assist for individuals、Google AI Pro、Google AI Ultra、無料枠の Google ログインによる Gemini CLI / Gemini Code Assist IDE extension のリクエスト提供を停止した。
この環境でも `gemini` の認証時に "This client is no longer supported" と表示され、個人向け OAuth の継続利用はできない状態になった。

一方、Gemini Code Assist Standard / Enterprise や paid Gemini / Gemini Enterprise Agent Platform API key による Gemini CLI 利用は別契約として残るため、Gemini CLI 関連の runner を即時削除すると enterprise / API key 用途まで壊す可能性がある。

## Decision

- Homebrew の管理対象を `gemini-cli` formula から `antigravity-cli` cask へ切り替える。
- CLI の日次更新 automation は `gemini-cli` ではなく `antigravity-cli`（binary: `agy`）を対象にする。
- `gemini-cli-runner` は残すが、個人向け OAuth / Google ログインでは使わないことを skill の発火説明と手順に明記する。
- `gemini-cli-runner` は、"client is no longer supported" や Antigravity への migration 指示を fatal error として分類する。
- Antigravity CLI の runner skill は今回作らない。`agy -p` の非対話実行、構造化出力、権限モデル、既存 Gemini runner との成功判定契約が一致しないため、別 ADR と検証で扱う。

## Consequences

- 新しい環境では Homebrew から `agy` を導入できる。
- 個人向け認証で壊れる `gemini-cli` を自動更新対象から外せる。
- Gemini CLI がまだ有効な enterprise / API key 環境向けの runner skill は温存される。
- Codex / Claude から Gemini 系 runner を使う場合、個人向けアカウントでは明示的に Antigravity 移行が必要だと判断できる。
- Antigravity CLI の自動 runner 化は、権限と出力契約を確認するまで保留される。
