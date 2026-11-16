import re
import numpy as np
import pandas as pd

def norm(s):
    s = str(s or "").lower()
    s = re.sub(r"\s+(jr|sr|ii|iii|iv)\.?$", "", s)
    s = re.sub(r"[.'`\u2019\-]", "", s)
    return re.sub(r"\s+", " ", s).strip()

W = pd.read_parquet("weekly_all.parquet")
if "season_type" in W.columns:
    W = W[W["season_type"] == "REG"]
W = W[W["position"].isin(["QB", "RB", "WR", "TE"])].copy()
W["k"] = W["player_display_name"].map(norm)
W["fp"] = pd.to_numeric(W["fantasy_points_ppr"],
                        errors="coerce").fillna(0.0)
W = W[W["week"] <= 17]
SEA = (W.groupby(["season", "k", "position"])["fp"]
       .agg(["mean", "count"]).reset_index())
SEA = SEA[SEA["count"] >= 6]
M = {(r["season"], r["k"]): r["mean"]
     for _, r in SEA.iterrows()}
PM = SEA.groupby(["season", "position"])["mean"]\
    .mean().to_dict()

rows = []
for (sea, k), d in W.groupby(["season", "k"]):
    w1 = d[d["week"] == 1]["fp"]
    rest = d[d["week"].between(2, 17)]["fp"]
    if not len(w1) or len(rest) < 6:
        continue
    p1 = M.get((sea - 1, k))
    if p1 is None:
        continue
    p2 = M.get((sea - 2, k))
    p3 = M.get((sea - 3, k))
    hist = [x for x in (p1, p2, p3) if x is not None]
    wts = [0.5, 0.3, 0.2][:len(hist)]
    wts = [x / sum(wts) for x in wts]
    multi = sum(a * b for a, b in zip(hist, wts))
    pos = d["position"].iloc[0]
    pmean = PM.get((sea, pos), 8.0)
    shrunk = (multi * len(hist) + pmean * 1.0) \
        / (len(hist) + 1.0)
    rows.append({"p1": p1, "multi": multi,
                 "shrunk": shrunk,
                 "wk1": float(w1.iloc[0]),
                 "rest": float(rest.mean())})
D = pd.DataFrame(rows)
print("player-seasons: %d" % len(D))

def fit(col):
    X = np.column_stack([D[col], D["wk1"],
                         np.ones(len(D))])
    b = np.linalg.lstsq(X, D["rest"].values,
                        rcond=None)[0]
    lam = b[1] / (b[0] + b[1])
    pred = X.dot(b)
    mae_alone = np.abs(D[col] - D["rest"]).mean()
    return lam, mae_alone, np.abs(pred - D["rest"]).mean()

print("\n%-28s %9s %11s %11s"
      % ("PRIOR USED", "WK1 WT", "MAE ALONE", "MAE +WK1"))
for col, lab in (("p1", "last season only"),
                 ("multi", "3-season weighted"),
                 ("shrunk", "3-season + shrinkage")):
    lam, a, b2 = fit(col)
    print("%-28s %9.3f %11.3f %11.3f" % (lab, lam, a, b2))

print("\nthe better the prior, the less week 1 should "
      "move it.")
