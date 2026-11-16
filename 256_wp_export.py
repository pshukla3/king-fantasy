import json
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import log_loss, brier_score_loss

D = pd.read_csv("wp_train.csv")
tr = D[D["season"] < 2023]
te = D[D["season"] >= 2023]
print("train %d plays | holdout %d" % (len(tr), len(te)))

STATE = ["sd_t", "expt", "score_differential", "t",
         "half", "down", "ydstogo", "yardline_100",
         "to_diff", "is4"]
MKT = STATE + ["spread_pos"]

def fit(cols, label):
    m = Pipeline([("s", StandardScaler()),
                  ("m", LogisticRegression(
                      max_iter=2000))])
    m.fit(tr[cols].values, tr["win"].values)
    p = m.predict_proba(te[cols].values)[:, 1]
    y = te["win"].values
    ll = log_loss(y, p)
    br = brier_score_loss(y, p)
    worst = 0.0
    rows = []
    for lo in np.arange(0, 1.0, 0.1):
        k = (p >= lo) & (p < lo + 0.1)
        if k.sum() < 200:
            continue
        a, b = float(p[k].mean()), float(y[k].mean())
        worst = max(worst, abs(a - b))
        rows.append((lo, int(k.sum()), a, b))
    print("\n=== %s ===" % label)
    print("  log loss %.4f | brier %.4f | worst gap %.3f"
          % (ll, br, worst))
    for lo, n, a, b in rows:
        print("    %.1f-%.1f %8d  pred %.3f  actual %.3f"
              % (lo, lo + 0.1, n, a, b))
    sc, lg = m.named_steps["s"], m.named_steps["m"]
    return {"feat": cols,
            "mean": [float(x) for x in sc.mean_],
            "scale": [float(x) for x in sc.scale_],
            "coef": [float(x) for x in lg.coef_[0]],
            "intercept": float(lg.intercept_[0]),
            "logloss": float(ll), "brier": float(br),
            "worst_calib_gap": float(worst)}

OUT = {"mkt": fit(MKT, "WITH MARKET SPREAD"),
       "state": fit(STATE, "GAME STATE ONLY"),
       "meta": {"trained": "2015-2022",
                "holdout": "2023-2025",
                "plays": int(len(tr)),
                "games": int(D["game_id"].nunique())}}
json.dump(OUT, open("site/_wp.json", "w"), indent=1)
print("\nwrote site/_wp.json")
print("  market model beats state-only by %.2f%%"
      % (100 * (1 - OUT["mkt"]["logloss"]
                / OUT["state"]["logloss"])))
print("\n  market model coefficients:")
for a, b in sorted(zip(MKT, OUT["mkt"]["coef"]),
                   key=lambda x: -abs(x[1])):
    print("    %-22s %+7.3f" % (a, b))
