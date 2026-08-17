---
name: opus-5-tuning
description: "Audit and rewrite prompts, AGENTS.md / CLAUDE.md, skills, and agent harness scaffolding to fit Claude Opus 5: default-on thinking, low-to-max effort ladder, deletion of redundant self-check scaffolding, subagent delegation caps, refusal stop-reason handling, and prompt-cache minimums. Use to migrate or readiness-check prompts and eval harnesses for Claude Opus 5. Not for broad SDK migrations."
---

# Opus 5 Tuning

リポジトリのドキュメント、スキル、プロンプト、agent harness を Claude Opus 5 に合わせて整備するためのスキル。

API クライアントコードの自動移行は対象外。SDK や Messages API 呼び出しの実装修正は公式 Claude API 移行手順へ委譲し、本スキルは人間と AI が読む運用文書・プロンプト・ハーネス設計に集中する。

## 起動する場面

- ユーザーが「Opus 5 向けに整備したい」「Opus 5 migration」「Opus 5 readiness」と発話した。
- `CLAUDE.md` / `AGENTS.md` / `SKILL.md` / `docs/**` / `prompts/**` / eval harness が古い Opus / Sonnet 前提になっていないか棚卸しする。
- 検証 scaffolding、subagent 委譲奨励、強制進捗報告、severity filter 付き review prompt、effort 既定の持ち越しを見直す。

## 起動しない場面

- Claude SDK / API 呼び出しコード自体の移行。
- 単発の質問応答で文書編集や監査を伴わない場合。
- モデル registry の実値変更だけを求められた場合。ただし関連プロンプト監査を含むなら対象にする。

## 参照する公式ソース

作業中は最新の公式ドキュメントを確認する。

- What's new in Claude Opus 5: <https://platform.claude.com/docs/en/about-claude/models/whats-new-opus-5>
- Prompting Claude Opus 5: <https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5>
- Migration guide: <https://platform.claude.com/docs/en/about-claude/models/migration-guide>
- Adaptive thinking: <https://platform.claude.com/docs/en/build-with-claude/adaptive-thinking>
- Effort: <https://platform.claude.com/docs/en/build-with-claude/effort>
- Fast mode: <https://platform.claude.com/docs/en/build-with-claude/fast-mode>
- Prompt caching: <https://platform.claude.com/docs/en/build-with-claude/prompt-caching>

## Opus 5 で押さえる項目

1. **Opus 4.8 からはモデル ID 差し替え+2 つの breaking change**
   価格・機能セットは 4.8 同等のドロップイン。ただし (a) `thinking` 未指定でも adaptive thinking が既定で有効になり、`max_tokens` は thinking と本文の合計上限になる。thinking 前提のなかった route は `max_tokens` を見直す。(b) `thinking: {type: "disabled"}` は effort `high` 以下でのみ許可され、`xhigh`/`max` との併用はリクエスト毎に 400 になる。
2. **Effort は全 5 段階を sweep する**
   既定は `high`。coding / agentic は `xhigh` 起点にしつつ、Opus 5 は `low` / `medium` が旧世代の上位 effort に匹敵するため下方向へ sweep して確定する。旧モデルから持ち越した effort 既定は再評価対象。可視出力の長さは effort では制御できない。
3. **検証 scaffolding は削除する**
   Opus 5 は指示なしで自己検証する。「double-check」「最後に検証せよ」「検証用 subagent を使え」といったプロンプト指示や harness の冗長検証 step は over-verification を招くため削除する。これは従来の self-check ベストプラクティスの逆であり、プロンプト集には Opus 5 向けの例外を設ける。
4. **Subagent 委譲は cap する(4.8 と逆方向)**
   Opus 5 は subagent へ委譲しやすい。4.8 向けに書いた「もっと委譲せよ」系の指導は撤去し、委譲してよい条件と並列数上限を明示する。少数 tool call で済む作業や検証目的の委譲は禁止方向に倒す。
5. **スコープ規律を明示する**
   依頼されていない手順の追加や暗黙のスコープ変更が起きうる。「依頼された範囲で完遂し、逸脱は一言添えて依頼どおり続行」という scope-discipline 指示を足す。
6. **冗長性はプロンプトで調整する**
   user-facing 応答もディスク上の成果物も長くなる傾向。conciseness 指示と成果物の長さ指定を明示する。agentic セッションのナレーションは communication 指示で調整し、強制進捗 scaffolding(N tool call ごと報告など)は削除する。
7. **Code review harness は coverage-first を維持**
   「high severity のみ」「保守的に」等の filter は recall を下げる。発見段階は confidence / severity 付きで全件報告させ、filtering は後段に分離する。
8. **4.7 以降の非対応 API は継続して 400**
   sampling params(`temperature` / `top_p` / `top_k`)、`thinking.budget_tokens`、末尾 assistant prefill は使えない。4.6 以前からの移行ではまずこれらを除去する。
9. **Refusal と fallback**
   safety classifier により HTTP 200 + `stop_reason: "refusal"` が返りうる。`content` を読む前に `stop_reason` を確認し、API 利用文書では `fallbacks: "default"`(beta `server-side-fallback-2026-07-01`)へのオプトインを既定として案内する。運用文書では blocked / refused / failed を混同しないことを明示すれば足りる。
10. **Prompt cache / fast mode / rate limit の実務差分**
    cache 最小 prefix は 512 tokens に半減し、従来 cache 対象外とした短い prompt を再確認する。fast mode(`speed: "fast"`、$10/$50)は Claude API のみで、CLI runner へ勝手に引数追加しない。rate limit は Opus 4.x 統合プールと別バケット。
11. **自己訂正ナレーション**
    誤りの訂正を長く語る傾向がある。user-facing 製品では「結果に影響する訂正だけを簡潔に述べる」corrections 指示を検討する。
12. **実行経路は Claude CLI に限らない**
    Opus 5 は `claude-cli-runner` だけでなく `copilot-cli-runner` など他 CLI runner 経由でも実行される。世代固有の挙動補正は各 runner の prompt profile(model adapter)が担い、role prompt や skill 本文へ固定しない。

## 実行モード判定

依頼を受けたら、編集前に次を決める。判定結果は artifact または作業結果に残す。

1. 中央モデル registry や `CLAUDE.md` / `AGENTS.md` の構造変更を伴う場合は、Plan を提示してから実装する。
2. 明確で局所的な修正なら単発処理として進め、それ以外は監査フローへ進む。

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
- `rg` で stale な 4.8 / 旧モデル前提の残存を確認する。
- 可能なら小さな dry-run prompt で読み解きやすさを確認する。

artifact: `.context/<task>/04-verify.md`

## 典型修正パターン

### A. thinking-disabled と高 effort の併用

- 兆候: `thinking: {type: "disabled"}` を `xhigh` / `max` と組み合わせる想定の文書・設定が残っている。
- 対応: thinking を有効化して effort を下げるか、effort を `high` 以下にする。latency 目的なら `medium` + thinking 有効を第一候補にする。

### B. thinking 前提のない `max_tokens`

- 兆候: `thinking` 未指定 route の `max_tokens` が本文サイズぎりぎりで設計されている。
- 対応: thinking 分の headroom を確保するか、明示的に disabled(effort `high` 以下)へ倒す。

### C. 検証 scaffolding が残っている

- 兆候: 「double-check」「re-verify before responding」「検証 subagent を必ず使う」等の指示、harness の冗長検証 step。
- 対応: 削除する。独立 verifier role が設計上必要な高リスク workflow だけ、目的を明記して残す。

### D. Subagent 委譲奨励が残っている

- 兆候: 4.8 向けの「積極的に委譲せよ」「memory / subagent を必ず使え」系の指導。
- 対応: 撤去し、委譲条件(独立・大規模・並列可能)と並列数 cap、検証目的の委譲禁止を明示する。

### E. 強制進捗 scaffolding

- 兆候: N tool call ごと、各 step ごとの固定進捗報告。
- 対応: 削除する。ナレーション量・文体の調整は communication 指示で行う。

### F. Effort 既定の持ち越し

- 兆候: 「常に xhigh」「4.8 では high 推奨」等が Opus 5 文脈で正本化されている。
- 対応: coding / agentic は `xhigh` 起点、その他は `high` 起点で、`low` / `medium` を含めて sweep して確定する方針に書き換える。

### G. 冗長出力を effort で制御しようとしている

- 兆候: 「短くしたいので effort を下げる」等の記述。
- 対応: conciseness 指示・成果物長さ指定・corrections 指示へ置き換える。effort は思考深度と作業量のレバーとして扱う。

### H. スコープ規律の欠如

- 兆候: 依頼範囲の定義がなく、モデルの裁量でスコープが広がる余地がある prompt。
- 対応: scope-discipline 指示(依頼どおり完遂、逸脱は一言添えて続行、範囲外の行動は停止)を追加する。

### I. Code review finding で recall を落としている

- 兆候: finding prompt に「high severity のみ」「be conservative」「nit は出すな」など曖昧なフィルタがある。
- 対応: finding phase は coverage-first にし、confidence / severity を付けて downstream filtering に渡す。

### J. 4.7 以前の遺物

- 兆候: `temperature` / `top_p` / `top_k` / `thinking.budget_tokens` / 末尾 prefill / `ultrathink` 等の magic word を推奨している。
- 対応: 削除し、adaptive thinking + effort + 明確な task intent へ寄せる。

### K. Skill description が弱い

- 兆候: 起動条件、除外条件、対象粒度が description から読めない。
- 対応: literal に解釈できる description へ更新する。変更前後で誤発火と不発火を確認する。

## プロンプト書き換え最小例

旧:

> 3 tool call ごとに進捗を報告し、完了前に必ず自分の作業を double-check し、大きめの調査は積極的に subagent へ委譲してください。

新:

> Intent: <目的>
> Constraints: <制約>
> Acceptance criteria: <完了条件>
> 依頼された範囲で完遂してください。スコープの変更が必要と判断した場合は一言添えたうえで、依頼どおりの作業を続けてください。subagent は独立・大規模・並列可能な作業に限り、検証目的では使わないでください。

`effort` は呼び出し側で設定する。coding / agentic なら `xhigh` 起点で `low` / `medium` まで sweep し、知能要求があるなら最低 `high`。

## 完了条件

- 対象ファイルに stale な 4.8 専用 tuning 方針(委譲奨励・検証 scaffolding・effort 既定)が残っていない。
- Opus 5 の thinking 既定、disabled-thinking effort 上限、effort sweep、検証 scaffolding 削除、委譲 cap、scope discipline、review harness、refusal / fallback 方針が公式ドキュメントと矛盾しない。
- API コード変更と文書 / prompt tuning の責務が分離されている。
- 変更根拠、検証結果、残置理由が artifact または作業結果に残っている。
