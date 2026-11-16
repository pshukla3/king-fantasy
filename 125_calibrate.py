import sys
import pandas as pd
import numpy as np

# measured in 124_calibration.py, fit on pre-2020
# seasons (8+ games), verified out of sample on 2020+
FIT = {"QB": (8.24, 0.512),
       "RB": (2.44, 0.714),
       "WR": (2.46, 0.746),
       "TE": (2.04, 0.701)}

B = pd.read_csv("board_final.csv", low_memory=False)
print("board rows: %d" % len(B))
if "calibrated" in B.columns:
    print("already calibrated - nothing to do")
    sys.exit(0)

pre = B[["player_display_name", "position", "points",
         "rank"]].copy()
pre = pre.rename(columns={"points": "pp0",
                          "rank": "rk0"})
b0 = pd.to_numeric(B["blend"], errors="coerce")
pts = pd.to_numeric(B["points"], errors="coerce")
eg = pd.to_numeric(B["exp_games"], errors="coerce")
live = (pts > 0) & (eg > 0)

print("\n=== APPLYING SHRINKAGE ===")
hit = skip = 0
for p, (a, b) in FIT.items():
    ip = B["position"] == p
    m = ip & live
    n = int(m.sum())
    s = int((ip & ~live).sum())
    hit += n
    skip += s
    B.loc[m, "points"] = a + b * B.loc[m, "points"]
    B.loc[m, "vorp"] = b * B.loc[m, "vorp"]
    B.loc[m, "value"] = b * B.loc[m, "value"]
    print("  %-4s %4d scaled x%.3f, %2d skipped (zero proj)"
          % (p, n, b, s))
print("  total %d scaled, %d left alone" % (hit, skip))

v = B["value"].notna() & (B["points"].fillna(0) > 0.01)
_z = ~v
B["model_rank"] = np.nan
B.loc[v, "model_rank"] = B.loc[v, "value"].rank(
    ascending=False, method="min")
_nl = int(v.sum())
if _z.any():
    B.loc[_z, "model_rank"] = _nl + B.loc[_z, "value"].rank(
        ascending=False, method="min").fillna(1.0)
    print("pushed %d zero-projection players below the "
          "%d live players" % (int(_z.sum()), _nl))
mr = B["model_rank"]
mk = pd.to_numeric(B["market_rank"], errors="coerce")
nb = np.where(mk.notna(), (mr + mk) / 2.0, mr)
nb = np.where(_z.values, mr.values, nb)
B["blend"] = np.where(mr.notna(), nb, b0)
print("rows keeping their old blend: %d" % int(mr.isna().sum()))
B["blend"] = B["blend"].fillna(b0.max() + 1)

B = B.sort_values("blend").reset_index(drop=True)
B["rank"] = B.index + 1
B["pos_rank"] = B.groupby("position")["blend"].rank(
    method="min").astype(int)
B["calibrated"] = 1
B.to_csv("board_final.csv", index=False)
print("re-ranked and saved")

M = B.merge(pre, on=["player_display_name", "position"],
            how="left")
M["shift"] = M["rk0"] - M["rank"]
C = ["rank", "rk0", "shift", "player_display_name",
     "position", "team", "pp0", "points"]
q = M[(M["rk0"] <= 130) & (M["pp0"] > 0)]
print("\n=== RISERS (top 130, real projections only) ===")
print(q.nlargest(10, "shift")[C].round(2)
      .to_string(index=False))
print("\n=== FALLERS ===")
print(q.nsmallest(10, "shift")[C].round(2)
      .to_string(index=False))
zero = int((M["pp0"].fillna(0) == 0).sum())
print("\nzero-projection rows left untouched: %d" % zero)
