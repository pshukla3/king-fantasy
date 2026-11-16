import json
import math
import numpy as np
import nflreadpy as nfl

def pl(x):
    return x.to_pandas() if hasattr(x, "to_pandas") else x

W = json.load(open("site/_wp.json"))
M = W["mkt"]
def wp(d):
    z = M["intercept"]
    for i, k in enumerate(M["feat"]):
        z += ((d[k] - M["mean"][i]) / M["scale"][i]
              * M["coef"][i])
    return 1.0 / (1.0 + math.exp(-max(-30, min(30, z))))

def pre(sp):
    t = 3600.0
    return wp({"sd_t": 0.0, "expt": math.exp(-4.0),
               "score_differential": 0.0, "t": t,
               "half": t - 1800, "down": 1,
               "ydstogo": 10, "yardline_100": 75,
               "to_diff": 0, "is4": 0,
               "spread_pos": sp})

S = pl(nfl.load_schedules(
    seasons=list(range(2015, 2026))))
S = S[S["result"].notna() & S["spread_line"].notna()]
S = S[S["result"] != 0]
S["hw"] = (S["result"] > 0).astype(int)
print("games %d" % len(S))
print("\n=== PREGAME: MODEL vs REALITY ===")
print("  model at 0-0, 1st and 10, own 25\n")
print("  %-14s %7s %9s %9s %8s"
      % ("home line", "n", "model", "actual", "gap"))
print("  " + "-" * 50)
worst = 0.0
for lo, hi in [(-99, -7), (-6.5, -3.5), (-3, -0.5),
               (0, 0), (0.5, 3), (3.5, 6.5), (7, 99)]:
    d = S[(S["spread_line"] >= lo)
          & (S["spread_line"] <= hi)]
    if len(d) < 40:
        continue
    m = float(np.mean([pre(x) for x
                       in d["spread_line"].values]))
    a = float(d["hw"].mean())
    worst = max(worst, abs(m - a))
    print("  %+5.1f..%+5.1f %7d %9.3f %9.3f %+8.3f"
          % (lo, hi, len(d), m, a, a - m))
print("\n  worst pregame gap: %.3f" % worst)
print("\n  spot checks:")
for s in (-10, -7, -3, 0, 3, 7, 10):
    print("    home %+3d  ->  home wins %.1f%%"
          % (s, 100 * pre(s)))

try:
    W["ot"] = json.load(open("ot_table.json"))
except IOError:
    pass
W["pregame_worst_gap"] = round(worst, 4)
json.dump(W, open("site/_wp.json", "w"), indent=1)
print("\nupdated site/_wp.json with ot + pregame check")
