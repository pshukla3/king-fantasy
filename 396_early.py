import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import r2_score
from scipy.stats import spearmanr

D = pd.read_parquet("features.parquet")
g = D.groupby(["k", "season"])
for c, out in (("wopr", "r3_wopr"),
               ("air_yards_share", "r3_ays"),
               ("target_share", "r3_ts")):
    if c in D.columns:
        D[c] = pd.to_numeric(D[c], errors="coerce")
        D[out] = g[c].transform(
            lambda x: x.shift(1).rolling(3,
                                         min_periods=1).mean())
FE = ["r3_fp", "r8_fp", "prev_fp", "py_fp", "r3_tgt",
      "r3_car", "r3_snap", "r3_tgts", "r3_cars",
      "r8_snap", "opp_allow", "gm_no", "r3_wopr",
      "r3_ays", "r3_ts"]
FE = [c for c in FE if c in D.columns]
for p in ("QB", "RB", "WR", "TE"):
    D["is_" + p] = (D["position"] == p).astype(int)
    FE.append("is_" + p)

# rest-of-season target: what we actually rank on
D = D.sort_values(["k", "season", "week"])
D["ros"] = (D.groupby(["k", "season"])["fp"]
            .transform(lambda x: x[::-1].shift(1)
                       .expanding().mean()[::-1]))
E = D[(D["week"] >= 2) & D["ros"].notna()
      & D["fp"].notna()].copy()
print("rows with a rest-of-season target: %d" % len(E))

print("\n=== PREDICTING REST OF SEASON, BY WEEK ===")
print("%-6s %6s %8s %8s %8s %8s"
      % ("WEEK", "N", "MODEL", "SEASON", "LASTYR", "RANK-r"))
for wk in (2, 3, 4, 6, 10):
    tr = E[(E["season"] < 2025) & (E["week"] >= 2)]
    te = E[(E["season"] == 2025) & (E["week"] == wk)]
    if len(te) < 100:
        continue
    m = HistGradientBoostingRegressor(
        max_iter=350, learning_rate=0.06, max_depth=6,
        min_samples_leaf=40, l2_regularization=1.0,
        random_state=0)
    m.fit(tr[FE], tr["ros"])
    p = m.predict(te[FE])
    mae = float(np.abs(p - te["ros"]).mean())
    b1 = float(np.abs(te["r3_fp"].fillna(0)
                      - te["ros"]).mean())
    b2 = float(np.abs(te["py_fp"].fillna(
        te["ros"].mean()) - te["ros"]).mean())
    rho = float(spearmanr(p, te["ros"]).statistic)
    print("%-6d %6d %8.3f %8.3f %8.3f %8.3f"
          % (wk, len(te), mae, b1, b2, rho))

tr = E[E["season"] < 2026]
M = HistGradientBoostingRegressor(
    max_iter=400, learning_rate=0.06, max_depth=6,
    min_samples_leaf=40, l2_regularization=1.0,
    random_state=0).fit(tr[FE], tr["ros"])
import pickle
pickle.dump({"model": M, "features": FE},
            open("ros_model.pkl", "wb"))
print("\nwrote ros_model.pkl (trained on %d rows)"
      % len(tr))
