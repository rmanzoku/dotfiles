---
title: "ADR 0069: AI CLI runner の task-data boundary を正規化する"
status: "Accepted"
date: "2026-08-26"
worked_at: "2026-08-26 00:33 JST"
agent_model: "OpenAI Codex GPT-5.6"
---

# ADR 0069: AI CLI runner の task-data boundary を正規化する

## Context

AI CLI delegation runner の正規 governance は、permission・approval・sandbox・tool policy を caller または CLI config/profile に置き、runner は observability、prompt/artifact transport、timeout、failure classification を担うとしている。一方、`copilot-cli-runner` は Fable だけに用途限定、retention の二重承認、private/confidential source の追加除外、最低200 credits を課していた。他 runner にも固定 research quota、task-scoped editing の一律禁止、画像内容ポリシーが残り、transport runner が高位 workflow の task/data policy を上書きしていた。

Anthropic の公式 data-retention documentation は Fable 5 に30日保持を要求し、ZDR の対象外としている。GitHub の Copilot policy は training opt-out を別設定として扱う。したがって、training opt-out を operational retention ゼロと解釈せず、Fable の明示選択を30日保持条件の acknowledgment として扱う。

## Decision

- AI CLI delegation runner は model-neutral な task-data boundary を使う。caller が executor/model を明示選択した場合、configured account/organization policy と caller の scope 内で task-relevant な private repository code と internal documents を渡せる。モデル固有の二重確認を要求しない。
- secret values、secret references と解決結果、credentials、private keys、authenticated-session material、unrelated personal data は委譲しない。この境界は model-neutral に維持する。
- Fable は明示選択、30日保持 notice、hard AI-credit cap、暗黙 fallback 禁止を必須とする。positive cap に provider/documented minimum がない限り、過去の代表 run を根拠に model-specific floor を強制しない。Fable の uncapped 実行は拒否する。
- research tool count/output quota、task-scoped editing、image content policy は caller/workflow または専用 artifact skill の責務とし、delegation runner は一律制約を追加しない。
- Agy/Grok の headless permission flags、Agy の argv-size limit、cwd/path/expected-artifact contract、timeout、failure evidence、account/profile boundary、silent fallback 禁止は CLI mechanics または既存 equivalence guard に根拠があるため維持する。
- `instruction-gc` に runner guard boundary check を追加し、同じ provider/model-specific overguard の再導入を fail にする。Copilot wrapper の budget preflight は no-API regression test で固定する。

## Authoritative Sources

- Anthropic, API and data retention: <https://platform.claude.com/docs/en/manage-claude/api-and-data-retention>
- Anthropic, Introducing Claude Fable 5 and Claude Mythos 5: <https://platform.claude.com/docs/en/about-claude/models/introducing-claude-fable-5-and-claude-mythos-5>
- GitHub, Managing GitHub Copilot policies as an individual subscriber: <https://docs.github.com/en/copilot/how-tos/manage-your-account/manage-policies>
- Repository runner governance: `docs/runner-skill-governance.md` §AI CLI Delegation Defaults

## Consequences

- 明示的に選んだ CLI/model は、オーケストレーターと同じ task-relevant repository/internal-document context を利用できる。
- retention notice は残るが、同じ入力への二重承認にはならない。
- 小さい positive cap の read-only Fable task を wrapper が一律拒否しなくなる。cap不足による実行失敗は observable artifact として扱い、代表値は advisory に留める。
- secret/session boundary、課金制御、外部副作用境界、artifact recovery は弱まらない。

## Validation

- `scripts/skill-quick-validate` を変更した全 first-party skill に実行する。
- `python3 skills/copilot-cli-runner/scripts/test_run_copilot_cli.py` で low positive cap が preflight を通り、uncapped Fable が拒否されることを確認する。
- `scripts/instruction-gc --no-doctor` で runner guard boundary check を確認する。
- blank-slate behavior probe で explicit Fable private-repository task、small-cap Fable task、delegated editing/research hold-out の critical requirements を確認する。
