import re, glob
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
W = W[W["position"].isin(["RB", "WR", "TE"])].copy()
W["k"] = W["player_display_name"].map(norm)
W["fp"] = pd.to_numeric(W["fantasy_points_ppr"],
                        errors="coerce").fillna(0.0)
W = W[W["week"] <= 17]
for c in ("targets", "carries"):
    if c in W.columns:
        W[c] = pd.to_numeric(W[c], errors="coerce")\
            .fillna(0.0)
    else:
        W[c] = 0.0
W["touch"] = W["targets"] + W["carries"]
print("touch data available:",
      float(W["touch"].sum()) > 0)

S = pd.concat([pd.read_parquet(f) for f in
               sorted(glob.glob("data_usage/snaps_2*.parquet"))],
              ignore_index=True)
S["k"] = S["player"].map(norm)
S["snap"] = pd.to_numeric(S["offense_pct"],
                          errors="coerce")
S1 = S[S["week"] == 1][["season", "k", "snap"]]

rows = []
for (sea, k), d in W.groupby(["season", "k"]):
    w1 = d[d["week"] == 1]
    rest = d[d["week"].between(2, 17)]
    if not len(w1) or len(rest) < 6:
        continue
    pv = W[(W["season"] == sea - 1) & (W["k"] == k)]
    if len(pv) < 6:
        continue
    rows.append({"season": sea, "k": k,
                 "prior": float(pv["fp"].mean()),
                 "ptouch": float(pv["touch"].mean()),
                 "wk1": float(w1["fp"].iloc[0]),
                 "wtouch": float(w1["touch"].iloc[0]),
                 "rest": float(rest["fp"].mean())})
D = pd.DataFrame(rows).merge(S1, on=["season", "k"],
                             how="left")
D = D.dropna(subset=["snap"])
print("player-seasons with usage: %d" % len(D))

def fit(cols, lab):
    X = np.column_stack([D[c] for c in cols]
                        + [np.ones(len(D))])
    b = np.linalg.lstsq(X, D["rest"].values,
                        rcond=None)[0]
    mae = np.abs(X.dot(b) - D["rest"].values).mean()
    print("  %-38s MAE %.4f" % (lab, mae))
    return mae, b

print("\n=== WHAT SHOULD WE UPDATE ON? ===")
fit(["prior"], "prior only")
fit(["prior", "wk1"], "prior + week 1 POINTS")
fit(["prior", "wtouch"], "prior + week 1 TOUCHES")
fit(["prior", "snap"], "prior + week 1 SNAP SHARE")
fit(["prior", "wtouch", "snap"], "prior + touches + snaps")
_, b = fit(["prior", "wk1", "wtouch", "snap"],
           "prior + points + touches + snaps")
print("\n  coefficients on the full model:")
for c, v in zip(["prior", "points", "touches", "snaps"],
                b[:4]):
    print("    %-10s %+.4f" % (c, v))
