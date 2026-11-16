import numpy as np
import pandas as pd

W = pd.read_pickle("matchup_weekly.pkl")
PC = [c for c in W.columns
      if c.startswith("fantasy_points")][0]
print("weekly rows: %d | points col: %s" % (len(W), PC))

W = W[W["base"] > 3].copy()
W["shock"] = W[PC] / W["base"]
W = W[W["shock"].between(-0.5, 6.0)]

print("\n=== EMPIRICAL WEEKLY SHOCK BY POSITION ===")
print("  weekly points / that player's season average\n")
print("  %-4s %7s %6s %6s %6s %6s %6s"
      % ("pos", "n", "mean", "sd", "p10", "p50", "p90"))
SH = {}
for p in ["QB", "RB", "WR", "TE"]:
    d = W[W["position"] == p]["shock"].values
    if len(d) < 500:
        continue
    SH[p] = d
    print("  %-4s %7d %6.2f %6.2f %6.2f %6.2f %6.2f"
          % (p, len(d), d.mean(), d.std(),
             np.percentile(d, 10),
             np.percentile(d, 50),
             np.percentile(d, 90)))

np.save("shock_pool.npy",
        np.array([len(SH[k]) for k in sorted(SH)]))
import pickle
pickle.dump(SH, open("shocks.pkl", "wb"))
print("\n  saved shocks.pkl (%d positions)" % len(SH))
print("  note: mean is ~1.0 by construction;")
print("  the SPREAD is what we are after")
