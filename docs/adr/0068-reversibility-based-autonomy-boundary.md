---
title: "ADR 0068: 可逆性を軸に AI の自走範囲を定義する"
status: "Accepted"
date: "2026-08-12"
worked_at: "2026-08-12 JST"
agent_model: "Claude Opus 5 (Claude Code)"
---

# ADR 0068: 可逆性を軸に AI の自走範囲を定義する

## Context

「簡単に復旧できる可逆な操作は AI が確認なしで進めてよい」という運用方針を共通ルールへ入れるにあたり、
素朴に書くと解釈がぶれる箇所が 3 つあった。

1. **可逆性の判定軸**: 「取り消しコマンドが存在するか」で判定すると `git revert` の存在により
   ほぼ全ての push が可逆になり、ルールが無効化される
2. **具体例の扱い**: git / CI / public repository の具体は 3 条件から導出できる事例であり、
   条文に列挙すると原則より列挙が参照され、未記載ケースが「載っていない＝可」に倒れる
3. **harness permission との関係**: allowlist を「ユーザーが承認済み」と読むと自走し、
   prompt を「禁止」と読むと停止する。permission は実行可否であって判断ではない

初期案では git 操作の判定例を条文に含めていたが、ユーザー指摘により削除した。
「private repository の共同作業者は他者ではない」という判断も、初期の条件定義からは導出できず、
境界の単位（個人 / リポジトリ / 組織）が未定義であることが原因と判明したため条件側を修正した。

## Decision

`.chezmoitemplates/common-rules.md` に `## 可逆性と自走範囲` を新設する（6 bullet）。

- 可逆性は 3 条件の AND で定義する。**(1) 巻き戻し作業の帰属**（実行者だけで完結するか）、
  **(2) 影響の到達範囲**（管理境界の外へ出るか）、**(3) 時間境界**（巻き戻しコストが時間経過や
  外部の反応で増大するか）。この 3 軸により、git 以外の未知の操作にも適用できる
- 不可逆性は「取り消し手段の不在」ではなく「取り消しコストが自分の外側へ漏れること」で判定する
- 管理境界の内側に private repository の collaborator と社内メンバーを含め、**条件(2) の到達先判定に
  のみ用いる**。条件(1) は「実際に取得・参照済みの相手」を行為ベースで数える
- 確定できないときの既定停止点を「成果物を利用者の管理下に置いたまま提示できる最後の地点」と
  絶対値で定める。停止はより可逆な代替経路が無い場合に限る
- 手続規約が存在する場合は可逆性より優先する。規約は推測せず、運用実績などの間接証拠を
  自走の根拠にしない
- permission は「実行できるか」であって「実行してよいか」ではない

git / CI / public repository の判定例は条文に含めず、本 ADR の Consequences に残す。

## Consequences

### 判定例（条文には含めない。境界が疑われたときの参照用）

| 操作 | 判定 | 破れる条件 |
|---|---|---|
| ローカル commit、作業ブランチ作成 | 可逆 | — |
| private repository の作業ブランチへの push | 可逆 | — |
| private repository 内の PR 作成 | 可逆 | — |
| CI / デプロイ連携のないブランチへの merge | 可逆 | — |
| public repository への push / merge | 不可逆 | (2) 境界外への公開 |
| CI・Vercel が連携したブランチへの merge | 不可逆 | (2) 境界外での自動実行、(3) |
| force push、履歴書き換え、branch / tag の削除 | 不可逆 | (1) 他者の取り直しが必要 |
| 破壊操作の事前バックアップ後の実行 | 可逆化して可 | 退避取得の失敗時は不可逆へ戻す |

### 守りの条文を持たない設計

本セクションは意図的に「攻め」側の規定に絞り、harness が既定で持つ保守的判断（不可逆・外部作用の
ある操作は確認を取る）を重複記述しない。empirical-prompt-tuning による 5 イテレーション・
19 subagent run の検証で、守りの条文が結論を変えたケースは 1 件も観測されず、9 bullet から
6 bullet へ削っても [critical] 判定（main へ push しない / force push しない / Slack 投稿しない /
DNS を変えない / allowlist を根拠にしない）は全て維持された。
逆に、観測された executor のやり直しはほぼ全件が「保守側へ傾いた判断を攻めの条文が引き戻した」
ケースであり、本セクションの価値は自走を許可する方向に集中している。

この知見は cleaner の doctrine（`dot_claude/agents/private_cleaner.md` と Codex 側の複製）へ
stale class の一種として反映した。ADR-0061 のクラス 1「モデル既定挙動の教示」は能力・手順の既定を
指しており、harness が課す判断の向きの重複は読み落とされやすいこと、およびこのクラスだけは
「消すと安全装置を外したように見える」ため過剰に温存される非対称があることを追記している。
instruction-cleaner の挙動 probe 側には、保守側の規定を削るときは `[critical]` にその規定が
守っているように見える結末を置く条件を加えた（攻め側の結末だけで固定すると probe が空振りで通るため）。

### 検証

- 評価シナリオ 3 種 + hold-out 1 種、`[critical]` タグ付き要件チェックリストで accuracy を測定
- accuracy はイテレーション 3・4・5 で全シナリオ 100%。hold-out は導入以来 3 回連続 100% で
  overfitting なし
- 残存する曖昧性 2 件（条件(1) の対象範囲、条件(2) の係り受け）は最終版で修正し、
  新規不明点 0 の 2 連続クリア（厳密な収束条件）には未達のまま resource cutoff で打ち切った
- 検証 artifact は `.context/reversibility-rule/`（git 管理外）

### skill 本文への適用と判定例の精緻化（2026-08-17 追記、Claude Opus 5 / Claude Code）

skills/ の保守的ガードを本 ADR の 3 条件で棚卸しし（docs-evaluator `guidance-consistency-review`、95 件）、
自走境界と矛盾する規定を skill 側で閉じた。あわせて判定例を 2 点精緻化した（表の行は変えない）。

- **merged な remote branch の削除（private repository）**: 表では「branch / tag の削除 = 不可逆 (1)」だが、
  default branch に到達可能な tip を持ち open PR も protection もない branch は、tip SHA を記録すれば
  `git push origin <sha>:refs/heads/<name>` で実行者だけが復元でき、到達先は private repository の
  collaborator（境界内）にとどまる。「事前バックアップ後の破壊操作」行に該当するものとして、
  `git-branch-review` は private のときだけ自動削除し、public / internal / 不明では提案に留める
- **private repository への PR comment 投稿**: PR 作成と同じく可逆（author が削除でき、通知先は境界内）。
  `handoff` は private のとき push / PR 作成 / comment 投稿まで行い、それ以外は draft-first を維持する
- 可視性は `gh repo view --json visibility` で毎回解決し、`PRIVATE` 以外は保守側に倒す

### 想定される影響

- private repository での commit / push / PR 作成が確認なしで進むため、往復が減る
- 共有ブランチへの合流と外部到達を伴う操作は従来どおり停止する
- 「恒久的な permission 緩和を不可逆として扱う」規定は Codex 固有ルール
  （`danger-full-access` はその実行時だけ）が既にカバーしているため、共通ルールには置かない
