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

print("=== 1. DOES A BOOM PREDICT A BUST NEXT WEEK? ===")
rows = []
for (sea, k), d in W.groupby(["season", "k"]):
    d = d.sort_values("week")
    if len(d) < 8:
        continue
    base = d["fp"].mean()
    if base < 4:
        continue
    v = list(zip(d["week"].values, d["fp"].values))
    for i in range(len(v) - 1):
        if v[i + 1][0] != v[i][0] + 1:
            continue
        rows.append({"base": base,
                     "s0": v[i][1] - base,
                     "s1": v[i + 1][1] - base})
S = pd.DataFrame(rows)
print("consecutive week pairs: %d" % len(S))
r = np.corrcoef(S["s0"], S["s1"])[0, 1]
print("corr(surprise week t, surprise week t+1) = %.4f" % r)
print("\nnext-week result after each kind of week:")
print("%-22s %7s %9s %9s"
      % ("THIS WEEK", "N", "NEXT VS", "BASELINE"))
for lo, hi, lab in ((12, 999, "boom  (+12 or more)"),
                    (6, 12, "good  (+6 to +12)"),
                    (-6, 6, "normal (-6 to +6)"),
                    (-12, -6, "poor  (-6 to -12)"),
                    (-999, -12, "bust  (-12 or worse)")):
    d = S[(S["s0"] >= lo) & (S["s0"] < hi)]
    if len(d) < 50:
        continue
    print("%-22s %7d %9.2f %9s"
          % (lab, len(d), d["s1"].mean(),
             "%+.2f" % d["s1"].mean()))

print("\n=== 2. SHOULD ELITE PLAYERS MOVE LESS? ===")
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
                 "rest": float(rest.mean())})
D = pd.DataFrame(rows)
print("player-seasons: %d" % len(D))

def lam(d):
    X = np.column_stack([d["prior"], d["wk1"],
                         np.ones(len(d))])
    b = np.linalg.lstsq(X, d["rest"].values,
                        rcond=None)[0]
    return b[1] / (b[0] + b[1])

print("\n%-26s %7s %9s" % ("BASELINE TIER", "N",
                           "WK1 WEIGHT"))
for lo, hi, lab in ((14, 99, "elite (14+ ppg)"),
                    (10, 14, "strong (10-14)"),
                    (6, 10, "mid (6-10)"),
                    (0, 6, "low (under 6)")):
    d = D[(D["prior"] >= lo) & (D["prior"] < hi)]
    if len(d) < 80:
        continue
    print("%-26s %7d %9.3f" % (lab, len(d), lam(d)))

print("\n=== 3. HOW STABLE IS EACH PLAYER TIER? ===")
print("%-26s %7s %9s %9s"
      % ("TIER", "N", "WEEK SD", "CORR t,t+1"))
for lo, hi, lab in ((14, 99, "elite (14+ ppg)"),
                    (10, 14, "strong (10-14)"),
                    (6, 10, "mid (6-10)"),
                    (0, 6, "low (under 6)")):
    d = S[(S["base"] >= lo) & (S["base"] < hi)]
    if len(d) < 80:
        continue
    print("%-26s %7d %9.2f %9.4f"
          % (lab, len(d), d["s1"].std(),
             np.corrcoef(d["s0"], d["s1"])[0, 1]))
