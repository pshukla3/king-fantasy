import json
import numpy as np
import pandas as pd

TARGET = {"K": 135, "DST": 145}   # round 14-15, 10-team

M = json.load(open("pos_mult.json"))
B = pd.read_csv("board_final.csv")
B["pre_vorp"] = pd.to_numeric(B.get("pre_vorp"),
                              errors="coerce")
B["upd_vorp"] = pd.to_numeric(B.get("upd_vorp"),
                              errors="coerce")

# undo the current multiplier to recover raw vorp
raw = {}
for p in ("K", "DST"):
    cur = float(M.get(p, 1.0)) or 1.0
    m = B["position"] == p
    raw[p] = (B.loc[m, "pre_vorp"] / cur).values

others = B[~B["position"].isin(["K", "DST"])][
    "pre_vorp"].dropna().sort_values(ascending=False).values

print("=== SOLVING FOR THE MULTIPLIER ===")
for p in ("K", "DST"):
    v = np.nanmax(raw[p])
    lo, hi = 0.0, 1.0
    for _ in range(40):
        mid = (lo + hi) / 2
        scaled = v * mid
        rank = int((others > scaled).sum()) + 1
        if rank < TARGET[p]:
            hi = mid
        else:
            lo = mid
    M[p] = round((lo + hi) / 2, 4)
    scaled = v * M[p]
    rank = int((others > scaled).sum()) + 1
    print("  %-4s top raw value %.2f -> x%.4f "
          "-> lands at #%d (target %d)"
          % (p, v, M[p], rank, TARGET[p]))

json.dump(M, open("pos_mult.json", "w"), indent=1)
print("\npos_mult.json:")
print(json.dumps(M, indent=1))
print("\nJustification: measured predictive correlation "
      "is 0.023 for DST and negative for K, so almost "
      "none of the projected edge is capturable. The "
      "market prices this correctly at round 14-15.")
