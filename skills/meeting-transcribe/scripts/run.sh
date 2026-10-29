#!/usr/bin/env bash
# 録音1本を、話者つきの文字起こしにする（Mac の中だけで動き、通信しない）。事前に setup.sh を1回実行しておく。
# 使い方: run.sh <音声ファイル（ogg/mp3/m4a/wav 等）> <出力ディレクトリ（git 管理外。作業リポジトリの .context/ の下など）> [話者数=2。0 なら人数を指定しない]
# 出力: audio16k.wav / words.tsv（Apple の認識単位と時刻）/ segments.tsv（話者分離）/ diarized.txt（AI 補正の入力）
# 目安（M4・33分の音声）: 文字起こし約15秒＋話者分離約90秒。
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
H="${MEETING_TRANSCRIBE_HOME:-$HOME/.cache/meeting-transcribe}"
[ $# -ge 2 ] || { echo "usage: run.sh <audio> <outdir> [num_speakers]"; exit 2; }
IN="$1"; OUT="$2"; N="${3:-2}"
[ -x "$H/bin/apple_words" ] || { echo "setup.sh を先に実行する"; exit 1; }
mkdir -p "$OUT"
log() { echo "[run $(date +%T)] $*"; }

log "start in=$IN out=$OUT speakers=$N"
ffmpeg -nostdin -loglevel error -y -i "$IN" -ar 16000 -ac 1 -c:a pcm_s16le "$OUT/audio16k.wav"
log "transcribe (Apple)"
"$H/bin/apple_words" "$OUT/audio16k.wav" ja-JP > "$OUT/words.tsv"
log "diarize (sherpa-onnx)"
"$H/venv/bin/python" -I "$HERE/diarize.py" "$OUT/audio16k.wav" "$OUT/segments.tsv" "$N"
"$H/venv/bin/python" -I "$HERE/merge.py" "$OUT/words.tsv" "$OUT/segments.tsv" "$OUT/diarized.txt"
log "done -> $OUT/diarized.txt"
