# Apple の認識単位ごとに、時間が一番重なる話者を付け、同じ話者の連続を1発言にまとめる。
# 使い方: merge.py <words.tsv> <segments.tsv> <out.txt>   （出力: 「[hh:mm:ss-hh:mm:ss] 話者N: 本文」）
import sys

words_f, seg_f, out_f = sys.argv[1:4]
segs = [(float(a), float(b), int(c)) for a, b, c in (l.rstrip("\n").split("\t") for l in open(seg_f) if l.strip())]
words = [(float(a), float(b), t.rstrip("\n")) for a, b, t in (l.split("\t", 2) for l in open(words_f) if l.strip())]


def hms(s):
    s = int(s)
    return "%02d:%02d:%02d" % (s // 3600, s // 60 % 60, s % 60)


def speaker(a, b):
    o = {}
    for s, e, k in segs:
        if s >= b:
            break
        v = min(b, e) - max(a, s)
        if v > 0:
            o[k] = o.get(k, 0) + v
    if o:
        return max(o, key=o.get)
    m = (a + b) / 2  # 重なりが無ければ一番近い区間の話者
    return min(segs, key=lambda x: 0 if x[0] <= m <= x[1] else min(abs(m - x[0]), abs(m - x[1])))[2]


runs = []
for a, b, t in words:
    k = speaker(a, b)
    if runs and runs[-1][2] == k:
        runs[-1][1] = b
        runs[-1][3] += t
    else:
        runs.append([a, b, k, t])
with open(out_f, "w") as f:
    for a, b, k, t in runs:
        f.write(f"[{hms(a)}-{hms(b)}] 話者{k}: {t}\n")
print(f"[merge] turns={len(runs)} -> {out_f}", file=sys.stderr)
