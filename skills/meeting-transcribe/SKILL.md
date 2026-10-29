---
name: meeting-transcribe
description: 会議の録音を、この Mac の中だけで話者つきの文字起こし（diarized.txt）にする。Apple 音声認識と sherpa-onnx の話者分離を使い、通信しない。Soundcore からエクスポートした音声ファイルと、Recite の録音フォルダ（mic / system）の両方を扱う。「録音を文字起こしして」「Recite の録音を取り込んで」「Soundcore の音声から議事録を作って」と言われたときに使う。補正辞書、議事録の置き場と書式は案件側のリポジトリが決める。
---

# meeting-transcribe

録音を手元に置き、Mac の中で話者つきの文字起こし `diarized.txt` を作る。ここで扱うのは、どの案件でも同じ部分だけ。補正辞書、raw / sanitized の置き場、議事録の書き方は、作業中のリポジトリの skill や docs に従う。

録音と文字起こしは機密として扱う。本文をチャット、ログ、コミットに出さない。出力先は git 管理外にする（作業リポジトリの `.context/` の下など）。スクリプトのログに出るのは件数と時刻だけ。

## 0. 準備（初回だけ）

```bash
bash ~/.claude/skills/meeting-transcribe/scripts/setup.sh   # Codex では ~/.codex/skills/meeting-transcribe/scripts/setup.sh
```

- 通信するのはこの準備だけ。pip と、k2-fsa 公式リリースからのモデル取得。置き場は `~/.cache/meeting-transcribe/`（`MEETING_TRANSCRIBE_HOME` で変えられる）で、両 agent が共有する。
- 前提: macOS 26 以降、Apple シリコン、Xcode（`swiftc`）、`ffmpeg`。初回の文字起こしでは、Apple の日本語音声データが自動で入る。

以下、`S` は上の `scripts/` ディレクトリを指す。`gh skill install` はスクリプトの実行権限を保たないので、`bash` で呼ぶ。

## 1a. Soundcore の録音

1. Soundcore の Web UI で、録音ページ右上の「共有」→「音声をエクスポート」→ OGG を選ぶ。`~/Downloads/<録音名>.ogg` に保存される。**「生成」（Soundcore の有料文字起こし）は押さない。** ブラウザの選び方と 1Password は `soundcore-minutes` スキルに従う。
2. 保存されたファイルを出力先へ移し、`~/Downloads` に残さない。
3. 話者数が分かっていれば第3引数で渡す（既定は 2）。分からなければ 0 を渡す。0 は声の近さで分けるので、1つの番号に複数人が混ざったり、1人が複数の番号に分かれたりすることがある。

```bash
bash $S/run.sh <out>/audio.ogg <out> 2
```

出力: `audio16k.wav`、`words.tsv`（Apple の認識単位と時刻）、`segments.tsv`（話者分離）、`diarized.txt`（`[hh:mm:ss-hh:mm:ss] 話者N: 本文`）。目安は M4 で 33 分の音声に約 1 分 40 秒。

## 1b. Recite の録音

Recite（`com.dhizume.Recite`）は 1 会議を 1 フォルダ（`~/Library/Containers/com.dhizume.Recite/Data/Library/Application Support/Recite/Recordings/<UUID>/`）に保存する。`mic.m4a` は自分側の音声で、スピーカーから相手の声も回り込む。`system.m4a` は相手側の音声。`speakers.json` には話者区間 `spans[{speakerKey,start,end,side}]` があり、side は mine / others。

1. 対象の録音を決める。`list` は新しい順に、UUID・フォルダ更新時刻（録音の終了時刻）・長さを出す。会議の日時から 1 件に絞れなければ、候補を利用者に見せて選んでもらう。

   ```bash
   bash $S/recite.sh list
   ```

2. 文字起こしする。第1引数は `latest`、UUID、フォルダのパス、`YYYY-MM-DD` のどれか。日付で 2 件以上見つかったときは、候補を出して exit 3 で止まる。

   ```bash
   bash $S/recite.sh latest <out>            # 話者ラベルは speakers.json の speakerKey（既定）
   bash $S/recite.sh <UUID> <out> sherpa     # 各側を sherpa-onnx で話者分離する（人数は自動）
   ```

3. 処理の中身:
   - mic と system を別々に Apple 音声認識にかける。
   - 自分の発話は mic 側を、相手の発話は system 側を正とする。system 側で誰かが話している時刻の mic の認識単位は、回り込みとみなして捨てる。同時に話した部分の自分の発言も、このとき一緒に落ちる。
   - 話者ラベルは、既定（`recite`）では speakers.json の `speakerKey`（`自分側A`、`相手B` など）を時間の重なりで付ける。`sherpa` では `自分側N` / `相手N` になる。
   - 両側の発言を開始時刻の順に並べ、1 本の `diarized.txt` にする。ログには、各側の認識単位の数と、捨てた数・残した数が出る。
4. 既定を `recite` にしているのは、sherpa の人数自動では相手が 3 人いる会議で話者が混ざったためである。speakerKey の精度はまだ確かめていない。どちらのラベルでも、§2 で発言内容から人を割り当てる。

`speakers.json` の side=mine には回り込みが入る。2026-10-29 に実録音 1 本で確かめたところ、自分側の 2 話者のうち 1 人は、mic の認識単位の 92% が system 側の発話中にあった。そのため、回り込みの判定には side を使わない。

Recite 自身の文字起こしは、録音フォルダではなくアプリの DB（`Recite/default.store` の `ZRECORDING.ZTRANSCRIPT`。`[m:ss] 話者キー` の見出しと本文の形）に入っている。スキーマは公開されていない。このスクリプトは DB を読まない。

## 2. 文字起こしのあと（案件側）

`diarized.txt` を作業リポジトリの手順に渡す。補正辞書、話者の割り当て、raw / sanitized の置き場は案件側の skill や docs に従う。どの案件にも共通する注意:

- **話者**: 番号やラベルは録音ごとに変わる。発言内容から人を推定し、確度を書く。決めきれなければ利用者に聞く。
- **数字**: Apple 音声認識は数字を崩しやすい（「60万件」が「6000件」になった例がある）。件数・金額・日付は推測で直さない。時刻をつけて、確認が要る箇所として並べる。
- **相槌**: 2 秒未満の発話は話者の帰属が不正確なので、判断の根拠にしない。
- **固有名詞**: カタカナに寄る。Apple 音声認識に文脈語を渡しても直らなかった（2026-10-28）。補正は AI と人の確認で行う。

## 既知の限界

- 話者分離が Soundcore と一致したのは約 88%。5 秒以上の発言では約 98%、2 秒未満では約 27% だった（2 人の会議 1 本で比較）。
- `run.sh` の話者数 0 は、しきい値 1.0 で分ける。45 分・6 人前後の会議で、実際の人数に近かった値。
- Recite の経路では、mic と system が同じ時刻に始まる前提で突き合わせる。system が mic より短い録音もあった。
- 区間の端では、Apple の時刻のずれで 1〜2 文字が欠けたり混ざったりする。

## 検証

スクリプトを変えたら、合成音声（`say -v Kyoko` など）で `run.sh` と `recite.sh` を 1 回ずつ通す。Recite は `RECITE_RECORDINGS` に、`mic.m4a` / `system.m4a` / `speakers.json` を置いたフィクスチャのフォルダを指定する。実録音は使わない。そのうえで `scripts/skill-quick-validate skills/meeting-transcribe` を実行する。
