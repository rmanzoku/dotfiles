# sherpa-onnx で話者分離する（Mac の中だけで動く。モデルは setup.sh で取得済みのものを読む）。
# 使い方: diarize.py <16kHzモノラルwav> <out.tsv> [話者数=2]   （列: 開始秒 / 終了秒 / 話者番号）
#   話者数に 0 を渡すと人数を指定せず、声の近さ（しきい値 1.0）で分ける。参加者数が分からない会議用（2026-10-28: 45分・6人前後の会議で 0.5 は約240人、0.8 は約20人、1.2 は2人に分かれ、1.0 が実態に近かった）
# 構成: pyannote segmentation 3.0 ＋ 3D-Speaker CAM++（zh_en common advanced）。
#   2026-10-28 の実験で ERes2Net（zh-cn）は日本語の2人を分けられなかったため使わない。
import os, sys, time, wave
import numpy as np
import sherpa_onnx

M = os.environ.get("MEETING_TRANSCRIBE_HOME", os.path.expanduser("~/.cache/meeting-transcribe")) + "/models/"
SEG = M + "sherpa-onnx-pyannote-segmentation-3-0/model.onnx"
EMB = M + "3dspeaker_speech_campplus_sv_zh_en_16k-common_advanced.onnx"

wav, out = sys.argv[1], sys.argv[2]
n = int(sys.argv[3]) if len(sys.argv) > 3 else 2
w = wave.open(wav)
assert w.getframerate() == 16000 and w.getnchannels() == 1 and w.getsampwidth() == 2, "16kHz mono 16bit wav が必要"
x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768

cfg = sherpa_onnx.OfflineSpeakerDiarizationConfig(
    segmentation=sherpa_onnx.OfflineSpeakerSegmentationModelConfig(
        pyannote=sherpa_onnx.OfflineSpeakerSegmentationPyannoteModelConfig(model=SEG), num_threads=4),
    embedding=sherpa_onnx.SpeakerEmbeddingExtractorConfig(model=EMB, num_threads=4),
    clustering=sherpa_onnx.FastClusteringConfig(num_clusters=n) if n > 0 else sherpa_onnx.FastClusteringConfig(num_clusters=-1, threshold=1.0),
    min_duration_on=0.2, min_duration_off=0.3)


def progress(done, total, *_):
    if done % 50 == 0:
        print(f"[diarize] progress {done}/{total}", file=sys.stderr, flush=True)
    return 0


print(f"[diarize] start audio={len(x) / 16000:.0f}s speakers={n}", file=sys.stderr, flush=True)
t = time.time()
r = sherpa_onnx.OfflineSpeakerDiarization(cfg).process(x, callback=progress).sort_by_start_time()
with open(out, "w") as f:
    for s in r:
        f.write(f"{s.start:.2f}\t{s.end:.2f}\t{s.speaker}\n")
print(f"[diarize] done segments={len(r)} elapsed={time.time() - t:.0f}s", file=sys.stderr, flush=True)
