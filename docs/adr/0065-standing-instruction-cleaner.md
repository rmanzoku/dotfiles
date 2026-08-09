---
title: "ADR 0065: 指示面の掃除を常設ロール化する(cleaner agent + instruction-cleaner skill)"
status: "Accepted"
date: "2026-08-09"
worked_at: "2026-08-09 JST"
agent_model: "Claude Fable 5 (Claude Code)"
---

# ADR 0065: 指示面の掃除を常設ロール化する

## Context

連作「増幅と掃除」の中心命題は、生成能力 α が上がり続ける環境では掃除率 c を上げない限り stale な記述が次の判断の前例として増幅される(安定条件 α(1−c) < 1)、というものである。この repo では ADR-0061〜0063 で一回きりの大掃除を行い、`scripts/instruction-gc` で検知を機械化したが、**検知された warn を誰が消すかは手動のまま**で、c のオーナーが存在しなかった。

常時露出面の実測では、最大の未掃除面は AGENTS.md(4,684 字、probe 検証済み)ではなく **skill description 群(合計 13,435 字)**である。description は毎セッション全文がコンテキストに載るため、増幅の観点では本文より優先度が高い。first-party 13 skill が 400 字超(計 8,829 字)、うち最大は fable-5-tuning の 1,002 字。

## Decision

1. **cleaner ロールを常設する**。`dot_claude/agents/private_cleaner.md` / `dot_codex/agents/private_cleaner.toml`(tracked)+ `skills/instruction-cleaner`(workflow 正本)の対。委譲契約は ADR-0063 に従い agent description に置く。
2. **KPI は 3 点構成とし、削除行数・削除バイト数を KPI にしない**(Goodhart 対策)。
   - 鮮度 SLO: instruction-gc の fail は即時、warn は次回 run までに解消または明示的却下
   - 露出予算: 常時露出面(common-rules、first-party skill description、agent description)の合計字数を `docs/instruction-baseline.json` に記録し、超過は warn。意図的な増加は同じ変更内で baseline を更新する
   - 等価性ガード: 意味を持つ行の削除・圧縮は、blank-slate probe(挙動 probe / description は発火 probe)で維持を示したものだけを「掃除」に数える
3. **権限線**: 機械的に検証可能な死参照(退役ツール名、存在しない path、install 鮮度ずれ)は自動修正してよい。意味を持つ削除・統合は PR 提案とし、probe 証跡を添えて人間が merge する。
4. **cadence**: イベント駆動(gc 非 green 時)+手動起動から始める。定期化は運用実績を見てから判断する。自動実行は仕掛けない。
5. **one-in-one-out**: common-rules「指示の永続化と反映先」に 1 行追加する——恒久指示の追加時に、既存指示の削除・統合候補を併せて検討すること。書き込み時点(増幅の発生点)に効く唯一のルールであり、automation では代替できないため、露出予算の増加を許容する。追加は blank-slate probe で再検証する。
6. **cleaner 自身の足跡を最小化する**: レポート時系列ファイルは作らない(PR 履歴と gc 出力が記録)。増える永続ファイルは baseline JSON 1 つ。cleaner の description も 400 字以下とする。
7. **instruction-gc の check 6 を first-party / external で区別する**。external skill(vercel-cli 等)の description は編集権がないため warn ではなく info とする。また、md/toml の意図的ホスト分岐を持つ agent(personal / tech)は allowlist で info に落とし、warn は実際に対処可能な signal だけに保つ(恒常 warn は alert fatigue として掃除対象)。
8. stale の判定基準は ADR-0061 の削除 4 クラス(死参照 / モデル既定挙動の教示 / 期限切れ一時ルール / 重複)を正とし、cleaner skill がこれを常設ルールブックとして参照する。

## Consequences

- ADR-0061〜0063 の方法論が一回きりの作業から常設プロセスへ昇格し、c にオーナーが付く。
- 掃除の成果は「挙動を変えずに減らした量」だけが得点になる。probe を通らない削除は掃除と数えない。
- chezmoi checkout は複数セッションで共有されるため、cleaner は worktree での作業を標準とし(`chezmoi apply --source` で検証)、共有 checkout で作業する場合は blob staging で自分の変更だけを commit する。
- git 未追跡の private_*(biz / tech / personal)は cleaner の編集・commit 対象外。計測(露出量)には installed 実体を使ってよい。
- external skill は読み取り専用。ダイエットは upstream への提案か、install 差し替えの判断としてユーザーへ返す。

## Validation

- `scripts/skill-quick-validate skills/instruction-cleaner`
- one-in-one-out 追加後の blank-slate probe 2 本(重複追加の抑止 / 新規追加時の削除候補検討)で [critical] 全達成
- description ダイエットの旧新発火 probe(16 プロンプト、blank-slate 選択器 2 体)で critical 全一致・新が旧を下回らないこと
- 施工後 `scripts/instruction-gc` が fail=0、first-party description warn=0
