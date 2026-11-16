import numpy as np
import pandas as pd

POS = ["QB", "RB", "WR", "TE"]
REPRK = {"QB": 10, "RB": 28, "WR": 32, "TE": 10}
W = pd.read_parquet("weekly_all.parquet")
if "season_type" in W.columns:
    W = W[W["season_type"] == "REG"]
W = W[W["position"].isin(POS)].copy()
W["fp"] = pd.to_numeric(W["fantasy_points_ppr"],
                        errors="coerce").fillna(0.0)

def tbl(s):
    d = W[W["season"] == s]
    a = d.groupby(["player_display_name",
                   "position"])["fp"]\
        .agg(["mean", "count"]).reset_index()
    return a[a["count"] >= 8]

per = {p: {} for p in POS}
for s in range(2017, 2026):
    prev, cur = tbl(s - 1), tbl(s)
    cmap = dict(zip(cur["player_display_name"],
                    cur["mean"]))
    for p in POS:
        cz = cur[cur["position"] == p]\
            .sort_values("mean", ascending=False)
        v = list(cz["mean"].values)
        if len(v) <= REPRK[p]:
            continue
        rep = v[REPRK[p]]
        pz = prev[prev["position"] == p]\
            .sort_values("mean", ascending=False)
        g = []
        for nm in list(pz["player_display_name"])[:3]:
            x = cmap.get(nm)
            g.append((x if x is not None else rep) - rep)
        per[p][s] = float(np.mean(g))

print("=== VALUE OF A TOP PICK, BY SEASON ===")
print("%-6s %7s %7s %7s %7s" % ("YEAR", "QB", "RB",
                                "WR", "TE"))
for s in range(2017, 2026):
    print("%-6d %7.2f %7.2f %7.2f %7.2f"
          % (s, per["QB"].get(s, 0), per["RB"].get(s, 0),
             per["WR"].get(s, 0), per["TE"].get(s, 0)))

print("\n=== SPLIT-HALF: does the RB edge hold? ===")
for lab, yrs in (("2017-2021", range(2017, 2022)),
                 ("2022-2025", range(2022, 2026))):
    m = {p: np.mean([per[p][s] for s in yrs
                     if s in per[p]]) for p in POS}
    print("  %-10s QB %.2f  RB %.2f  WR %.2f  TE %.2f"
          % (lab, m["QB"], m["RB"], m["WR"], m["TE"]))
    print("  %-10s ratios QB %.2f WR %.2f TE %.2f"
          % ("", m["QB"] / m["RB"], m["WR"] / m["RB"],
             m["TE"] / m["RB"]))

print("\n=== DOES A LONGER TRACK RECORD MEAN WEEK 1 "
      "SHOULD MOVE YOU LESS? ===")
rows = []
for s in range(2019, 2026):
    cur = tbl(s)
    hist = {}
    for b in range(s - 4, s):
        for _, r in tbl(b).iterrows():
            hist.setdefault(r["player_display_name"],
                            []).append(r["mean"])
    d = W[W["season"] == s]
    for nm, g in d.groupby("player_display_name"):
        w1 = g[g["week"] == 1]["fp"]
        rest = g[g["week"].between(2, 17)]["fp"]
        h = hist.get(nm, [])
        if not len(w1) or len(rest) < 6 or not h:
            continue
        rows.append({"yrs": len(h), "prior": np.mean(h),
                     "wk1": float(w1.iloc[0]),
                     "rest": float(rest.mean())})
D = pd.DataFrame(rows)
print("n = %d" % len(D))
for lo, hi, lab in ((1, 1, "1 season"), (2, 2, "2 seasons"),
                    (3, 4, "3-4 seasons")):
    d = D[(D["yrs"] >= lo) & (D["yrs"] <= hi)]
    if len(d) < 60:
        continue
    X = np.column_stack([d["prior"], d["wk1"],
                         np.ones(len(d))])
    b = np.linalg.lstsq(X, d["rest"].values, rcond=None)[0]
    lam = b[1] / (b[0] + b[1])
    print("  %-12s n=%-5d weight on week 1: %.3f"
          % (lab, len(d), lam))
