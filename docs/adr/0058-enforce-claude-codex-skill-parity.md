---
title: "ADR 0058: manifest 管理 Skill を Claude Code と Codex で同一化する"
status: accepted
date: 2026-07-26
worked_at: 2026-07-26 16:30 JST
agent_model: OpenAI GPT-5 (Codex)
---

# ADR 0058: manifest 管理 Skill を Claude Code と Codex で同一化する

## Context

`docs/skills-install-manifest.md` の first-party publisher skills は Claude Code 24件、Codex 23件で一致していなかった。
そのため repository を pull して chezmoi を apply しても、`skills/` の更新は各 host の user-level install へ反映されず、古い runner や evaluator が残った。
agent ごとの差異を許容する従来方針では、この状態を drift として検出できなかった。

## Decision

- `docs/skills-install-manifest.md` で管理する repo オリジナル skill と external skill は、Claude Code と Codex に同じ skill セット・同じ ref / version で配備する。
- first-party publisher skills は `skills/` 配下の25件を両 host に配備する。host 名を含む runner も相互運用・委譲用途があるため parity 対象に含める。
- Codex `.system` skill、Claude / Codex の plugin 同梱 skill、各 host の組み込み skill は、repository が lifecycle を管理できないため parity 対象外とする。
- manifest 管理 skill の片側配備を例外とする場合は、理由と期限を manifest または ADR に明記する。
- skill-manager は repository policy を先に解決し、parity 必須 repository では skill 名だけでなく version / ref の差も drift として扱う。

## Consequences

- Claude Code と Codex のどちらから作業を開始しても、repository 管理 Skill の利用可能性と内容が一致する。
- Skill 更新時は両 host への再配備と parity 検証が必要になる。
- system / plugin / host 組み込み Skill の差は残るが、repository 管理対象との境界が明確になる。

## Validation

- Claude Code / Codex の first-party install command から agent flag を除いた skill 名一覧が一致すること。
- `scripts/skill-quick-validate skills/skill-manager` が成功すること。
- 再配備後、両 host の user-level skill 名一覧と publisher payload が一致すること。
