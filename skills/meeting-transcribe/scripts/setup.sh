#!/usr/bin/env bash
# 議事録の文字起こし（Apple 音声認識＋sherpa-onnx 話者分離）の準備。1回だけ実行する。再実行しても済んだ手順は飛ばす。
# 置き場: $MEETING_TRANSCRIBE_HOME（既定 ~/.cache/meeting-transcribe）。リポジトリには何も書かない。
# 通信するのはここだけ（pip と、k2-fsa 公式リリースからのモデル取得）。run.sh は通信しない。
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
H="${MEETING_TRANSCRIBE_HOME:-$HOME/.cache/meeting-transcribe}"
REL=https://github.com/k2-fsa/sherpa-onnx/releases/download
mkdir -p "$H/bin" "$H/models"
log() { echo "[setup $(date +%T)] $*"; }

log "start home=$H"
command -v ffmpeg >/dev/null || { log "ffmpeg が無い（brew install ffmpeg）"; exit 1; }

if [ ! -x "$H/bin/apple_words" ] || [ "$HERE/apple_words.swift" -nt "$H/bin/apple_words" ]; then
  log "build apple_words（macOS 26 以降・Xcode が要る）"
  swiftc -O "$HERE/apple_words.swift" -o "$H/bin/apple_words"
fi

if [ ! -x "$H/venv/bin/python" ]; then
  log "create venv + pip install sherpa-onnx numpy"
  python3 -m venv "$H/venv"
  "$H/venv/bin/pip" install --quiet sherpa-onnx numpy
fi

if [ ! -f "$H/models/sherpa-onnx-pyannote-segmentation-3-0/model.onnx" ]; then
  log "download segmentation model"
  curl -fsSL --retry 3 -o "$H/models/seg.tar.bz2" "$REL/speaker-segmentation-models/sherpa-onnx-pyannote-segmentation-3-0.tar.bz2"
  tar -xjf "$H/models/seg.tar.bz2" -C "$H/models" && rm "$H/models/seg.tar.bz2"
fi

EMB=3dspeaker_speech_campplus_sv_zh_en_16k-common_advanced.onnx
if [ ! -f "$H/models/$EMB" ]; then
  log "download embedding model"
  curl -fsSL --retry 3 -o "$H/models/$EMB.part" "$REL/speaker-recongition-models/$EMB" && mv "$H/models/$EMB.part" "$H/models/$EMB"
fi
log "done"
