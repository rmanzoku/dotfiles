---
title: "Adopting This Dotfiles Repository"
updated_at: 2026-06-23
---

# Adopting This Dotfiles Repository

このリポジトリは、第一義的には元の利用者の作業環境を復元・運用するための dotfiles です。
同時に、他者が初期設定として流用したり、AI 運用の方針を参照したりするケースも想定します。

## レイヤー分離

流用時は、次の 3 層を分けて扱います。

| 層 | 内容 | 流用時の扱い |
|---|---|---|
| 汎用 dotfiles | shell、git、共通 AI 指示、runner / Skill 管理の骨格 | そのまま流用しやすい |
| オーナー固有の既定値 | clone 元、workspace repo、1Password account / vault の既定値、private agent restore 手順 | fork 側で差し替える |
| private state | private agent 定義、secret-backed file、account profile 対応、secret reference、認証済み state | git では共有しない |

新しい設定を追加するときは、できるだけ汎用層へ置きます。
個人・会社・案件・マシンに依存する値は、環境変数、ignored private file、1Password-backed restore、または各作業リポジトリの `.env` に寄せます。

## 既知のオーナー依存点

流用者は少なくとも以下を確認します。

- `README.md` の clone URL は元の upstream を指しているため、fork 利用時は自分の repo URL に置き換える。
- `scripts/bootstrap-workspace` は既定で元利用者の workspace repo を対象にする。流用時は `WORKSPACE_REPO_URL`、`WORKSPACE_REPO_HOST_PATH`、`WORKSPACE_ROOT`、`WORKSPACE_TARGET` で差し替えるか、実行しない。
- `oprun` / `opmaterialize` の既定 1Password account / vault は元利用者の運用に合わせている。流用時は `OP_ACCOUNT`、`OP_DOTFILES_ENV_FILE`、`OP_DOTFILES_MATERIALIZE_VAULT` を明示する。
- `personal`、`tech`、`biz` などの private agent 定義は git に含まれない。必要なら流用者自身の agent 定義を作る。
- Google / Freee の account profile 名、実アカウント対応、credential path、secret reference は git に含めない。Personal または各作業リポジトリの責務として扱う。

## Role Agents

この repo の運用では `tech`、`biz`、`personal` のような role agent を使うことがあります。
これらは単なる汎用 assistant ではなく、元利用者の判断スタイル、実務文脈、レビュー観点をある程度模倣する private agent として存在します。

- `tech`: 設計、実装方針、保守性、不可逆リスクのレビュー
- `biz`: 事業前提、顧客価値、収益性、運用判断の整理
- `personal`: 予定、タスク、連絡、優先度、個人実務の整理

流用者が同じ名前の agent を使う場合でも、中身は自分の文脈に合わせて作り直します。
元利用者の private agent 定義や private secretary facts は 1Password-backed private state であり、git からは復元できません。

AI agent は、これらの role agent が見つからない場合に元利用者を模倣して補完してはいけません。
利用可能な agent / docs / user confirmation の範囲で判断します。

## 追加時の方針

この repo に新しい設定・script・Skill・runner を追加するときは、次を確認します。

1. 個人名、会社名、account 名、profile 名、credential path、secret reference、ローカル絶対 path を git に固定していないか。
2. オーナー固有値が必要なら、環境変数や ignored private state で差し替えられるか。
3. 流用者が実行すると危険な副作用があるなら、README または関連 docs に opt-in 条件を書いたか。
4. AI が誤って元利用者の private context を前提にしないよう、AGENTS / Skill / runner で停止条件を明示したか。
