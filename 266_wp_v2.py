import json
import math
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import log_loss

D = pd.read_csv("wp_train.csv")
D["sp_t"] = D["spread_pos"] * (D["t"] / 3600.0)
print("plays %d" % len(D))

STATE = ["sd_t", "expt", "score_differential", "t",
         "half", "down", "ydstogo", "yardline_100",
         "to_diff", "is4"]
MKT = STATE + ["spread_pos"]
MKT2 = MKT + ["sp_t"]

def lr():
    return Pipeline([("s", StandardScaler()),
                     ("m", LogisticRegression(
                         max_iter=3000))])

print("\n=== WALK-FORWARD: DOES THE INTERACTION HELP? ===")
print("  %6s %8s %10s %10s %8s"
      % ("test", "n", "mkt", "mkt+sp_t", "gain"))
print("  " + "-" * 46)
a1, a2 = [], []
for T in [2021, 2022, 2023, 2024, 2025]:
    tr, te = D[D["season"] < T], D[D["season"] == T]
    r = []
    for C in (MKT, MKT2):
        m = lr().fit(tr[C].values, tr["win"].values)
        r.append(log_loss(te["win"].values,
                          m.predict_proba(
                              te[C].values)[:, 1]))
    a1.append(r[0])
    a2.append(r[1])
    print("  %6d %8d %10.4f %10.4f %+7.2f%%"
          % (T, len(te), r[0], r[1],
             100 * (1 - r[1] / r[0])))
print("  " + "-" * 46)
print("  %6s %8s %10.4f %10.4f %+7.2f%%"
      % ("mean", "", np.mean(a1), np.mean(a2),
         100 * (1 - np.mean(a2) / np.mean(a1))))

import nflreadpy as nfl
def pl(x):
    return x.to_pandas() if hasattr(x, "to_pandas") else x

tr = D[D["season"] < 2023]
te = D[D["season"] >= 2023]
FIN = {}
for nm, C in [("mkt", MKT), ("mkt2", MKT2)]:
    m = lr().fit(tr[C].values, tr["win"].values)
    p = m.predict_proba(te[C].values)[:, 1]
    sc, lg = m.named_steps["s"], m.named_steps["m"]
    FIN[nm] = {"feat": C,
               "mean": [float(x) for x in sc.mean_],
               "scale": [float(x) for x in sc.scale_],
               "coef": [float(x) for x in lg.coef_[0]],
               "intercept": float(lg.intercept_[0]),
               "logloss": float(log_loss(
                   te["win"].values, p))}

def pre(M, sp):
    t = 3600.0
    d = {"sd_t": 0.0, "expt": math.exp(-4.0),
         "score_differential": 0.0, "t": t,
         "half": t - 1800, "down": 1, "ydstogo": 10,
         "yardline_100": 75, "to_diff": 0, "is4": 0,
         "spread_pos": sp, "sp_t": sp * 1.0}
    z = M["intercept"]
    for i, k in enumerate(M["feat"]):
        z += ((d[k] - M["mean"][i]) / M["scale"][i]
              * M["coef"][i])
    return 1.0 / (1.0 + math.exp(-max(-30, min(30, z))))

S = pl(nfl.load_schedules(
    seasons=list(range(2015, 2026))))
S = S[S["result"].notna() & S["spread_line"].notna()]
S = S[S["result"] != 0]
S["hw"] = (S["result"] > 0).astype(int)

X = S["spread_line"].values.reshape(-1, 1)
pm = LogisticRegression(max_iter=1000).fit(
    X, S["hw"].values)
def preg(sp):
    z = float(pm.intercept_[0] + pm.coef_[0][0] * sp)
    return 1.0 / (1.0 + math.exp(-max(-30, min(30, z))))

print("\n=== PREGAME CALIBRATION, THREE WAYS ===")
print("  %-13s %6s %8s %8s %8s %8s"
      % ("home line", "n", "actual", "mkt", "mkt2",
         "pure"))
print("  " + "-" * 54)
w = {"mkt": 0.0, "mkt2": 0.0, "pure": 0.0}
for lo, hi in [(-99, -7), (-6.5, -3.5), (-3, -0.5),
               (0, 0), (0.5, 3), (3.5, 6.5), (7, 99)]:
    d = S[(S["spread_line"] >= lo)
          & (S["spread_line"] <= hi)]
    if len(d) < 40:
        continue
    sp = d["spread_line"].values
    a = float(d["hw"].mean())
    v1 = float(np.mean([pre(FIN["mkt"], x) for x in sp]))
    v2 = float(np.mean([pre(FIN["mkt2"], x) for x in sp]))
    v3 = float(np.mean([preg(x) for x in sp]))
    for k, v in (("mkt", v1), ("mkt2", v2), ("pure", v3)):
        w[k] = max(w[k], abs(v - a))
    print("  %+5.1f..%+5.1f %6d %8.3f %8.3f %8.3f %8.3f"
          % (lo, hi, len(d), a, v1, v2, v3))
print("\n  worst gap:  mkt %.3f | mkt2 %.3f | pure %.3f"
      % (w["mkt"], w["mkt2"], w["pure"]))

W = json.load(open("site/_wp.json"))
W["mkt2"] = FIN["mkt2"]
W["pregame"] = {"intercept": float(pm.intercept_[0]),
                "coef": float(pm.coef_[0][0]),
                "games": int(len(S)),
                "worst_gap": round(w["pure"], 4)}
W["pregame_gaps"] = {k: round(v, 4) for k, v in w.items()}
json.dump(W, open("site/_wp.json", "w"), indent=1)
print("\nwrote mkt2 + pregame model to site/_wp.json")
print("\n  pure = logistic on the line alone, 3,018")
print("  games. it cannot be beaten at kickoff because")
print("  that is exactly what it was fit on.")
