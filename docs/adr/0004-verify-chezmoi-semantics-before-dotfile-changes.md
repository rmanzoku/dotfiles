# ADR 0004: dotfile 変更前に chezmoi の source / target semantics を確認する

- Status: Accepted
- Date: 2026-03-12
- Worked At: 2026-03-12 18:10 JST
- Agent Model: GPT-5 Codex

## Context

このリポジトリでは dotfile 更新時に `dotfile-update` スキルを使う運用だが、chezmoi の source state と target state の理解が浅いまま変更すると、
意図しない ignore、誤ったファイル対応表、権限属性の誤解といった問題が起きる。

実際に、`.chezmoiignore` を source path 感覚で変更しそうになったこと、`private_` を名前変換として説明してしまったことから、
chezmoi の公式仕様に基づく恒久ドキュメントと手順の明文化が必要になった。

## Decision

- chezmoi の基本概念、`dot_` / `private_`、hidden source directory の扱い、`.chezmoiignore` の評価基準を `docs/chezmoi-reference.md` にまとめる。
- `dotfile-update` では、変更前に source と target のどちらを触っているかを明確にし、必要に応じて `chezmoi target-path` / `chezmoi source-path` で確認する。
- `.chezmoiignore` は target path に対するルールとして扱い、source path ベースの推測で変更しない。
- repo ローカルファイルと chezmoi 管理対象を混同しないよう、README と AGENTS から参照できるようにする。

## Consequences

- dotfile 更新時の判断基準が明確になり、誤った配備や ignore 変更を避けやすくなる。
- `dotfile-update` の説明が chezmoi の公式仕様と一致しやすくなる。
- 新しいセッションでも、まず `docs/chezmoi-reference.md` を見れば前提を再確認できる。
