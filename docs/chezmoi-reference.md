---
title: "chezmoi リファレンス"
updated_at: 2026-04-03
---

# chezmoi リファレンス

このドキュメントは、このリポジトリで dotfile を変更するときに誤解しやすい chezmoi の基本挙動をまとめたもの。
判断に迷ったら、ここで整理した前提と公式ドキュメントを確認してから変更する。

## 基本概念

- chezmoi は source state から target state を計算し、destination directory に適用する。
- source directory は通常 `~/.local/share/chezmoi`。
- destination directory は通常 `~`。
- このリポジトリで編集する `dot_*` などは source state の表現であり、実ファイル名や権限とは 1 対 1 ではない。

## このリポジトリで重要なルール

### 1. `dot_` は名前変換

- `dot_foo` は target では `.foo` になる。
- `dot_` はファイルだけでなくディレクトリにも使える。

### 2. `private_` は名前変換ではなく権限属性

- `private_` は target 名を変えるための接頭辞ではない。
- `private_` は target file / directory から group / world 権限を外す属性。
- このリポジトリの `dot_codex/private_config.toml` が `~/.codex/config.toml` になるのは、`private_` の後ろのファイル名が target 名として解釈されるためであり、意味は「config.toml を private 権限で配置する」こと。

### 3. 先頭 `.` の source ディレクトリは原則無視される

- source state で先頭 `.` のディレクトリは、`.chezmoi*` 系の special directory を除いて既定で無視される。
- そのため repo ローカルの `.claude/skills/` は chezmoi の配備対象ではない。
- `.claude/skills/` を編集しても `chezmoi apply` の対象にはならない。

### 4. `.chezmoiignore` は source path ではなく target path に対して書く

- `.chezmoiignore` のパターンは `dot_claude/...` のような source path ではなく、`.claude/...` のような target path に対して評価される。
- ignore 判定で迷ったら、source 名ではなく「最終的にどこへ出るか」を先に考える。

### 5. source / target の対応は推測せず確認する

- 命名規則の解釈を手で推測しきらない。
- 迷ったら `chezmoi target-path <source-path>` で source から target を確認する。
- 逆方向は `chezmoi source-path <target-path>` で確認する。

### 6. symlink は source state では「普通のファイル」で表現する

- chezmoi の source state は regular file と directory だけで構成される。
- target が symlink の場合でも、source 側では symlink 自体ではなく `symlink_` prefix を持つ regular file で表現する。
- `symlink_python` の内容が `/usr/bin/python3` なら、target では `python -> /usr/bin/python3` の symlink になる。
- symlink target は source file の内容から解釈され、末尾の改行は取り除かれる。
- `dot_` と組み合わせる場合の許可順は `symlink_`, `dot_`。たとえば `symlink_dot_foo` は target で `.foo` という symlink になる。

### 7. `chezmoi add --follow` は「symlink を管理する」ではなく「symlink の先を file として取り込む」

- 既に destination にある symlink を `chezmoi add` すると、既定ではその symlink 自体を source state に取り込む。
- `chezmoi add --follow <target>` は、その symlink を辿ってリンク先の実体を file として取り込むためのオプション。
- つまり `--follow` を使うと、次回 `chezmoi apply` では symlink が維持されるのではなく、通常 file に置き換わる。
- symlink ベースの dotfile manager から移行するときは、この挙動差を前提に `--follow` を使うか判断する。
- 絶対パス symlink を portable な template として取り込みたい場合は `--follow` ではなく `--template-symlinks` の検討対象。

### 8. symlink mode は「常に symlink」ではない

- `mode = "symlink"` は、可能な regular file を source directory への symlink として配備しやすくする mode。
- ただし encrypted, executable, private, template の file には使えない。
- directory 全体にも使えない。
- symlink mode でも `chezmoi add` した時点では target は即座に symlink 化されず、`chezmoi apply` が必要。
- このリポジトリでは通常 mode を前提とし、必要な箇所だけ明示的な `symlink_` source で扱うのが基本。

## dotfile 変更時のチェックリスト

1. 変更対象が chezmoi 管理の source state か、repo ローカルファイルかを区別する。
2. source 名から target 名を推測せず、必要なら `chezmoi target-path` で確認する。
3. 権限属性と名前変換を混同しない。特に `private_` を filename rewrite と見なさない。
4. `.chezmoiignore` を触る場合は、pattern が target path 基準かを確認する。
5. `chezmoi apply` の前とドリフト確認時に `scripts/chezmoi-drift --check-ignore` を実行し、source が `.chezmoiignore` により意図せず無効化されていないか確認する。
6. 変更後に `chezmoi diff` を見て、意図した target だけが差分になっているか確認する。
7. symlink を扱うときは、「source で `symlink_` file を書くのか」「既存 symlink の中身を `--follow` で file として取り込むのか」を先に区別する。

## 公式ドキュメント

- [Concepts](https://www.chezmoi.io/reference/concepts/)
- [Source state attributes](https://www.chezmoi.io/reference/source-state-attributes/)
- [Target types](https://www.chezmoi.io/reference/target-types/)
- [.chezmoiignore](https://www.chezmoi.io/reference/special-files/chezmoiignore/)
- [Special directories](https://www.chezmoi.io/reference/special-directories/)
- [add](https://www.chezmoi.io/reference/commands/add/)
- [target-path](https://www.chezmoi.io/reference/commands/target-path/)
- [Migrating from another dotfile manager](https://www.chezmoi.io/migrating-from-another-dotfile-manager/)
- [umask](https://www.chezmoi.io/reference/configuration-file/umask/)
