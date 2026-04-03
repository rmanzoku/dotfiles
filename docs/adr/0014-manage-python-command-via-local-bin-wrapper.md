---
title: "ADR 0014: python コマンドは ~/.local/bin の wrapper で python3 へ寄せる"
status: accepted
date: 2026-04-03
worked_at: 2026-04-03 11:25 JST
agent_model: GPT-5 Codex
---

# ADR 0014: python コマンドは ~/.local/bin の wrapper で python3 へ寄せる

## Context

この環境では `python3` は `/usr/bin/python3` にあるが、`python` は存在しない。
そのため、skill の検証や補助スクリプト実行時に `python` 前提のコマンドが失敗しやすい。

一方で、システムディレクトリ配下へ直接 symlink を置くのは管理責務が曖昧になりやすい。
この dotfiles リポジトリでは `~/.local/bin` が PATH の先頭側に入っており、ユーザー管理の軽量 shim を置く場所として既に使っている。

当初は `~/.local/bin/python -> /usr/bin/python3` の symlink を想定したが、
macOS では `/usr/bin/python3` が xcrun 経由の shim として振る舞い、`python` という argv0 で呼ばれると
`Failed to locate 'python'` になった。

## Decision

- `~/.local/bin/python` を `python3` への互換コマンドとして管理する。
- 実体は symlink ではなく shell wrapper とし、`exec /usr/bin/python3 "$@"` を実行する。
- source state では `dot_local/bin/executable_python` を使って executable file として管理する。
- これにより argv0 に依存せず、`python` でも確実に `python3` を起動できるようにする。

## Consequences

- `python` 前提の軽量スクリプトや検証コマンドが失敗しにくくなる。
- system 配下を直接いじらず、dotfiles と `chezmoi apply` で再現できる。
- `/usr/bin/python3` を直接呼ぶため、将来 Python 配置が変わった場合は source を更新する必要がある。
