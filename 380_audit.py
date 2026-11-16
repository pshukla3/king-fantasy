import json
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

D = pd.DataFrame(json.load(open("site/_wk1.json"))["rows"])
D = D[D["proj"].notna() & D["act"].notna()].copy()
print("=== WEEK 1 PREDICTION AUDIT: %d players ===" % len(D))

def blk(d, lab):
    if len(d) < 8:
        return
    mae = d["err"].abs().mean()
    bias = d["err"].mean()
    r = np.corrcoef(d["proj"], d["act"])[0, 1]
    rho = spearmanr(d["proj"], d["act"]).statistic
    print("  %-18s n=%-4d MAE %5.2f bias %+5.2f "
          "r %.3f rank-r %.3f"
          % (lab, len(d), mae, bias, r, rho))

print("\n--- OVERALL ---")
blk(D, "all")
print("\n--- BY POSITION ---")
for p in ("QB", "RB", "WR", "TE", "K", "DST"):
    blk(D[D["pos"] == p], p)

print("\n--- BY PROJECTION TIER ---")
D = D.sort_values("proj", ascending=False)
for lo, hi, lab in ((0, 24, "top 24 projected"),
                    (24, 60, "25-60"),
                    (60, 120, "61-120"),
                    (120, 9999, "121+")):
    blk(D.iloc[lo:hi], lab)

print("\n--- CALIBRATION: do projections mean anything? ---")
D["bucket"] = pd.cut(D["proj"], [0, 5, 8, 11, 14, 18, 99])
g = D.groupby("bucket", observed=True).agg(
    n=("act", "size"), proj=("proj", "mean"),
    act=("act", "mean"))
print(g.round(2).to_string())

print("\n--- HIT RATES ---")
for k in (12, 24, 36):
    top_p = set(D.nlargest(k, "proj")["n"])
    top_a = set(D.nlargest(k, "act")["n"])
    print("  top %-3d projected that finished top %-3d: "
          "%d of %d (%.0f%%)"
          % (k, k, len(top_p & top_a), k,
             100 * len(top_p & top_a) / k))

print("\n--- BIGGEST MISSES BY SIZE ---")
z = D.reindex(D["err"].abs().sort_values(
    ascending=False).index)
print("%-24s %-4s %6s %6s %7s"
      % ("PLAYER", "POS", "PROJ", "ACT", "ERR"))
for _, r in z.head(12).iterrows():
    print("%-24s %-4s %6.1f %6.1f %+7.1f"
          % (r["n"][:24], r["pos"], r["proj"], r["act"],
             r["err"]))

print("\n--- HOW MUCH OF THE ERROR IS UNAVOIDABLE? ---")
sd = D["act"].std()
print("  spread of actual scores (sd)   : %.2f" % sd)
print("  our MAE                        : %.2f"
      % D["err"].abs().mean())
print("  MAE if we predicted the mean   : %.2f"
      % (D["act"] - D["act"].mean()).abs().mean())
print("  MAE if we predicted position mean: %.2f"
      % D.groupby("pos")["act"].transform(
          lambda x: (x - x.mean()).abs()).mean())
