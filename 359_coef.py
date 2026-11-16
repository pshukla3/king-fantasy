import re
import numpy as np
import pandas as pd
import glob

def norm(s):
    s = str(s or "").lower()
    s = re.sub(r"\s+(jr|sr|ii|iii|iv)\.?$", "", s)
    s = re.sub(r"[.'`\u2019\-]", "", s)
    return re.sub(r"\s+", " ", s).strip()

W = pd.read_parquet("weekly_all.parquet")
W["k"] = W["player_display_name"].map(norm)
W["fp"] = pd.to_numeric(W["fantasy_points_ppr"],
                        errors="coerce").fillna(0.0)
W = W[W["week"] <= 17]
S = pd.concat([pd.read_parquet(f) for f in
               sorted(glob.glob("data_usage/snaps_*.parquet"))],
              ignore_index=True)
S["k"] = S["player"].map(norm)
S1 = S[S["week"] == 1][["season", "k", "offense_pct"]]
S1 = S1.rename(columns={"offense_pct": "snap1"})

rows = []
for (sea, k), d in W.groupby(["season", "k"]):
    w1 = d[d["week"] == 1]["fp"]
    rest = d[d["week"].between(2, 17)]["fp"]
    if not len(w1) or len(rest) < 6:
        continue
    prev = W[(W["season"] == sea - 1) & (W["k"] == k)]["fp"]
    if len(prev) < 6:
        continue
    rows.append({"prior": float(prev.mean()),
                 "wk1": float(w1.iloc[0]),
                 "rest": float(rest.mean()),
                 "season": sea, "k": k})
D = pd.DataFrame(rows).merge(S1, on=["season", "k"],
                             how="left")
D["snap1"] = pd.to_numeric(
    D["snap1"].astype(str).str.rstrip("%"),
    errors="coerce")
D = D.dropna(subset=["snap1"])

X = np.column_stack([D["prior"], D["wk1"], D["snap1"],
                     np.ones(len(D))])
b = np.linalg.lstsq(X, D["rest"].values, rcond=None)[0]
print("n = %d" % len(D))
print("rest = %.4f*prior + %.4f*wk1 + %.4f*snap%% + %.4f"
      % (b[0], b[1], b[2], b[3]))
lam = b[1] / (b[0] + b[1])
print("\nshrinkage toward week 1 : %.3f" % lam)
print("so updated = %.0f%% projection + %.0f%% week 1"
      % (100 * (1 - lam), 100 * lam))
print("snap share: each +10%% of snaps = %+.2f ppg"
      % (10 * b[2]))
