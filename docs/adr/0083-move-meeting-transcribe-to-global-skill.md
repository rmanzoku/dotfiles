---
title: "ADR 0083: 会議録音のローカル文字起こしを共通 skill にする"
status: accepted
date: 2026-10-29
worked_at: 2026-10-29 JST
agent_model: "Claude Opus 5.5 (claude-opus-5-5 / Claude Code)"
---

# Context

会議録音を Mac の中で話者つきの文字起こしにするエンジンは、consulting-gates リポジトリの中にだけあった（同リポジトリの ADR-0016）。エンジンは `scripts/meeting-transcribe/` と `.claude/skills/meeting-transcribe/` で、Apple 音声認識（macOS 26 SpeechTranscriber）に sherpa-onnx の話者分離（pyannote segmentation 3.0 ＋ 3D-Speaker CAM++）を組み合わせている。ほかの案件でも同じ録音機材（Soundcore、Recite）を使うので、エンジンをどの案件からも使えるようにしたい、という依頼が consulting-gates のセッションから来た。

governance の観点:

- 複数のリポジトリ・agent・セッションで再利用する。
- 録音の機密境界（通信しない、本文をログに出さない）を守る必要がある。
- 実行に分単位の時間がかかる。

docs や wrapper だけでは、スクリプト一式を各案件へ配れない。そこで、既存の `soundcore-minutes`（ブラウザ操作）とは別に、エンジンを持つ skill を 1 つ追加する。

Recite について観測したこと:

- 録音フォルダにあるのは `mic.m4a` / `system.m4a` / `speakers.json` / `analysis.json` で、文字起こしのテキストは無い。Recite 自身の文字起こしは、アプリの DB（`default.store` の `ZRECORDING.ZTRANSCRIPT`）にある。スキーマは公開されていない。
- `speakers.json` の side=mine には、スピーカーから回り込んだ相手の声が入る。2026-10-29 に実録音 1 本で確かめた（中身は見ず、件数だけ）。自分側の 2 話者のうち 1 人は、mic 認識単位の 92% が system 側の発話中にあった。もう 1 人は 4% だった。
- 前回の手作業では、system 側を sherpa の人数自動で分けたところ、相手が 3 人の会議で話者が混ざった。

# Decision

- publisher skill `skills/meeting-transcribe` を追加する。consulting-gates のスクリプト（`setup.sh` / `run.sh` / `apple_words.swift` / `diarize.py` / `merge.py`）をそのまま移す。変えたのは `run.sh` の出力先の注記だけ。モデルなどの置き場は、これまでどおり `~/.cache/meeting-transcribe/`。
- 入口は 2 つ。どちらも出口は `diarized.txt`。
  - Soundcore: 「共有 → 音声をエクスポート（OGG）」→ `run.sh`。
  - Recite: 録音フォルダ → `recite.sh`。
- `recite.sh` は、`latest` / UUID / パス / 日付で録音フォルダを選ぶ。日付は、フォルダの更新時刻で探す。DB は読まない（スキーマが公開されていないため）。mic と system を別々に Apple 音声認識にかけ、`recite_merge.py` で 1 本の時系列にまとめる。
- 回り込みは、system 側の発話中にある mic の認識単位を捨てることで除く。side=mine は回り込みを含むので、この判定には使わない。
- 話者ラベルの既定は speakers.json の speakerKey とする。`sherpa` を選ぶと、各側を sherpa で人数自動に分ける。既定を speakerKey にした根拠は、sherpa で相手 3 人が混ざったという観測だけで、speakerKey の精度は確かめていない。
- `soundcore-minutes` の主経路を音声のエクスポートに替える。既に生成された Soundcore の文字起こしを読む手順は、副経路として残す。ブラウザの選び方と 1Password の知見は変えない。
- 補正辞書、raw / sanitized の置き場、議事録の書き方は案件ごとに違うので、案件側（consulting-gates など）に残す。

# Consequences

- 案件側の skill は、`~/.claude/skills/meeting-transcribe/scripts/` を呼ぶ薄い形にできる。consulting-gates 側の書き換えは、そのリポジトリのセッションが行う。
- 新しいマシンでは、install のあとに `setup.sh` を 1 回実行する（manifest に記載）。
- 同時に話した部分の自分の発言は、回り込みと一緒に捨てられる。

# Validation

- 合成音声（`say` の Kyoko / Eddy / Flo）で `run.sh` を通した。話者数 3 なら 3 人に正しく分かれた。人数自動（0）では、合成音声どうしが似ているため 1 人にまとまった。
- 合成音声で作ったフィクスチャ（回り込みを -20 dB で混ぜた mic、system、speakers.json）で、`recite.sh` を recite / sherpa の両方で通した。回り込みは捨てられ、4 発言が時系列順に並んだ。日付の選択で 0 件のときは exit 1、2 件のときは exit 3 になることも確かめた。
- 実録音 1 本で `recite.sh` が最後まで動くこと（約 17 秒）と、上の件数統計を確かめた。出力は件数だけを見て、すぐ消した。
- `scripts/skill-quick-validate` と `scripts/instruction-gc` を通した。
