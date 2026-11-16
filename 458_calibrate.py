import numpy as np, pandas as pd, json

# Regress actual on projected per position. Slope < 1
# means we are over-dispersed: our spread is wider than
# our skill justifies, so predictions should be pulled
# toward the positional mean.
import subprocess, sys, os
if not os.path.exists("posbias.json"):
    print("run 457_posbias.py first"); sys.exit(1)

# rebuild the same frame 457 used, but keep the pairs
exec(open("457_posbias.py").read().split(
    'R = pd.DataFrame(rows)')[0])
R = pd.DataFrame(rows)

CAL = {}
print("  %-4s %7s %7s %8s %8s %9s"
      % ("POS", "SLOPE", "INTCPT", "SD PROJ", "SD ACT", "r"))
for pos, s in R.groupby("pos"):
    x, y = s["proj"].values, s["act"].values
    sl, ic = np.polyfit(x, y, 1)
    r = np.corrcoef(x, y)[0, 1]
    CAL[pos] = {"slope": float(sl), "intercept": float(ic),
                "r": float(r), "mean": float(y.mean())}
    print("  %-4s %7.3f %7.3f %8.2f %8.2f %9.3f"
          % (pos, sl, ic, x.std(), y.std(), r))

print("\n  what this does to a projection:")
for pos in ("QB", "RB", "WR", "TE"):
    c = CAL[pos]
    for v in (10, 15, 20, 25):
        print("    %-3s raw %4.1f -> calibrated %5.1f"
              % (pos, v, c["slope"] * v + c["intercept"]))
    print()

json.dump(CAL, open("calibration.json", "w"), indent=1)
print("wrote calibration.json")
