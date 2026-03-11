# ADR 0001: 人間からの継続的な指示は git 管理ファイルへ保存する

- Status: Accepted
- Date: 2026-03-11
- Worked At: 2026-03-11 10:22 JST
- Agent Model: GPT-5 Codex

## Context

この環境では、作業の大半を Git worktree 上で行う。
worktree はマージや削除で消えることがあり、AI セッションも worktree ごとに新規作成される。

そのため、AI がセッション内メモリや Auto memory に保持した情報は、次の worktree や新規セッションで再現できない場合がある。
一方で、人間から与えられた継続的な指示は、次回以降の作業でも再利用できる必要がある。

また、一時ファイルを `/private` や `/tmp` に出力すると、worktree の削除後もファイルが残り、後始末や再現性が崩れる。

## Decision

- 人間からの継続的な指示は Memory に依存せず、git 管理されたファイルに保存する。
- 保存先は、作業リポジトリの `docs/`、agent ごとの管理ディレクトリ（Claude は `.claude/`、Codex は `.agents/`）、またはグローバル dotfiles（`~/.claude/CLAUDE.md`、`~/.codex/AGENTS.md` など）とする。
- worktree の削除や新規セッションで失われる前提の情報は、再現可能な git ファイルとして残す。
- 一時ファイル、下書き、調査メモなどの一過性ファイルは、作業 worktree 内の `.context/` に生成する。
- `/private` や `/tmp` は一時ファイルの置き場として使わない。

## Consequences

- 新規セッションや別 worktree でも、人間の指示をファイルから再読できる。
- セッションメモリの有無に依存せず、作業の再現性が上がる。
- `.context/` を使うことで、一時ファイルの寿命を worktree と揃えられる。
- 継続的な指示を受けた場合は、その場で適切な git 管理ファイルへ反映する運用が必要になる。
