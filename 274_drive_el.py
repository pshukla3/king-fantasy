import numpy as np
import pandas as pd

D = pd.read_csv("drive_pool.csv")
print("in: %d drives | old secs/drive %.0f"
      % (len(D), D["el"].mean()))
print("   old seconds accounted per game %.0f"
      % (D.groupby("gid")["el"].sum().mean()))

D = D.sort_values(["gid", "t0"], ascending=[True, False])
nt = D.groupby("gid")["t0"].shift(-1)
D["el"] = (D["t0"] - nt.fillna(0.0)).clip(lower=0.0)
D["y1"] = D.groupby("gid")["y0"].shift(-1).fillna(75.0)
D = D[D["el"] <= 900]
D.to_csv("drive_pool.csv", index=False)

g = D.groupby("gid")["el"].sum()
print("\nout: %d drives" % len(D))
print("  secs/drive        %.0f   (expect ~163)"
      % D["el"].mean())
print("  secs per game     %.0f  (MUST be ~3600)"
      % g.mean())
print("  games under 3400s %d of %d"
      % (int((g < 3400).sum()), len(g)))
print("  zero-length drives %d  (MUST be near 0)"
      % int((D["el"] <= 0).sum()))
print("  pts/drive %.3f | start yl %.1f"
      % (D["op"].mean(), D["y0"].mean()))

print("\n  UP 1-8, by time left (kneels should")
print("  now burn the clock, not freeze it):")
u = D[(D["sd"] > 0) & (D["sd"] < 8.5)]
for lo, hi in [(0, 15), (16, 40), (41, 90),
               (91, 180), (181, 420)]:
    k = u[(u["t0"] >= lo) & (u["t0"] <= hi)]
    if len(k):
        print("    %3d-%-4ds n=%5d  pts %.2f  secs %3.0f"
              % (lo, hi, len(k), k["op"].mean(),
                 k["el"].mean()))
