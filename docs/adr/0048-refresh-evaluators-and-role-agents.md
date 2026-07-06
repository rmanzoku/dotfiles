---
title: "Refresh Evaluators And Role Agents For 2026 Context Practices"
date: 2026-07-05
agent_model: "Claude Fable 5 (claude-fable-5)"
status: "accepted"
---

# ADR 0048: Refresh Evaluators And Role Agents For 2026 Context Practices

## Context

docs-evaluator / code-evaluator は評価の具体手法であり、その根本にあるのはユーザーの判断ドクトリンを写した biz / tech custom agent である。ユーザーの AI 思想は rmanzoku/workspace(回答空間モデル、role 分離 + Judge 仲裁、registry-first、artifact-driven)にまとまっており、2026-07 時点の外部ベストプラクティス(Anthropic context engineering / Agent Skills authoring、LLM-as-judge の rubric 設計、行為リスク格付けと human-in-the-loop)も更新されていた。4 対象を同じ回で刷新し、思想は参照ではなく rubric・判断基準の中身へ織り込む方針をユーザーが選択した。

外部知見は Web 調査後に出典照合の敵対的検証を通し(21 confirmed / 3 refuted)、反証された主張(conditionally-activated criteria の形式化、Brier 数値比較、bias 対策系統評価の詳細)は設計から除外した。検証記録は `.context/2026-07-05-evaluator-agent-refresh/01-research.md`(作業時点のセッション artifact)。

## Decision

1. **evaluator 2 スキルの契約を v2.0 に更新する。**
   - 生成する `.context/<skill>/<task>/` 配下の全 artifact に Front Matter(`task` / `phase_or_step` / `created_at`、report は `mode` 追加)を必須化し、artifact gate(`scripts/phase_artifact_hook.py`)と整合させる。
   - rubric に「Applying the Rubric」を新設: 基準の独立判定、非該当基準の `N/A` 記録、trace 根拠(パス:行)必須、damage depth × 可逆性による severity、条件付き smell 仮説の表現、P0/P1 への Revisit conditions(判断が反転する観測)、verbosity bias の抑制、単一パス=一視点の自認、rubric 実質変更時の過去レポート突合。rubric は front matter で版管理する(v2.0)。
   - docs-evaluator の AI Readability を context economy 観点(最小 high-signal 読路、JIT ポインタとしての entrypoint、3 層 progressive disclosure、instruction altitude)へ刷新する。
   - code-evaluator に pillar「Future-context fit」を追加し、tech ドクトリン(phase 第一級入力、匿名仕様判断の観測点、guard clause 健全視、fallback 昇格原則、高 damage-depth 領域の除外)を rubric 本文へ織り込む。license-triage の「この repo の典型形」既定を廃し、配布文脈は対象 repo の証拠から確定(不能なら needs-confirmation)とする。
   - Workflow はコピー可能チェックリスト形式とし、SKILL.md と references の重複記述は正本 1 箇所へ集約する。

2. **biz / tech agent 定義へ外科的追加を行う(全面再構成はしない)。**
   - Context intake: fresh context 前提と、恒久判断に必要な最小入力の列挙。欠落時は条件付き判断+欠落入力の名指し+最安の検証。
   - 可逆性格付け: read-only / reversible / irreversible を判断速度の非対称(two-way fast / one-way slow + 人間承認)に接続。
   - 出力規律: confidence / supporting strength は証拠基盤の名指しとセット、Revisit conditions は判断反転情報を含む、凝縮出力+パス参照、`.context/` 保存時は artifact Front Matter。
   - biz に decision rights(出力は助言、最終決定権は常にユーザー)と decision journal 記録の促しを追加。tech の Future Context Review に context economics レンズを追加。
   - モデル名・世代依存の記述は引き続き置かない(registry-first と frontier 追従は agent 定義の外側の関心)。
   - `.md`(Claude)と `.toml`(Codex)は同内容を維持し、Codex 固有節は保持する。

3. **単発例外の記録**: `dot_*` 配下(agent 定義の chezmoi source)は通常 Codex 管理だが、今回はユーザーの明示許可により Claude Code が直接編集した。これは単発例外であり、`dot_*` 編集禁止ルール自体は変更しない。

## Consequences

- evaluator の成果物が artifact gate から可視になり、レポートの findings は反証条件付きで再訪可能になる。
- 両 evaluator と biz/tech agent が同じ判断語彙(damage depth、可逆性、条件付き仮説、Revisit conditions、証拠基盤付き confidence)を共有し、単独実行でも複数 reviewer + judge 構成でも出力を仲裁しやすくなる。
- rubric の版管理により基準変更のドリフトを検知できる。実質変更時は過去レポートとの突合を要する。
- agent 定義の変更は 1Password バックアップ(`opmaterialize add` × 4 ファイル)の更新が完了するまで、リストアで巻き戻るリスクがある(作業時点で認証待ちにより未完、`.context/2026-07-05-evaluator-agent-refresh/04-agent-changes.md` に手順記録)。
- ドクトリンの保守は今後も「失敗・違和感の観測 → 原則を 1 つ追加/修正 → 再評価」の増分ループで行い、大規模一括書き換えを避ける。
