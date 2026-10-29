#!/usr/bin/env bash
# Recite（com.dhizume.Recite）の録音フォルダ1つを、話者つきの1本の文字起こしにする（Mac の中だけで動き、通信しない）。
# 録音フォルダ: mic.m4a（自分側。相手の声も回り込む）/ system.m4a（相手側）/ speakers.json（side=mine|others の話者区間）。
# 使い方:
#   recite.sh list [件数=10]                        録音フォルダを新しい順に並べる（UUID / フォルダ更新時刻 / 長さ）
#   recite.sh <latest|UUID|フォルダのパス|YYYY-MM-DD> <出力ディレクトリ> [recite|sherpa]
#     日付指定はフォルダ更新時刻（録音終了時刻）の日付で探し、2件以上あれば候補を出して止まる（exit 3）。
#     話者ラベル: recite（既定）= speakers.json の話者キー（自分側A / 相手A …）、sherpa = 各側を sherpa-onnx で人数自動の話者分離。
# 出力: mic.words.tsv / system.words.tsv（Apple の認識単位）/ [sherpa のとき mic.segments.tsv / system.segments.tsv] / diarized.txt
# 録音フォルダの置き場は RECITE_RECORDINGS で差し替えられる（テスト用フィクスチャなど）。
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
H="${MEETING_TRANSCRIBE_HOME:-$HOME/.cache/meeting-transcribe}"
REC="${RECITE_RECORDINGS:-$HOME/Library/Containers/com.dhizume.Recite/Data/Library/Application Support/Recite/Recordings}"
log() { echo "[recite $(date +%T)] $*" >&2; }
usage() { echo "usage: recite.sh list [N] | recite.sh <latest|UUID|path|YYYY-MM-DD> <outdir> [recite|sherpa]" >&2; exit 2; }
[ -d "$REC" ] || { log "録音フォルダの置き場が無い: $REC"; exit 1; }

# 新しい順に「更新時刻<TAB>フォルダ名」を出す（speakers.json があるフォルダだけ）
folders() {
  for d in "$REC"/*/; do
    [ -f "$d/speakers.json" ] || continue
    printf '%s\t%s\n' "$(stat -f '%Sm' -t '%Y-%m-%d %H:%M' "$d")" "$(basename "$d")"
  done | sort -r
}

[ $# -ge 1 ] || usage
if [ "$1" = list ]; then
  folders | head -n "${2:-10}" | while IFS=$'\t' read -r t u; do
    printf '%s\t%s\t%ss\n' "$u" "$t" "$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$REC/$u/mic.m4a" 2>/dev/null | cut -d. -f1)"
  done
  exit 0
fi

[ $# -ge 2 ] || usage
SEL="$1"; OUT="$2"; MODE="${3:-recite}"
case "$MODE" in recite|sherpa) ;; *) usage ;; esac
if [ -d "$SEL" ]; then
  DIR="${SEL%/}"
elif [ "$SEL" = latest ]; then
  DIR="$REC/$(folders | head -n1 | cut -f2)"
elif [[ "$SEL" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]]; then
  hits="$(folders | awk -F'\t' -v d="$SEL" 'index($1, d) == 1')"
  n="$(printf '%s' "$hits" | grep -c . || true)"
  [ "$n" -ge 1 ] || { log "$SEL の録音が無い"; exit 1; }
  [ "$n" -eq 1 ] || { log "$SEL の録音が $n 件ある。UUID で指定する:"; printf '%s\n' "$hits" >&2; exit 3; }
  DIR="$REC/$(printf '%s' "$hits" | cut -f2)"
else
  DIR="$REC/$SEL"
fi
for f in mic.m4a system.m4a speakers.json; do [ -f "$DIR/$f" ] || { log "$DIR に $f が無い"; exit 1; }; done
[ -x "$H/bin/apple_words" ] || { log "setup.sh を先に実行する"; exit 1; }
mkdir -p "$OUT"

log "start recording=$(basename "$DIR") out=$OUT labels=$MODE"
for side in mic system; do
  log "$side: convert"
  ffmpeg -nostdin -loglevel error -y -i "$DIR/$side.m4a" -ar 16000 -ac 1 -c:a pcm_s16le "$OUT/$side.16k.wav"
  log "$side: transcribe (Apple)"
  "$H/bin/apple_words" "$OUT/$side.16k.wav" ja-JP > "$OUT/$side.words.tsv"
  if [ "$MODE" = sherpa ]; then
    log "$side: diarize (sherpa-onnx, 人数自動)"
    "$H/venv/bin/python" -I "$HERE/diarize.py" "$OUT/$side.16k.wav" "$OUT/$side.segments.tsv" 0
  fi
done
"$H/venv/bin/python" -I "$HERE/recite_merge.py" "$DIR/speakers.json" "$OUT" "$MODE"
log "done -> $OUT/diarized.txt"
