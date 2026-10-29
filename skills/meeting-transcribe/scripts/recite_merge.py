# Recite の mic / system それぞれの Apple 認識単位に話者を付け、1本の時系列にまとめる。
# 使い方: recite_merge.py <speakers.json> <出力ディレクトリ> <recite|sherpa>
#   入力: <出力ディレクトリ>/{mic,system}.words.tsv、sherpa のときは {mic,system}.segments.tsv
#   出力: <出力ディレクトリ>/diarized.txt（「[hh:mm:ss-hh:mm:ss] 話者ラベル: 本文」）
# 規則:
#   - 自分の発話は mic 側、相手の発話は system 側を正とする。mic の認識単位は、中央の時刻が system 側の発話中
#     （system の認識単位を 0.5 秒未満の隙間でつないだ区間）にあれば捨てる（スピーカーからの回り込み）。system 側は捨てない。
#     speakers.json の side=mine は回り込みを含むので、この判定には使わない（2026-10-29 実録音1本で、自分側の
#     2話者の片方は mic 認識単位の 92% が system の発話中にあり、もう片方は 4% だった）。
#   - ラベルは recite なら speakers.json の speakerKey、sherpa なら「自分側N」「相手N」（N は各側の sherpa の番号）。
#   - 同じラベルの認識単位が 1.5 秒以内に続く間を1発言にまとめ、両側の発言を開始時刻の順に並べる。
# ログには件数だけを出し、本文は出さない。
import bisect, json, sys

spk_f, out, mode = sys.argv[1:4]
GAP = 1.5
spans = json.load(open(spk_f))["spans"]
side_spans = {s: sorted((float(x["start"]), float(x["end"]), x["speakerKey"]) for x in spans if x["side"] == s) for s in ("mine", "others")}


def load_words(path):
    return [(float(a), float(b), t.rstrip("\n")) for a, b, t in (l.split("\t", 2) for l in open(path) if l.strip())]


def load_segs(path, prefix):
    return [(float(a), float(b), f"{prefix}{int(c) + 1}") for a, b, c in (l.rstrip("\n").split("\t") for l in open(path) if l.strip())]


def best(a, b, segs):
    o = {}
    for s, e, k in segs:
        if s >= b:
            break
        v = min(b, e) - max(a, s)
        if v > 0:
            o[k] = o.get(k, 0) + v
    if o:
        return max(o, key=o.get)
    if not segs:
        return None
    m = (a + b) / 2  # 重なりが無ければ一番近い区間のラベル
    return min(segs, key=lambda x: min(abs(m - x[0]), abs(m - x[1])))[2]


def activity(words, join=0.5):
    act = []
    for a, b, _ in words:
        if act and a - act[-1][1] < join:
            act[-1][1] = b
        else:
            act.append([a, b])
    return act


def inside(m, act, starts):
    i = bisect.bisect_right(starts, m) - 1
    return i >= 0 and act[i][0] <= m <= act[i][1]


def hms(s):
    s = int(s)
    return "%02d:%02d:%02d" % (s // 3600, s // 60 % 60, s % 60)


turns, stats = [], {}
system_act = activity(load_words(f"{out}/system.words.tsv"))
system_starts = [x[0] for x in system_act]
for side, rside, prefix in (("mic", "mine", "自分側"), ("system", "others", "相手")):
    words = load_words(f"{out}/{side}.words.tsv")
    labels = side_spans[rside] if mode == "recite" else sorted(load_segs(f"{out}/{side}.segments.tsv", prefix))
    kept = dropped = 0
    runs = []
    for a, b, t in words:
        if side == "mic" and inside((a + b) / 2, system_act, system_starts):
            dropped += 1
            continue
        k = best(a, b, labels) or prefix
        kept += 1
        if runs and runs[-1][2] == k and a - runs[-1][1] <= GAP:
            runs[-1][1] = b
            runs[-1][3] += t
        else:
            runs.append([a, b, k, t])
    turns += runs
    stats[side] = f"units={len(words)} kept={kept} dropped={dropped} turns={len(runs)}"

turns.sort(key=lambda r: r[0])
with open(f"{out}/diarized.txt", "w") as f:
    for a, b, k, t in turns:
        f.write(f"[{hms(a)}-{hms(b)}] {k}: {t}\n")
print(f"[recite_merge] labels={mode} " + " ".join(f"{k}({v})" for k, v in stats.items()) + f" -> {out}/diarized.txt", file=sys.stderr)
