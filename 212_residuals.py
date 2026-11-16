import numpy as np
import pandas as pd
from sklearn.linear_model import RidgeCV
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler

D = pd.read_csv("pos_pairs.csv", low_memory=False)

WIN = {
    "RB": ["ppg", "cpg", "tpg", "car_share", "opp_share",
           "ypc", "rtdr", "ctch", "age", "draft_pick",
           "moved", "n_cpg", "g"],
    "WR": ["ppg", "tpg", "tar_share", "ctch", "ypr", "tdr",
           "ay_share", "age", "draft_pick", "moved",
           "n_tpg", "g"],
    "TE": ["ppg", "tpg", "age", "ay_share", "draft_pick",
           "moved"],
}
TESTS = [2021, 2022, 2023, 2024, 2025]

def ridge():
    return Pipeline([
        ("i", SimpleImputer(strategy="median")),
        ("s", StandardScaler()),
        ("m", RidgeCV(alphas=np.logspace(-2, 3, 24)))])

rows = []
for p, cols in WIN.items():
    d = D[D["position"] == p]
    for T in TESTS:
        tr = d[d["label_season"] < T]
        te = d[d["label_season"] == T]
        if len(te) < 25 or len(tr) < 150:
            continue
        m = ridge().fit(tr[cols].values, tr["y"].values)
        pr = m.predict(te[cols].values)
        for q, (a, b) in enumerate(zip(pr, te["y"].values)):
            rows.append({"pos": p, "yr": T,
                         "pid": te["player_id"].values[q],
                         "pred": float(a), "act": float(b),
                         "res": float(b - a)})

R = pd.DataFrame(rows)
R.to_csv("model_residuals.csv", index=False)
print("out-of-sample predictions collected: %d" % len(R))
print(R.groupby("pos").size().to_string())
print("\n  %-4s %8s %8s %8s" % ("pos", "bias", "sd", "MAE"))
for p in ["RB", "WR", "TE"]:
    d = R[R["pos"] == p]
    print("  %-4s %+8.3f %8.3f %8.3f"
          % (p, d["res"].mean(), d["res"].std(),
             d["res"].abs().mean()))
print("\n  bias near zero = the model is not")
print("  systematically over- or under-shooting")

print("\n  213_resid_shape.py fits the sd curve and\n  writes resid_pool.npz - this script only\n  produces model_residuals.csv")
