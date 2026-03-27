---
title: "ADR 0009: SSH config は managed 本体と local include に分離する"
status: Accepted
date: 2026-03-24
worked_at: 2026-03-24 16:30 JST
agent_model: GPT-5 Codex
---

# ADR 0009: SSH config は managed 本体と local include に分離する

## Context

このリポジトリでは `chezmoi` で dotfiles を管理しているが、案件固有の接続先名、顧客名、専用鍵パスや、自宅 LAN 内ホストのようなマシン依存情報まで source state に含めると、リポジトリ自体に不要なローカル情報が残る。

一方で、`~/.ssh/config` のベース構成自体は継続的に再利用したいため、完全に unmanaged に戻すより、共通部分だけを `chezmoi` 管理し、個別案件向けの `Host` 定義だけをローカルに切り出す方が運用しやすい。

## Decision

- `~/.ssh/config` は `chezmoi` 管理対象に追加する。
- managed 側には共通エントリと `Include ~/.ssh/config.local` だけを置き、案件固有の `Host`、マシン固有の `Host`、`IdentityFile`、接続先別コメントは `~/.ssh/config.local` に置く。
- GitHub の複数アカウント運用は、`HostName github.com` を共有しつつ `Host github-<alias>` のような別名をローカル定義して切り替える。
- 案件固有の alias 名、顧客名、鍵ファイル名は managed repo に保存しない。

## Consequences

- 共通 SSH 設定は `chezmoi` で再現でき、案件固有情報やマシン固有情報はローカルに閉じ込められる。
- GitHub Enterprise Cloud のようにホスト名が `github.com` のままでも、SSH alias によりアカウントと鍵を分離できる。
- 新しい案件向けには `~/.ssh/config.local` と対応する鍵をローカルで用意する手順が必要になる。
