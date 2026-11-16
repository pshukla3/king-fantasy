import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import r2_score
from scipy.stats import spearmanr

D = pd.read_parquet("features.parquet")
g = D.groupby(["k", "season"])
for c, out in (("wopr", "r3_wopr"),
               ("air_yards_share", "r3_ays"),
               ("target_share", "r3_ts"),
               ("receiving_air_yards", "r3_ay")):
    if c in D.columns:
        D[c] = pd.to_numeric(D[c], errors="coerce")
        D[out] = g[c].transform(
            lambda x: x.shift(1).rolling(
                3, min_periods=1).mean())

FE = ["r3_fp", "r8_fp", "prev_fp", "py_fp", "r3_tgt",
      "r3_car", "r3_snap", "r3_tgts", "r3_cars",
      "r8_snap", "opp_allow", "gm_no",
      "r3_wopr", "r3_ays", "r3_ts", "r3_ay"]
FE = [c for c in FE if c in D.columns]
for p in ("QB", "RB", "WR", "TE"):
    D["is_" + p] = (D["position"] == p).astype(int)
    FE.append("is_" + p)

D = D[D["week"] >= 4].copy()
D = D.dropna(subset=["fp"])
print("training rows: %d | features: %d" % (len(D), len(FE)))

def run(test_season):
    tr = D[D["season"] < test_season]
    te = D[D["season"] == test_season]
    if len(tr) < 5000 or len(te) < 500:
        return None
    m = HistGradientBoostingRegressor(
        max_iter=400, learning_rate=0.06,
        max_depth=6, min_samples_leaf=40,
        l2_regularization=1.0, random_state=0)
    m.fit(tr[FE], tr["fp"])
    p = m.predict(te[FE])
    out = {"n": len(te),
           "mae": float(np.abs(p - te["fp"]).mean()),
           "r2": float(r2_score(te["fp"], p)),
           "rho": float(spearmanr(p, te["fp"]).statistic)}
    for base, lab in ((te["r3_fp"], "3-game avg"),
                      (te["py_fp"], "last season"),
                      (te["r8_fp"], "8-game avg")):
        b = base.fillna(te["fp"].mean())
        out[lab] = float(np.abs(b - te["fp"]).mean())
    return out, m

print("\n%-6s %6s %7s %7s %7s %9s %9s"
      % ("YEAR", "N", "MODEL", "3-GAME", "LASTYR",
         "R2", "RANK-r"))
acc = []
last = None
for s in range(2020, 2026):
    r = run(s)
    if not r:
        continue
    o, m = r
    last = m
    acc.append(o)
    print("%-6d %6d %7.3f %7.3f %7.3f %9.3f %9.3f"
          % (s, o["n"], o["mae"], o["3-game avg"],
             o["last season"], o["r2"], o["rho"]))

print("\nMEAN   model %.3f | 3-game %.3f | last yr %.3f"
      % (np.mean([o["mae"] for o in acc]),
         np.mean([o["3-game avg"] for o in acc]),
         np.mean([o["last season"] for o in acc])))
print("MEAN   R2 %.3f | rank corr %.3f"
      % (np.mean([o["r2"] for o in acc]),
         np.mean([o["rho"] for o in acc])))

if last is not None:
    try:
        from sklearn.inspection import permutation_importance
        te = D[D["season"] == 2025].sample(
            min(4000, len(D[D["season"] == 2025])),
            random_state=0)
        pi = permutation_importance(
            last, te[FE], te["fp"], n_repeats=3,
            random_state=0, scoring="neg_mean_absolute_error")
        idx = np.argsort(-pi.importances_mean)[:10]
        print("\n=== WHAT THE MODEL ACTUALLY USES ===")
        for i in idx:
            print("  %-12s %.4f" % (FE[i],
                                    pi.importances_mean[i]))
    except Exception as e:
        print("importance skipped:", str(e)[:50])
