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
9. **役割分担と層分離(2026-08-09 同日追記、ユーザー判断)**: 検知は 2 センサーが担う — instruction-gc(機械・毎回)と docs-evaluator(意味・明示起動。report-only 契約は変えない。検出と閉包で KPI 勾配が逆向きのため同一オーナーにしない)— cleaner は閉包だけを所有する。stale クラスに「description の取り合い(trigger 重複)」「skill 統廃合候補」「skill と docs の矛盾」を追加し、検知は evaluator と発火 probe に割り当てる。判断で検知した stale は可能な限り gc の check へ機械化してから閉じる(ratchet)。empirical-prompt-tuning は probe の設計規約(検証手法)として参照し、skill の再現性改善という別役割を cleaner に吸収しない。思想・根拠は ADR と role agent 層(層分離の正本: `docs/runner-skill-governance.md` §Layering)に置き、skill には再現可能な手順だけを書く。
   - 背景: 過去 13 run の docs-evaluator は思想(conditioning surface の重み付け)を持ちながら description 肥大を一度も検出できなかった。思想が判定文言(閾値)に落ちていなかったためで、evaluator 自身が出した具体候補(迷子 ~/CLAUDE.md、P1)も閉包オーナー不在で約 1 ヶ月放置された。
10. **cleaner を doctrine-only 化する(2026-08-10 追記、ユーザー判断)**: agent 定義から dotfiles 固有の手段(センサー名の固定・skill 固定・repo 束縛・実行環境制約)を外し、agent はドメイン中立の掃除ドクトリンだけを持つ — 検出/閉包分離、KPI 3 点、増幅荷重の優先順位、stale 分類、**4 スロット要件(センサー / 露出指標 / 等価性ガード / ratchet 先を名指しできないドメインでは掃除しない)**、権限線、escalation。ドメイン束縛は末尾 1 節に限定: 指示面は instruction-cleaner に従い(実行環境制約はそちらへ)、他ドメイン(コード: guard=テスト・型検査、ratchet=linter/CI / 仕様書: guard=blank-slate 実装者 probe)は 4 スロットを満たす skill か親の明示契約があるときだけ実行する。instantiation skill は必要時に作り、先回りの一般化はしない。あわせて tech に掃除軸・層分離検査・sensor/closure routing を、biz に増幅と掃除・依頼先想起・賭けと採用分離の lens を追記した(private_ 定義のため本 ADR が変更記録を兼ねる。検証は blank-slate probe 3 本、全 critical 合格)。
11. **run 1 残項目の裁定(2026-08-12 追記、ユーザー判断)**: **R3 は最小定義で採用** — gc check 11 として first-party description 間の backtick トークン重複を info で検知する(裁定済み共有トークンは allowlist。初期値 `opmaterialize` = run 1 probe で正しい近接と裁定済み)。**R4(probe fixture の永続化)は却下** — 発火 probe は run 内の旧新比較で完結するゲートであり時系列指標ではない。fixture は退役のたびに保守を要し(run 1 の発話セットには退役済み skill が既に含まれていた)、footprint 最小化ルールに例外を作る価値がない。probe セットは `.context` の使い捨てを正とする。**E-3(claude-cli-runner の fable-5 profile)は見送り** — 使用実績の証拠がなく、Fable の適応は de-prescription(引く方向)で `none` に対する adapter の価値が薄い。Codex → Claude CLI(Fable)委譲で `none` が不足する実例が出たら実装する。**§B-2(common-rules F11a / F11b の削減候補)は却下として閉包** — confidence low、両ホスト挙動 probe の費用が削減益(約 100〜150 字)を上回り、合格しても結果が現行ホスト世代に固定され再 probe のトリガーが存在しない。F11b 前半は挙動の教示であると同時に委譲の許可付与でもあり、削除は保守的世代を過小委譲へ振るリスクを持つ。再訪条件: common-rules の次回大改訂時、またはホスト世代の交代時。
12. **instruction-cleaner を repo 非依存にする(2026-08-18 追記、ユーザー判断、GPT-5.6 (Codex))**: `scripts/instruction-gc` と `docs-evaluator` は dotfiles adapter とし、skill の core 契約から固定名を外す。repo 固有 sensor が無い場合は、`rg`、path 存在確認、文字数計測、blank-slate review / probe を portable defaults として observe から開始する。sensor 不在は停止理由にせず、永続 ratchet が無い場合だけ close 時の制約として明示する。新しい CI / script の追加は依頼範囲と repo 規約に従い、汎用化を理由に自動追加しない。

## Consequences

- ADR-0061〜0063 の方法論が一回きりの作業から常設プロセスへ昇格し、c にオーナーが付く。
- 掃除の成果は「挙動を変えずに減らした量」だけが得点になる。probe を通らない削除は掃除と数えない。
- chezmoi checkout は複数セッションで共有されるため、cleaner は worktree での作業を標準とし(`chezmoi apply --source` で検証)、共有 checkout で作業する場合は blob staging で自分の変更だけを commit する。
- git 未追跡の private_*(biz / tech / personal)は cleaner の編集・commit 対象外。計測(露出量)には installed 実体を使ってよい。
- external skill は読み取り専用。ダイエットは upstream への提案か、install 差し替えの判断としてユーザーへ返す。
- 他リポジトリでは repo 固有 sensor が無くても portable defaults で掃除を開始できる。dotfiles 固有の sensor・baseline・ratchet は adapter として引き続き利用する。

## Validation

- `scripts/skill-quick-validate skills/instruction-cleaner`
- one-in-one-out 追加後の blank-slate probe 2 本(重複追加の抑止 / 新規追加時の削除候補検討)で [critical] 全達成
- description ダイエットの旧新発火 probe(16 プロンプト、blank-slate 選択器 2 体)で critical 全一致・新が旧を下回らないこと
- repo sensor 不在 / 永続 ratchet 不在の portable-defaults probe で critical 全一致し、hidden `.github/` 面を初回列挙できること
- 施工後 `scripts/instruction-gc` が fail=0、first-party description warn=0
