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

res = {p: {i: [] for i in range(1, 7)} for p in POS}
for s in range(2017, 2026):
    prev, cur = tbl(s - 1), tbl(s)
    if not len(prev) or not len(cur):
        continue
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
        for i, nm in enumerate(
                list(pz["player_display_name"])[:6], 1):
            got = cmap.get(nm)
            res[p][i].append(
                (got if got is not None else rep) - rep)

print("EX-ANTE: rank by LAST season, score THIS season")
print("(busts and injuries counted at replacement)\n")
print("%-4s %8s %8s %8s %9s"
      % ("POS", "PICK1", "PICK2", "PICK3", "AVG1-3"))
EX = {}
for p in POS:
    a = [float(np.mean(res[p][i])) for i in (1, 2, 3)]
    EX[p] = float(np.mean(a))
    print("%-4s %8.2f %8.2f %8.2f %9.2f"
          % (p, a[0], a[1], a[2], EX[p]))

print("\nvalue of a top pick, relative to RB:")
for p in POS:
    print("  %-4s %.3f" % (p, EX[p] / EX["RB"]))
print("\nsample sizes: %s"
      % {p: len(res[p][1]) for p in POS})
