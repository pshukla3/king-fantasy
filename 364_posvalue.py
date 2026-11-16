import numpy as np
import pandas as pd

POS = ["QB", "RB", "WR", "TE"]
W = pd.read_parquet("weekly_all.parquet")
if "season_type" in W.columns:
    W = W[W["season_type"] == "REG"]
W = W[W["position"].isin(POS)].copy()
W["fp"] = pd.to_numeric(W["fantasy_points_ppr"],
                        errors="coerce").fillna(0.0)

# 10-team, 1QB/2RB/2WR/1TE/2FLEX -> same as 363
REPRK = {"QB": 10, "RB": 28, "WR": 32, "TE": 10}

print("=== REALIZED VALUE OVER REPLACEMENT BY SEASON ===")
print("(season ppg, min 8 games, 10-team replacement)")
acc = {p: {i: [] for i in range(1, 13)} for p in POS}
rep_hist = {p: [] for p in POS}
for s in sorted(W["season"].unique()):
    d = W[W["season"] == s]
    g = d.groupby(["player_display_name", "position"])["fp"]
    agg = g.agg(["mean", "count"]).reset_index()
    agg = agg[agg["count"] >= 8]
    for p in POS:
        z = agg[agg["position"] == p]\
            .sort_values("mean", ascending=False)
        v = list(z["mean"].values)
        if len(v) <= REPRK[p]:
            continue
        rep = v[REPRK[p]]
        rep_hist[p].append(rep)
        for i in range(1, 13):
            if i <= len(v):
                acc[p][i].append(v[i - 1] - rep)

print("\n%-4s %9s %8s %8s %8s %8s"
      % ("POS", "REPL", "RK1", "RK3", "RK6", "RK12"))
for p in POS:
    print("%-4s %9.2f %8.2f %8.2f %8.2f %8.2f"
          % (p, np.mean(rep_hist[p]),
             np.mean(acc[p][1]), np.mean(acc[p][3]),
             np.mean(acc[p][6]), np.mean(acc[p][12])))

print("\n=== HOW OFTEN DOES THE PRESEASON QB1 "
      "FINISH AS QB1? (predictability) ===")
prev = {}
for p in POS:
    hits, tot = 0, 0
    for s in sorted(W["season"].unique()):
        d = W[W["season"] == s]
        agg = d.groupby(["player_display_name",
                         "position"])["fp"]\
            .agg(["mean", "count"]).reset_index()
        agg = agg[(agg["count"] >= 8)
                  & (agg["position"] == p)]
        z = list(agg.sort_values("mean",
                                 ascending=False)
                 ["player_display_name"])
        if p in prev and prev[p]:
            top5_prev = set(prev[p][:5])
            top5_now = set(z[:5])
            hits += len(top5_prev & top5_now)
            tot += 5
        prev[p] = z
    print("  %-4s top-5 holdover rate: %.0f%%"
          % (p, 100.0 * hits / max(tot, 1)))

print("\n=== WHAT THIS MEANS ===")
qb1 = np.mean(acc["QB"][1])
rb1 = np.mean(acc["RB"][1])
wr1 = np.mean(acc["WR"][1])
print("  the actual QB1 beats replacement by %.1f ppg" % qb1)
print("  the actual RB1 beats replacement by %.1f ppg" % rb1)
print("  the actual WR1 beats replacement by %.1f ppg" % wr1)
