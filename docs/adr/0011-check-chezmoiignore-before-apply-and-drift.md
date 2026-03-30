---
title: "ADR 0011: chezmoi apply と drift 確認前に .chezmoiignore 整合を検査する"
---

# ADR 0011: chezmoi apply と drift 確認前に `.chezmoiignore` 整合を検査する

- Status: Accepted
- Date: 2026-03-30
- Worked At: 2026-03-30 23:00 JST
- Agent Model: GPT-5 Codex

## Context

このリポジトリでは dotfile の更新後に `chezmoi apply` と `scripts/chezmoi-drift` を使って実ファイル反映とドリフト確認を行っている。
一方で、source file 自体は存在していても target path が `.chezmoiignore` に入っていると、`chezmoi apply` ではその target が配備されず、意図した変更が実ファイルへ反映されない。

今回も `dot_zshenv` を追加した時点で `.chezmoiignore` に `.zshenv` が残っていたため、`chezmoi apply` 後も `~/.zshenv` は unmanaged のままで、変更が効いていないことにすぐ気づけなかった。
通常の `chezmoi diff` だけでは、この「source はあるが ignore により無効化されている」状態を見落としやすい。

## Decision

- `scripts/chezmoi-drift` に `--check-ignore` オプションを追加し、`chezmoi ignored --source-path` を使って source state と `.chezmoiignore` の不整合を検査する。
- allowlist に含まれない ignored source を検出した場合は、source path と target path を表示してエラーにする。
- `scripts/chezmoi-drift` の通常実行でも ignore 不整合を表示対象に含める。
- `scripts/chezmoi-drift --apply` と `--restore` は ignore 不整合がある場合は処理を中断する。
- `setup.sh` と pre-commit hook でも同じ ignore 検査を実行し、ドリフト確認やコミット前に不整合を早期に検出する。
- 運用ルールとして、`chezmoi apply` の前とドリフト確認時には必ず ignore 整合確認を行う。

## Consequences

- source file を追加・更新しても `.chezmoiignore` により実ファイルへ出ていないケースを、`apply` 前後で検出できる。
- `chezmoi diff` が空でも「managed のつもりが unmanaged のまま」という状態を見落としにくくなる。
- repo-only の intentionally ignored files は allowlist で維持し、それ以外の ignored source は明示的に判断を要求する運用になる。
