---
name: opus-4-8-tuning
description: "Audit and rewrite repository docs, skills, prompts, and agent harness scaffolding so they fit Claude Opus 4.8 behavior and API guidance: Opus 4.7 prompt compatibility, high effort default, xhigh coding/agentic starting point, adaptive thinking, unsupported sampling parameters, improved tool triggering, coverage-first code review harnesses, long-context and compaction recovery, fast mode, mid-conversation system messages, lower prompt-cache minimums, and refusal stop details. Use when the user wants to migrate or readiness-check prompts, AGENTS.md / CLAUDE.md / skill files, agent rules, or eval harnesses for Opus 4.8. Do not use for broad Claude SDK migrations or application feature rewrites beyond prompt, model, and orchestration guidance."
---

# Opus 4.8 Tuning

リポジトリのドキュメント、スキル、プロンプト、agent harness を Claude Opus 4.8 に合わせて整備するためのスキル。

API クライアントコードの自動移行は対象外。SDK や Messages API 呼び出しの実装修正は公式 Claude API 移行手順へ委譲し、本スキルは人間と AI が読む運用文書・プロンプト・ハーネス設計に集中する。

## 起動する場面

- ユーザーが「Opus 4.8 向けに整備したい」「Opus 4.8 migration」「Opus 4.8 readiness」と発話した。
- `CLAUDE.md` / `AGENTS.md` / `SKILL.md` / `docs/**` / `prompts/**` / eval harness が古い Opus / Sonnet 前提になっていないか棚卸しする。
- 固定 thinking budget、sampling parameter 指定、強制進捗 scaffolding、古い code review prompt、曖昧な tool use 指示を見直す。

## 起動しない場面

- Claude SDK / API 呼び出しコード自体の移行。
- 単発の質問応答で文書編集や監査を伴わない場合。
- モデル registry の実値変更だけを求められた場合。ただし関連プロンプト監査を含むなら対象にする。

## 参照する公式ソース

作業中は最新の公式ドキュメントを確認する。

- What's new in Claude Opus 4.8: <https://platform.claude.com/docs/en/about-claude/models/whats-new-claude-4-8>
- Prompting best practices: <https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices>
- Migration guide: <https://platform.claude.com/docs/en/about-claude/models/migration-guide>
- Adaptive thinking: <https://platform.claude.com/docs/en/build-with-claude/adaptive-thinking>
- Effort: <https://platform.claude.com/docs/en/build-with-claude/effort>
- Fast mode: <https://platform.claude.com/docs/en/build-with-claude/fast-mode>
- Prompt caching: <https://platform.claude.com/docs/en/build-with-claude/prompt-caching>

## Opus 4.8 で押さえる項目

1. **Opus 4.7 prompt 互換**
   4.7 で動いているプロンプトは原則そのまま動く。全面 rewrite より、4.8 で問題が出る箇所と stale な 4.7 固有記述だけを最小修正する。
2. **Effort が最重要レバー**
   4.8 の既定 effort は `high`。coding / agentic use case は `xhigh` 起点、知能要求タスクは最低 `high`、`low` は短く明確な latency-sensitive タスクに限定する。複雑タスクで浅い場合は prompt magic word より先に effort を上げる。
3. **Adaptive thinking は明示有効化**
   thinking は `thinking: {"type": "adaptive"}` を明示しない限り off。固定 `budget_tokens` は使わない。
4. **Sampling parameter は使わない**
   `temperature` / `top_p` / `top_k` の非デフォルト指定は避け、出力揺れや文体はプロンプト、例、評価で調整する。
5. **Tool triggering 改善を踏まえる**
   4.8 は必要な tool call を飛ばしにくいが、tool 必須タスクでは「いつ・なぜ使うか」を明示する。古い対策としての過剰な tool 強制や N 回ごとの固定 tool 促進は削る。
6. **Code review harness は coverage-first**
   finding phase で「high severity のみ」「保守的に」などの曖昧なフィルタをかけると recall が落ちる。発見段階は uncertain / low severity も含めて出し、別段で ranking / dedupe / verification する。
7. **Long context と compaction 回復**
   長時間 agentic work では、artifact、summary、failure report、再開条件が compaction 後も読めるようにする。会話履歴だけを正本にしない。
8. **Mid-conversation system messages**
   長い API 会話で更新指示を追加する場合に使える。prompt cache を壊さず後続指示を足す用途に限定し、通常の skill 文書では詳細な API 実装を持たない。
9. **Fast mode は API 側の選択肢**
   `speed: "fast"` は Claude API の research preview。運用文書では latency / cost tradeoff と eval 対象として扱い、CLI runner へ勝手に引数追加しない。
10. **Refusal stop details**
    refusal 分岐を扱うアプリや harness は `stop_details` を確認する。通常の agent 運用文書では、blocked / refused / failed を混同しないことだけ明示すればよい。
11. **Vision / computer use**
    最大 2576px / 3.75MP まで扱えるが、1080p が性能とコストの良い起点。座標や画像サイズの旧前提が残っていれば更新する。

## 実行モード判定

依頼を受けたら、編集前に次を決める。判定結果は artifact または作業結果に残す。

1. 複数の合理的解釈がある、または設計合意が必要な場合は、確認してから進める。
2. 中央モデル registry、`CLAUDE.md` / `AGENTS.md` 構造、既存 skill description、複数ファイル横断の破壊的変更を伴う場合は、Plan を提示してから実装する。
3. 明確で局所的な修正なら単発処理として進める。

## 監査フロー

Phase を持つ作業では `.context/<task>/` に artifact を残し、各 Phase の完了条件にする。

### Phase 1: スコープ確定

- 対象ファイル群を列挙する。
- 中央 model registry / resolver の有無を確認する。
- API コード側変更を対象外として切り分ける。
- 旧 Opus / Sonnet 前提の語句を `rg` で洗い出す。

artifact: `.context/<task>/01-scope.md`

### Phase 2: 監査

各対象を「典型修正パターン」と照合し、`path:line`、パターン記号、理由、推奨アクションを記録する。

artifact: `.context/<task>/02-audit.md`

### Phase 3: 改修

正規指示ファイルや model registry を SoT として、重複を増やさず最小修正する。skill description を変更する場合は起動条件が変わるため特に明示する。

artifact: `.context/<task>/03-changes.md`

### Phase 4: 検証

- `scripts/skill-quick-validate <skill-dir>` など repo の検証を実行する。
- `rg` で stale な 4.7 / 旧モデル前提の残存を確認する。
- 可能なら小さな dry-run prompt で読み解きやすさを確認する。

artifact: `.context/<task>/04-verify.md`

## 典型修正パターン

### A. 廃止または非対応 API parameter が残っている

- 兆候: `temperature` / `top_p` / `top_k` / `thinking.budget_tokens` を推奨している。
- 対応: sampling parameter と固定 thinking budget を削除し、adaptive thinking + effort に寄せる。

### B. Effort を prompt magic word で代用している

- 兆候: `ultrathink` / `think hard` / `very carefully` を effort 設定の代替にしている。
- 対応: caller / registry 側で `high` / `xhigh` を設定する。prompt は task intent と acceptance criteria を明確にする。

### C. 4.7 固有の既定値が残っている

- 兆候: 「Opus 4.7 では」「推奨デフォルト xhigh」などが 4.8 migration 文脈で正本化されている。
- 対応: 4.8 既定 `high` と coding / agentic 推奨 `xhigh` を分けて書く。

### D. 強制進捗 scaffolding

- 兆候: N tool call ごと、各 step ごとの固定進捗報告。
- 対応: 削除する。必要なら「重要な blocker / 長時間待機時だけ短く報告」など目的ベースにする。

### E. Tool use 指示が古い

- 兆候: tool を必ず多用させる、または tool 必須タスクなのに条件が曖昧。
- 対応: tool を使う条件と evidence rule を明示する。過剰な固定回数指定は削る。

### F. Code review finding で recall を落としている

- 兆候: finding prompt に「high severity のみ」「be conservative」「nit は出すな」など曖昧なフィルタがある。
- 対応: finding phase は coverage-first にし、confidence / severity を付けて downstream filtering に渡す。

### G. Long context / compaction 後に再開不能

- 兆候: 会話中の合意だけが正本、artifact path や failure report がない。
- 対応: prompt、summary、expected artifacts、blocked state を `.context/` や runner artifact に保存する。

### H. 暗黙の汎化前提

- 兆候: 「関連箇所も適宜」「同様に」だけで対象が未列挙。
- 対応: 対象ファイル、対象範囲、除外範囲を列挙する。

### I. 古い frontend / design prompting

- 兆候: 過剰な boilerplate prompt や古い anti-pattern 指示で創造性を潰している。
- 対応: product context、desired aesthetic、avoid generic AI look を短く明確に書く。選択肢を先に出す flow が必要なら明示する。

### J. Vision / computer use の旧前提

- 兆候: 旧解像度上限や座標変換前提が残っている。
- 対応: 最大 2576px / 3.75MP、実用起点 1080p、cost-sensitive なら 720p / 1366x768 を評価する。

### K. Skill description が弱い

- 兆候: 起動条件、除外条件、対象粒度が description から読めない。
- 対応: literal に解釈できる description へ更新する。変更前後で誤発火と不発火を確認する。

## プロンプト書き換え最小例

旧:

> temperature=0、ultrathink で慎重に考え、3 tool call ごとに進捗を報告し、重要な問題だけ指摘してください。

新:

> Intent: <目的>
> Constraints: <制約>
> Acceptance criteria: <完了条件>
> Finding phase では重要度や確信度で落とさず、見つけた問題をすべて列挙してください。各 finding に confidence と severity を付け、ranking は後続 step で行います。

`effort` は呼び出し側で設定する。coding / agentic なら `xhigh` 起点、知能要求があるなら最低 `high`。

## 完了条件

- 対象ファイルに stale な 4.7 専用 tuning 方針が残っていない。
- 4.8 の effort、adaptive thinking、sampling parameter、tool triggering、review harness、long-context / compaction 方針が公式ドキュメントと矛盾しない。
- API コード変更と文書 / prompt tuning の責務が分離されている。
- 変更根拠、検証結果、残置理由が artifact または作業結果に残っている。
