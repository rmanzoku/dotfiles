---
title: "ADR 0076: AI CLI runner と role 割当を GPT-6 / Opus 5.5 世代へ移す"
status: accepted
date: 2026-10-03
worked_at: 2026-10-03 10:39 JST
agent_model: Claude Opus 5.5 (claude-opus-5-5)
---

# ADR 0076: AI CLI runner と role 割当を GPT-6 / Opus 5.5 世代へ移す

> [ADR 0054](./0054-allocate-codex-56-and-copilot-review-models-by-role.md) の Codex 5.6 role 割当と Copilot 既定モデルを本 ADR で置き換える。Fable の明示選択・hard cap・暗黙 fallback 禁止、role で委譲する方針は ADR 0054 / 0069 のまま維持する。

## Context

- Codex は ChatGPT.app 同梱の app-managed CLI になり、binary が `Contents/Resources/codex-cli/bin/codex` へ移った。`dot_zprofile` は `Contents/Resources` を PATH に入れていたため、`codex` が PATH 上で解決できず、codex-cli-runner の既定 `--codex-bin codex` が使えなかった。
- Codex の model catalog は GPT-6 世代（`gpt-6.1-sol`、`gpt-6-astra`、`gpt-6-sol`、`gpt-6-luna`）になった。GPT-6 には Terra 相当の中位モデルがない。実機の既定は `gpt-6.1-sol` / `medium` だったが、source は `gpt-6-astra` / `xhigh` のままで drift していた。
- codex-cli-runner の prompt adapter は GPT-5.5 と GPT-5.6 にしか対応しておらず、GPT-6 では adapter が付かなかった。
- Copilot CLI は `claude-opus-5.5` を選べるのに、既定は `claude-opus-4.8` のままだった。
- claude-cli-runner は Opus 5 adapter しか持たず、copilot-cli-runner にある Fable 5 adapter が無かった。

## Decision

- `dot_zprofile` の PATH を `ChatGPT.app/Contents/Resources/codex-cli/bin` に直す。旧 PATH が公開していた `rg` は Homebrew 版で代替できる。
- Codex parent の既定は実機に合わせ `gpt-6.1-sol` / `medium` とする。
- Codex の role 割当（effort は ADR 0054 から変えない）:
  - `tech` / `biz`: `gpt-6-astra` / `high`（高リスク判断に最上位モデルを使う）
  - `cleaner`: `gpt-6.1-sol` / `medium`
  - `worker` / `personal`: `gpt-6.1-sol` / `medium`（Terra の後継がないため）
  - `mechanical` と daily-ai-brew-upgrade automation: `gpt-6-luna` / `low`
- Copilot CLI の既定を `claude-opus-5.5` / `high` にする。
- codex-cli-runner に `gpt-6` と `gpt-6-luna` の prompt profile を追加する。`--model` が GPT-6 と判定できるときは `auto` で選ばれる。adapter は OpenAI の公式ガイダンスにある GPT-6 の傾向だけを補正する。対象は、確認を求めすぎる、skill / AGENTS.md の指示で止まる、最初の実装で止まる、テストをやりすぎる、の 4 点。Codex 組み込みの GPT-6 指示と重複する内容は入れない。Luna の組み込み指示は「依頼がなければテストしない」なので、`gpt-6-luna` には success criteria の検証を実行する 1 行を加える。
- GPT-5.6 adapter にある「think hard で effort を模さない」「最終出力を簡潔に」の 2 行は、GPT-6 の公式資料に根拠がないため GPT-6 adapter に入れない。
- claude-cli-runner に copilot-cli-runner と同じ文面の `fable-5` profile を追加する。

## Sources

- https://developers.openai.com/api/docs/guides/latest-model
- https://developers.openai.com/api/docs/guides/prompt-guidance
- https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra
- https://developers.openai.com/codex/models
- `~/.codex/models_cache.json` の gpt-6 系 entry（model description と組み込み指示）

GPT-6 の公式ガイダンスは主に Astra 向けで、6.1-sol / 6-sol / luna 個別の prompting guidance は見つからなかった。6.1-sol は組み込み指示が Astra とほぼ同じなので、同じ adapter を使う。

## Consequences

- 既定の `codex` コマンドで codex-cli-runner が使える。
- `tech` / `biz` は Astra を使うため、ADR 0054 の Sol/high よりコストが上がる。
- `tech` / `biz` / `personal` の agent file は git 管理外で 1Password に保存されている。他マシンへ反映するには `opmaterialize add` で manifest を更新する必要がある。
- GPT-6 の prompting doctrine は `gpt-6-tuning` skill に置く。GPT-6.1 専用の prompting guidance は公式に存在せず、6.1-sol 固有なのは effort 範囲と Responses API 必須というパラメータ面だけなので、同じ skill で扱う。
- `codex exec` の persistent mode と `ultra` effort が非対話実行でどう振る舞うかは未確認。短い smoke run（`gpt-6-luna` / `low`）は通常どおり終了した。

## Validation

- `python3 -m py_compile` と `scripts/skill-quick-validate` で claude / codex / agy runner を確認する。
- モデル名ごとに `resolve_prompt_profile` の結果を確認する（`gpt-6.1-sol`→`gpt-6`、`gpt-6-luna`→`gpt-6-luna`、`gpt-5.6-luna`→`gpt-5-6`、`claude-fable-5-1`→`fable-5`、bare alias→`none`）。
- 新しい PATH で `codex` が解決できること、codex-cli-runner で実際に 1 回実行できることを確認する。
- `scripts/chezmoi-drift --check-ignore` と `chezmoi diff` を確認する。

## Addendum: runner review and legacy removal (2026-10-03)

Three reviews of the CLI runners (opus-5-tuning, gpt-6-tuning, cleaner) were folded in. Proposals are in `.context/runner-review/`, which is not tracked.

- Adopted:
  - Claude and Codex Caller Checklists now say how to pick the prompt profile when `--model` is omitted, so the default path gets an adapter.
  - Checklists in five runners use defaults first and ask only when an item has no default and cannot be inferred.
  - Runtime validation runs only the checks the change touches.
  - The Opus 5 adapters in claude and copilot now carry the same contract: no verification subagents, parallelism within source-prompt limits, artifact length within source-prompt limits.
  - GPT-6 adapter: skip tests for low-impact edits; mark items blocked only when the context cannot settle them.
  - Fixed dead references: `--ask-for-approval`, the `research` skill, the grok `--session-id` meaning, agy `--sandbox`/`--add-dir`, the op auth stop rule, and the hard-coded op paths.
  - Removed duplicates and rules restated from governance.
  - Removed the pinned `grok-4.5` example.
- Removed legacy models: the codex-cli-runner GPT-5.5 / GPT-5.6 profiles and the `gpt-5-6-tuning` skill are retired. Older Codex models now get no adapter. Claude runners already cover only Opus 5.x and Fable 5.x.
- Not adopted:
  - GPT-6 adapter trims that overlap Codex built-in instructions (M1/M2): these need an A/B run first.
  - Description rewrites for claude / gws / agy: these need firing probes.
  - The gws `.env` ask rule: it is a credential gate and stays conservative.
  - The shared "Keep it concise" response format: instruction-gc check 9 requires it to stay verbatim.
  - Refusal classification text: the stream format is unverified.
  - The grok 0.2.112 `--always-approve` observation: re-checking it needs a real call, and the current behavior is harmless.
  - The agy stdin stream-json transport: it needs a probe.
  - Moving op AWS / Vultr steps out of the skill: deferred to an owner decision.

## Addendum: codex on PATH (2026-10-04)

The `dot_zprofile` PATH entry only reaches login shells. Agents and automations started from desktop apps kept an older PATH and could not find `codex`. The fix replaces that entry with a chezmoi-managed symlink, `~/.local/bin/codex`, pointing at the ChatGPT.app bundle. `~/.local/bin` is on PATH in every observed context, and the bundled launcher resolves symlinks to find its own files. codex-cli-runner now documents the bundle path for hosts where `codex` is not on PATH.
