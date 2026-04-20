---
title: "ADR 0025: skill 一覧は source-aware identity で集約する"
status: accepted
date: 2026-04-20
worked_at: 2026-04-20 09:26 JST
agent_model: GPT-5 Codex
---

# ADR 0025: skill 一覧は source-aware identity で集約する

## Context

Claude Code と Codex の両方で、session に渡される skill catalog には複数ソースの skill が混在する。
少なくとも次の source が存在する。

- user / global skill
- project skill
- plugin / marketplace skill
- Codex `.system` skill

Claude Code では plugin skill が namespaced に見えるケースがある一方、
context usage や一部ログでは bare name に見えることもある。
Codex 側の session log でも、同名 skill が複数回 `Available skills` に含まれる記録がある。

この状況で bare skill name だけを key にして一覧を平坦化すると、
実在する複数 entry の区別が消え、collision の見落としや誤った優先判定につながる。

## Decision

- `skill-manager` の skill inventory は source-aware identity で集約する。
- inventory の単位は bare skill name ではなく、少なくとも source type と source identity を含む。
- plugin / marketplace skill は、host が namespace を提供する場合はその namespace を保持する。
- 同じ bare skill name が複数 source に存在する場合、黙って 1 つに畳み込まず collision として扱う。
- 自動優先を持つのは Codex `.system` collision のみとし、それ以外は source を見える形で併記する。

## Consequences

- plugin skill と user/project skill の重名を見落としにくくなる。
- host ごとの見え方が違っても、`skill-manager` 側では provenance を保った inventory を返せる。
- inventory 出力は `bare_name`、`display_name`、`source_type`、`source_id`、`identity`、`collisions` などの source-aware field を前提に扱う。
- 将来 `plugin-collision` や `source-preferred` 系の診断を追加しやすくなる。
- 単純な `name -> one entry` のデータモデルは使えなくなるため、一覧・doctor・表示側は source-aware な key で扱う必要がある。
