# chezmoi リファレンス

最終更新: 2026-03-12

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

## dotfile 変更時のチェックリスト

1. 変更対象が chezmoi 管理の source state か、repo ローカルファイルかを区別する。
2. source 名から target 名を推測せず、必要なら `chezmoi target-path` で確認する。
3. 権限属性と名前変換を混同しない。特に `private_` を filename rewrite と見なさない。
4. `.chezmoiignore` を触る場合は、pattern が target path 基準かを確認する。
5. 変更後に `chezmoi diff` を見て、意図した target だけが差分になっているか確認する。

## 公式ドキュメント

- [Concepts](https://www.chezmoi.io/reference/concepts/)
- [Source state attributes](https://www.chezmoi.io/reference/source-state-attributes/)
- [.chezmoiignore](https://www.chezmoi.io/reference/special-files/chezmoiignore/)
- [Special directories](https://www.chezmoi.io/reference/special-directories/)
- [target-path](https://www.chezmoi.io/reference/commands/target-path/)
- [umask](https://www.chezmoi.io/reference/configuration-file/umask/)
