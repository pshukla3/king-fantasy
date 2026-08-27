import pandas as pd
import numpy as np

P = pd.read_csv("wr_pairs.csv")
P = P.dropna(subset=["ppg", "tpg", "ppg_n"])
P = P[P["tpg"] > 0].copy()
P["eff"] = P["ppg"] / P["tpg"]

yrs = sorted(P["season"].unique())
cut = yrs[int(len(yrs) * 0.6)]
TR = P[P["season"] < cut].copy()
TE = P[P["season"] >= cut].copy()
print("seasons: %s" % yrs)
print("train < %d  n=%d" % (cut, len(TR)))
print("test >= %d  n=%d" % (cut, len(TE)))

MT = TR["tpg"].mean()
ME = TR["eff"].mean()
print("train mean: %.2f tgt/g, %.3f pts/tgt" % (MT, ME))

def proj(d, kt, ke):
    t = MT + kt * (d["tpg"] - MT)
    e = ME + ke * (d["eff"] - ME)
    return t * e

best = (0.0, 0.0, -1.0)
for i in range(21):
    for j in range(21):
        kt = i / 20.0
        ke = j / 20.0
        r = proj(TR, kt, ke).corr(TR["ppg_n"])
        if r > best[2]:
            best = (kt, ke, r)
kt, ke, rtr = best

print("\n=== FITTED ON TRAIN SEASONS ===")
print("  keep %.2f of his target volume" % kt)
print("  keep %.2f of his efficiency edge" % ke)
print("  train r %.3f" % rtr)

print("\n=== OUT OF SAMPLE (test seasons) ===")
rv = proj(TE, kt, ke).corr(TE["ppg_n"])
rraw = TE["ppg"].corr(TE["ppg_n"])
print("  volume x regressed eff   r %.3f" % rv)
print("  raw ppg baseline         r %.3f" % rraw)
print("  improvement              %+.3f" % (rv - rraw))

bw, br = 0.0, -1.0
for i in range(21):
    w = i / 20.0
    b = w * proj(TR, kt, ke) + (1 - w) * TR["ppg"]
    r = b.corr(TR["ppg_n"])
    if r > br:
        bw, br = w, r
bt = bw * proj(TE, kt, ke) + (1 - bw) * TE["ppg"]
rb = bt.corr(TE["ppg_n"])

print("\n=== BLEND OF BOTH ===")
print("  best weight on volume model %.2f" % bw)
print("  train r %.3f | test r %.3f" % (br, rb))

print("\n=== DECISION ===")
gain = max(rv, rb) - rraw
print("  best test r %.3f vs baseline %.3f  (%+.3f)"
      % (max(rv, rb), rraw, gain))
if gain > 0.01:
    print("  ADOPT: rebuild WR projections on this")
else:
    print("  REJECT: not worth the complexity")
