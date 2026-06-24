---
title: "ADR 0014: python コマンドは ~/.local/bin の wrapper で python3 へ寄せる"
status: accepted
date: 2026-04-03
worked_at: 2026-04-03 11:25 JST
agent_model: GPT-5 Codex
---

# ADR 0014: python コマンドは ~/.local/bin の wrapper で python3 へ寄せる

## Context

この環境では `python3` は Homebrew の `/opt/homebrew/bin/python3` と macOS / Xcode Command Line Tools の `/usr/bin/python3` にあるが、
`python` は標準では存在しない。
そのため、skill の検証や補助スクリプト実行時に `python` 前提のコマンドが失敗しやすい。

一方で、システムディレクトリ配下へ直接 symlink を置くのは管理責務が曖昧になりやすい。
この dotfiles リポジトリでは `~/.local/bin` が PATH の先頭側に入っており、ユーザー管理の軽量 shim を置く場所として既に使っている。

当初は `~/.local/bin/python -> /usr/bin/python3` の symlink を想定したが、
macOS では `/usr/bin/python3` が xcrun 経由の shim として振る舞い、`python` という argv0 で呼ばれると
`Failed to locate 'python'` になった。

その後、画像処理系の補助処理で Pillow をマシン共通に使いたい要件が出た。
`/usr/bin/python3` は OS 管理の Python であり、Homebrew の `pillow` formula で導入した Python package を安定して参照する入口には向かない。

## Decision

- `~/.local/bin/python` を `python3` への互換コマンドとして管理する。
- 実体は symlink ではなく shell wrapper とし、Homebrew の `/opt/homebrew/bin/python3` があればそれを優先し、なければ `/usr/bin/python3` へ fallback する。
- source state では `dot_local/bin/executable_python` を使って executable file として管理する。
- `Brewfile` では `python@3.14` と `pillow` を明示し、Homebrew Bundle で共通 Python と Pillow を復元できるようにする。
- これにより argv0 に依存せず、`python` でも Homebrew Python を優先して起動できるようにする。

## Consequences

- `python` 前提の軽量スクリプトや検証コマンドが失敗しにくくなる。
- system 配下を直接いじらず、dotfiles と `chezmoi apply` で再現できる。
- Homebrew Python では Pillow を共通に使いやすくなる。
- プロジェクト固有の venv、pyenv、別バージョン Python から Pillow を使う場合は、その環境側にも依存追加が必要になる。
- Homebrew の prefix が `/opt/homebrew` 以外の環境では fallback として `/usr/bin/python3` が使われるため、必要なら wrapper の prefix 対応を見直す。
