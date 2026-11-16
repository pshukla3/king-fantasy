import json
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

per = {p: [] for p in POS}
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
        got = []
        for nm in list(pz["player_display_name"])[:3]:
            x = cmap.get(nm)
            got.append((x if x is not None else rep) - rep)
        if got:
            per[p].append(float(np.mean(got)))

print("%-4s %8s %7s %7s %9s"
      % ("POS", "MEAN", "SE", "n", "95% CI"))
M, SE = {}, {}
for p in POS:
    a = np.array(per[p])
    M[p] = float(a.mean())
    SE[p] = float(a.std(ddof=1) / np.sqrt(len(a)))
    print("%-4s %8.2f %7.2f %7d   %.2f..%.2f"
          % (p, M[p], SE[p], len(a),
             M[p] - 1.96 * SE[p], M[p] + 1.96 * SE[p]))

print("\nratio to RB, with shrinkage toward 1.0")
print("(shrink = signal / (signal + noise))")
MULT = {}
for p in POS:
    raw = M[p] / M["RB"]
    diff = abs(M[p] - M["RB"])
    noise = np.sqrt(SE[p] ** 2 + SE["RB"] ** 2)
    conf = diff / (diff + noise) if diff > 0 else 0.0
    MULT[p] = round(1.0 + (raw - 1.0) * conf, 3)
    print("  %-4s raw %.3f  conf %.2f  ->  x%.3f"
          % (p, raw, conf, MULT[p]))
MULT["K"] = 1.0
MULT["DST"] = 1.0
json.dump(MULT, open("pos_mult.json", "w"), indent=1)
print("\nwrote pos_mult.json")
